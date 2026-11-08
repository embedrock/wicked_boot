#include <stdio.h>
#include <ctype.h>
#include <assert.h>
#include "version.h"
#include "version_check.h"
#include "app.h"
#include "tim.h"
#include <string.h>

#include "main.h"
#include "bootutil/bootutil.h"
#include "bootutil/image.h"
#include "bootutil/bootutil_log.h"
#include "Driver_Usart.h"
#include "Driver_GPIO.h"
#include "boot_hal.h"

#include "flash_map_backend/flash_map_backend.h"

#include "shell/shell.h"
#include "usb_descriptors.h"

#ifdef STM32F407xx
    #include "lcd_driver.h"
#endif

#include "tusb.h"
#include "SEGGER_RTT.h"

/* Blink pattern
 * - 250 ms  : device not mounted
 * - 1000 ms : device mounted
 * - 2500 ms : device is suspended
 */
enum {
  BLINK_NOT_MOUNTED = 250,
  BLINK_MOUNTED     = 1000,
  BLINK_SUSPENDED   = 2500,
};

void init(void){
#ifdef PRINTF_RTT
	SEGGER_RTT_ConfigUpBuffer( 0, NULL, NULL, 0, SEGGER_RTT_MODE_NO_BLOCK_TRIM );
#endif
}

void My_Delay(uint32_t Delay){
    uint64_t del = Delay*1000;
    while(del--);
}

static void emergency_cli(void);

static void do_boot(struct boot_rsp *rsp)
{
    struct boot_arm_vector_table *vt;
    uintptr_t flash_base;
    int rc;

    /* The beginning of the image is the ARM vector table, containing
     * the initial stack pointer address and the reset vector
     * consecutively. Manually set the stack pointer and jump into the
     * reset vector
     */
    rc = flash_device_base(rsp->br_flash_dev_id, &flash_base);
    (void)rc;
    assert(rc == 0);

    if (rsp->br_hdr->ih_flags & IMAGE_F_RAM_LOAD) {
       /* The image has been copied to SRAM, find the vector table
        * at the load address instead of image's address in flash
        */
        vt = (struct boot_arm_vector_table *)(rsp->br_hdr->ih_load_addr +
                                         rsp->br_hdr->ih_hdr_size);
    } else {
        /* Using the flash address as not executing in SRAM */
        vt = (struct boot_arm_vector_table *)(flash_base +
                                         rsp->br_image_off +
                                         rsp->br_hdr->ih_hdr_size);
    }

#if defined(MCUBOOT_HAVE_LOGGING)
//    stdio_uninit();
#endif

    /* This function never returns, because it calls the secure application
     * Reset_Handler().
     */
    boot_platform_quit(vt);
}

void setup(void){
  HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_3);
  BOOT_LOG_INF("Bootloader Version: %d.%d.%d", FW_VERSION_MAJOR, FW_VERSION_MINOR, FW_VERSION_PATCH);
	BOOT_LOG_INF("Build: %s %s (git: %s)", FW_BUILD_DATE, FW_BUILD_TIME, FW_GIT_HASH);
#ifdef STM32F407xx
    static LCD_HandleTypeDef hlcd1 = {.delay_ms = My_Delay}; //HAL_Delay;
    lcd_printer_msg_t msg;

    LCD_Init(&hlcd1);

    msg.line = 1;
    msg.offset = 1;
    strcpy(msg.data, "loading..");
    LCD_SetCursor(&hlcd1, msg.line, msg.offset);
    LCD_SendString(&hlcd1, msg.data);
#endif
    BOOT_LOG_INF("Wait or enter any symbol to go CLI:\n\r");
    if((int8_t)console_getc(CONSOLE_GETCH_TIMEOUT) != - 1){
        emergency_cli();
    }
    
    struct boot_rsp rsp;
    fih_int fih_rc = FIH_FAILURE;
    FIH_CALL(boot_go, fih_rc, &rsp);
    if (fih_not_eq(fih_rc, FIH_SUCCESS)) {
        BOOT_LOG_ERR("Unable to find bootable image. Falling into CLI:");
        emergency_cli();//FIH_PANIC;
    }

    BOOT_LOG_INF("Bootloader chainload address offset: 0x%x", (int)rsp.br_image_off);
    BOOT_LOG_INF("Jumping to the first image slot");
    do_boot(&rsp);

    BOOT_LOG_ERR("Something came up. Go CLI");
//FAIL:
#ifdef STM32F407xx
    strcpy(msg.data, " fail");
    LCD_SendString(&hlcd1, msg.data);
#endif
    emergency_cli();
}

uint8_t reboot_flag = 0;

void emergency_cli(void){
    char c = 0;

    // init device stack on configured roothub port
    tusb_rhport_init_t dev_init = {.role = TUSB_ROLE_DEVICE, .speed = TUSB_SPEED_AUTO};
    tusb_init(BOARD_TUD_RHPORT, &dev_init);

    sShellImpl shell_impl = { .send_char = console_putc, };
    shell_boot(&shell_impl);
    __HAL_TIM_SET_AUTORELOAD(&htim3, 5000 - 1);
    while (true) {
        tud_task();
        c = console_getc(0);
        if((int8_t)c != - 1){
            shell_receive_char(c);
        }
        // if(reboot_flag){
        //     uint32_t i = 0x1FFF;
        //     while(i--){
        //         tud_task();
        //     }
        //     NVIC_SystemReset();
        // }
    }
}


//--------------------------------------------------------------------+
// Device callbacks
//--------------------------------------------------------------------+

// Invoked when device is mounted
void tud_mount_cb(void) {
  BOOT_LOG_INF("usb mount");//blink_interval_ms = BLINK_MOUNTED;
}

// Invoked when device is unmounted
void tud_umount_cb(void) {
  BOOT_LOG_INF("usb unmount");//blink_interval_ms = BLINK_NOT_MOUNTED;
}

// Invoked when usb bus is suspended
// remote_wakeup_en : if host allow us  to perform remote wakeup
// Within 7ms, device must draw an average of current less than 2.5 mA from bus
void tud_suspend_cb(bool remote_wakeup_en) {
  (void)remote_wakeup_en;
  BOOT_LOG_INF("usb suspend");//blink_interval_ms = BLINK_SUSPENDED;
}

// Invoked when usb bus is resumed
void tud_resume_cb(void) {
  BOOT_LOG_INF("usb resume");//blink_interval_ms = tud_mounted() ? BLINK_MOUNTED : BLINK_NOT_MOUNTED;
}

//--------------------------------------------------------------------+
// DFU callbacks
// Note: alt is used as the partition number, in order to support multiple partitions like FLASH, EEPROM, etc.
//--------------------------------------------------------------------+

// Invoked right before tud_dfu_download_cb() (state=DFU_DNBUSY) or tud_dfu_manifest_cb() (state=DFU_MANIFEST)
// Application return timeout in milliseconds (bwPollTimeout) for the next download/manifest operation.
// During this period, USB host won't try to communicate with us.
uint32_t tud_dfu_get_timeout_cb(uint8_t alt, uint8_t state) {
  if (state == DFU_DNBUSY) {
    // For this example
    // - Atl0 Flash is fast : 1   ms
    // - Alt1 EEPROM is slow: 100 ms
    return (alt == 0) ? 1 : 100;
  } else if (state == DFU_MANIFEST) {
    // since we don't buffer entire image and do any flashing in manifest stage
    return 0;
  } else {
    // nothing to do
  }

  return 0;
}

// Invoked when received DFU_DNLOAD (wLength>0) following by DFU_GETSTATUS (state=DFU_DNBUSY) requests
// This callback could be returned before flashing op is complete (async).
// Once finished flashing, application must call tud_dfu_finish_flashing()
void tud_dfu_download_cb(uint8_t alt, uint16_t block_num, const uint8_t *data, uint16_t length) {
    (void)alt;
    (void)block_num;
    static uint32_t last_erased_sector = 0xFFFFFFFF;
    static uint32_t bytes_written = 0;

    if (block_num == 0) {
        bytes_written = 0;
        last_erased_sector = 0xFFFFFFFF;
    }

    BOOT_LOG_DBG("Received Alt %u BlockNum %u of length %u", alt, block_num, length);

    uint32_t current_addr = (alt + 1) * 0x40000 + bytes_written;
    uint32_t current_sector = GetSectorFromAddress(0x8000000 + current_addr);

    if (current_sector != last_erased_sector) {
        BOOT_LOG_DBG("[DFU] >>> Erasing Sector %u at 0x%08lX...", current_sector, current_addr);
        
        if (Driver_FLASH0.EraseSector(current_addr) != ARM_DRIVER_OK) {
            BOOT_LOG_ERR("[DFU] >>> Erase FAILED!");
            tud_dfu_finish_flashing(DFU_STATUS_ERR_ERASE);
            return;
        }
        
        last_erased_sector = current_sector;
        BOOT_LOG_DBG("[DFU] >>> Erase OK. Starting programming...");
    }

    if (Driver_FLASH0.ProgramData(current_addr, data, length) != ARM_DRIVER_OK) {
        BOOT_LOG_ERR("[DFU] Program FAILED at 0x%08lX!", current_addr);
        tud_dfu_finish_flashing(DFU_STATUS_ERR_WRITE);
        return;
    }
    bytes_written += length;
    printf(".");
    fflush(stdout); 
    // flashing op for download complete without error
    tud_dfu_finish_flashing(DFU_STATUS_OK);
}

// Invoked when download process is complete, received DFU_DNLOAD (wLength=0) following by DFU_GETSTATUS (state=Manifest)
// Application can do checksum, or actual flashing if buffered entire image previously.
// Once finished flashing, application must call tud_dfu_finish_flashing()
void tud_dfu_manifest_cb(uint8_t alt) {
  const int permanent = 0;
  printf("\n\r");
  BOOT_LOG_INF("Download completed, enter manifestation");

  // flashing op for manifest is complete without error
  // Application can perform checksum, should it fail, use appropriate status such as errVERIFY.
  tud_dfu_finish_flashing(DFU_STATUS_OK);

  if(alt == 1){
    BOOT_LOG_INF("Set pending");
    boot_set_pending(permanent);
  }
  BOOT_LOG_INF("reboot\n\r");
              uint32_t i = 0x1FFF;
            while(i--){
                tud_task();
            }
  NVIC_SystemReset();
  //reboot_flag = 1;
}

// Invoked when received DFU_UPLOAD request
// Application must populate data with up to length bytes and
// Return the number of written bytes
uint16_t tud_dfu_upload_cb(uint8_t alt, uint16_t block_num, uint8_t *data, uint16_t length) {
  (void)block_num;
  (void)length;

  if (block_num != 0u) {
    return 0; // for this example we only support single block upload
  }

  return 0;
}

// Invoked when the Host has terminated a download or upload transfer
void tud_dfu_abort_cb(uint8_t alt) {
  (void)alt;
  BOOT_LOG_INF("Host aborted transfer");
}

// Invoked when a DFU_DETACH request is received
void tud_dfu_detach_cb(void) {
  BOOT_LOG_INF("Host detach, we should probably reboot");
}
//--------------------------------------------------------------------+
//#define URL  "example.tinyusb.org/webusb-serial/index.html"
//#define WEBUSB_URL "devanlai.github.io/webdfu/"
#define URL  "evgeniyga.github.io/wicked_boot/"

const tusb_desc_webusb_url_t desc_url = {
  .bLength         = 3 + sizeof(URL) - 1,
  .bDescriptorType = 3, // WEBUSB URL type
  .bScheme         = 1, // 0: http, 1: https
  .url             = URL
};

static bool web_serial_connected = false;
//--------------------------------------------------------------------+
// WebUSB use vendor class
//--------------------------------------------------------------------+

// Invoked when a control transfer occurred on an interface of this class
// Driver response accordingly to the request and the transfer stage (setup/data/ack)
// return false to stall control endpoint (e.g unsupported request)
bool tud_vendor_control_xfer_cb(uint8_t rhport, uint8_t stage, tusb_control_request_t const* request) {  
    // nothing to with DATA & ACK stage
  if (stage != CONTROL_STAGE_SETUP) {
    return true;
  }

  switch (request->bmRequestType_bit.type) {
    case TUSB_REQ_TYPE_VENDOR:
      switch (request->bRequest) {
        case VENDOR_REQUEST_WEBUSB:
          // match vendor request in BOS descriptor
          // Get landing page url
          return tud_control_xfer(rhport, request, (void*)(uintptr_t)&desc_url, desc_url.bLength);

        case VENDOR_REQUEST_MICROSOFT:
          if (request->wIndex == 7) {
            // Get Microsoft OS 2.0 compatible descriptor
            //uint16_t total_len;
            //memcpy(&total_len, desc_ms_os_20 + 8, 2);
            
            //return tud_control_xfer(rhport, request, (void*)(uintptr_t)desc_ms_os_20, total_len);
            return tud_control_xfer(rhport, request, (void*)(uintptr_t)desc_ms_os_20, 0x152/*MS_OS_20_DESC_LEN*/);

          } else {
            return false;
          }

        default: break;
      }
      break;

    case TUSB_REQ_TYPE_CLASS:
      if (request->bRequest == 0x22) {
        // Webserial simulate the CDC_REQUEST_SET_CONTROL_LINE_STATE (0x22) to connect and disconnect.
        web_serial_connected = (request->wValue != 0);

        // Always lit LED if connected
        if (web_serial_connected) {
          //board_led_write(true);
          //blink_interval_ms = BLINK_ALWAYS_ON;

          tud_vendor_write_str("\r\nWebUSB interface connected\r\n");
          tud_vendor_write_flush();
        } else {
          //tud_vendor_write_clear(); // anything left in the buffer is now thrown out
          //blink_interval_ms = BLINK_MOUNTED;
        }

        // response with status OK
        return tud_control_status(rhport, request);
      }
      break;

    default: break;
  }

  // stall unknown request
  return false;
}

//void tud_vendor_rx_cb(uint8_t idx, const uint8_t *buffer, uint32_t bufsize) {
void tud_vendor_rx_cb(uint8_t idx, const uint8_t *buffer, uint16_t bufsize) {
  (void)idx;
  (void)buffer;
  (void)bufsize;

  while (tud_vendor_available()) {
    uint8_t        buf[64];
    const uint32_t count = tud_vendor_read(buf, sizeof(buf));
    for(int i = 0; i < count; i++){
        printf("%c ", buf[i]);
    }
    printf("\n\r");
    
    tud_vendor_write(buf, count);
    tud_vendor_write_flush();
  }
}