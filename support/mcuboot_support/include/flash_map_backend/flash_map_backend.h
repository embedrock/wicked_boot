/*
 * Copyright (c) 2018 Nordic Semiconductor ASA
 * Copyright (c) 2015 Runtime Inc
 * Copyright (c) 2020 Arm Limited.
 * Copyright (c) 2023 STMicroelectronics.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

/*
 * Original code taken from mcuboot project at:
 * https://github.com/mcu-tools/mcuboot
 * Git SHA of the original version: ac55554059147fff718015be9f4bd3108123f50a
 */

#ifndef __FLASH_MAP_BACKEND_H__
#define __FLASH_MAP_BACKEND_H__

#include <stdint.h>
#include <stddef.h>
#include "Driver_Flash.h"

#define FLASH_DEVICE_ID                 0
#define FLASH_DEVICE_BASE               0x08000000

/**
 * @brief Structure describing an area on a flash device.
 *
 * Multiple flash devices may be available in the system, each of
 * which may have its own areas. For this reason, flash areas track
 * which flash device they are part of.
 */
struct flash_area {
    /**
     * This flash area's ID; unique in the system.
     */
    uint8_t fa_id;

    /**
     * ID of the flash device this area is a part of.
     */
    uint8_t fa_device_id;

    uint16_t pad16;

    /**
     * Pointer to driver
     */
    ARM_DRIVER_FLASH *fa_driver;

    /**
     * This area's offset, relative to the beginning of its flash
     * device's storage.
     */
    uint32_t fa_off;

    /**
     * This area's size, in bytes.
     */
    uint32_t fa_size;
};

/**
 * @brief Structure describing a sector within a flash area.
 *
 * Each sector has an offset relative to the start of its flash area
 * (NOT relative to the start of its flash device), and a size. A
 * flash area may contain sectors with different sizes.
 */
struct flash_sector {
    /**
     * Offset of this sector, from the start of its flash area (not device).
     */
    uint32_t fs_off;

    /**
     * Size of this sector, in bytes.
     */
    uint32_t fs_size;
};

/**
 * @brief Macro retrieving driver from struct flash area
 *
 */
#define DRV_FLASH_AREA(area) ((area)->fa_driver)

/*
 * Start using flash area.
 */
int flash_area_open(uint8_t id, const struct flash_area **area);

void flash_area_close(const struct flash_area *area);

/*
 * Read/write/erase. Offset is relative from beginning of flash area.
 */
int flash_area_read(const struct flash_area *area, uint32_t off, void *dst,
                    uint32_t len);

int flash_area_write(const struct flash_area *area, uint32_t off,
                     const void *src, uint32_t len);

int flash_area_erase(const struct flash_area *area, uint32_t off, uint32_t len);

/*
 * Alignment restriction for flash writes.
 */
uint32_t flash_area_align(const struct flash_area *area);

/*
 * Given flash area ID, return info about sectors within the area.
 */
int flash_area_get_sectors(int fa_id, uint32_t *count,
  struct flash_sector *sectors);

int flash_area_id_from_multi_image_slot(int image_index, int slot);
int flash_area_id_from_image_slot(int slot);
uint8_t flash_area_erased_val(const struct flash_area *fap);

#endif /* __FLASH_MAP_BACKEND_H__ */
