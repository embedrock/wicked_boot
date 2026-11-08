/* Manual version of auto-generated version. */

/*
 * Original code taken from mcuboot project at:
 * https://github.com/mcu-tools/mcuboot
 * Git SHA of the original version: ac55554059147fff718015be9f4bd3108123f50a
 * Modifications are Copyright (c) 2020 Arm Limited.
 *                   Copyright (c) 2023 STMicroelectronics.
 */

#ifndef __SYSFLASH_H__
#define __SYSFLASH_H__

#ifdef __cplusplus
extern "C" {
#endif

#include "Driver_Flash.h"

# define FLASH_DEVICE_INTERNAL_FLASH 0

//! NB: MCUBoot expects this define to exist but it's only used
//! if MCUBOOT_SWAP_USING_SCRATCH is defined
# define FLASH_AREA_IMAGE_SCRATCH FLASH_SLOT_DOES_NOT_EXIST
//#define FLASH_AREA_IMAGE_SCRATCH      3

//! An arbitrarily high slot ID we will use to indicate that
//! there is not slot
#define FLASH_SLOT_DOES_NOT_EXIST 255

//! The slot we will use to track the bootloader allocation
# define FLASH_AREA_BOOTLOADER 0

//! A mapping to primary and secondary/upgrade slot
//! given an image_index. We'll plan to use
# define FLASH_AREA_IMAGE_PRIMARY(i) ((i == 0) ? 1 : 255)
# define FLASH_AREA_IMAGE_SECONDARY(i) ((i == 0) ? 2 : 255)

#ifdef __cplusplus
}
#endif

#endif /* __SYSFLASH_H__ */
