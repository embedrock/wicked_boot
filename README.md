# Wicked Boot
[![forthebadge](https://forthebadge.com/images/badges/powered-by-coffee.svg)](https://forthebadge.com)

[![Build Status](https://github.com/EvgeniyGA/wicked_boot/actions/workflows/build-all.yml/badge.svg)](https://github.com/EvgeniyGA/wicked_boot/actions/workflows/build-all.yml)
[![Tests Status](https://github.com/EvgeniyGA/wicked_boot/actions/workflows/qemu-tests.yml/badge.svg)](https://github.com/EvgeniyGA/wicked_boot/actions/workflows/qemu-tests.yml)
[![Latest Release](https://img.shields.io/github/v/release/EvgeniyGA/wicked_boot?label=release)](https://github.com/EvgeniyGA/wicked_boot/releases)
![MCUboot](https://img.shields.io/badge/MCUboot-v1.7.2-blue)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](https://github.com/EvgeniyGA/wicked_boot/blob/main/LICENSE)

Modern, lightweight bootloader for STM32 microcontrollers, based on [MCUboot](https://www.mcuboot.com/). Designed for secure updates and easy remote debugging.
This project incorporates configuration files and build scripts adapted from the official [STMicroelectronics stm32-mw-mcuboot](https://github.com/STMicroelectronics/stm32-mw-mcuboot) repository.

## ✨ Features
- [X] Simple boot
- [X] Remote debugging
- [X] USB-DFU support
- [X] WebUSB support

## 🚀 Quick Start
1. Clone the repository:
```bash
git clone --recursive https://github.com/EvgeniyGA/wicked_boot.git
cd wicked_boot
git submodule update --init --recursive
```
2. Build:
```bash
cmake --preset=stm32f4
cmake --build --preset=stm32f4
```
4. Flash the device. You can use any preferred flashing method compatible with your hardware setup (J-Link, ST-Link).
Target binary: build/stm32f4/wicked_boot.bin
5. WEB DFU: https://embedrock.github.io/wicked_boot/
## 🛠️ Hardware
Tested on: **STM32F407VGT6** (Waveshare Core407V)

## 📚 Documentation
For detailed MCUboot concepts, refer to the [official MCUboot design documentation](https://docs.mcuboot.com/design.html).

## 🗺️ STM32F407VG Flash Layout for MCUboot
```mermaid
flowchart TB

    %%{init: {'flowchart': {'nodeSpacing': 25, 'rankSpacing': 1,'useMaxWidth': false}}}%%
    subgraph STM32F407[" "]
        direction TB
        
        subgraph BOOT["Bootloader Region (128K)"]
            B1["Sector 0 (16 KB):<br/><span style='white-space: nowrap;'>0x08000000-0x08003FFF</span>"]
            B2["Sector 1 (16 KB):<br/><span style='white-space: nowrap;'>0x08004000-0x08007FFF</span>"]
            B3["Sector 2 (16 KB):<br/><span style='white-space: nowrap;'>0x08008000-0x0800BFFF</span>"]
            B4["Sector 3 (16 KB):<br/><span style='white-space: nowrap;'>0x0800C000-0x0800FFFF</span>"]
            B5["Sector 4 (64 KB):<br/><span style='white-space: nowrap;'>0x08010000-0x0801FFFF</span>"]
            B1 ~~~ B2
            B3 ~~~ B4
			B4 ~~~ B5
        end
        
        subgraph PRIMARY["Primary Slot (256K)"]
			P1["Sector 5 (128 KB):<br/><span style='white-space: nowrap;'>0x08020000-0x0803FFFF</span>"]
			P2["Sector 6 (128 KB):<br/><span style='white-space: nowrap;'>0x08040000-0x0805FFFF</span>"]
			P1 ~~~ P2
        end
        
        subgraph SECONDARY["Secondary Slot (256K)"]
			S1["Sector 7 (128 KB):<br/><span style='white-space: nowrap;'> 0x08060000-0x0807FFFF</span>"]
			S2["Sector 8 (128 KB):<br/><span style='white-space: nowrap;'> 0x08080000-0x0809FFFF</span>"]
			S1 ~~~ S2
        end
        
        subgraph SCRATCH["Storage Area (384K)"]
            SC1["Sector 9  (128 KB):<br/><span style='white-space: nowrap;'> 0x080A0000-0x080BFFFF</span>"]
			SC2["Sector 10 (128 KB):<br/><span style='white-space: nowrap;'> 0x080C0000-0x080DFFFF</span>"]
			SC3["Sector 11 (128 KB):<br/><span style='white-space: nowrap;'> 0x080E0000-0x080FFFFF</span>"]
			SC1 ~~~ SC2
			SC2 ~~~ SC3
        end

        BOOT ~~~ PRIMARY
        PRIMARY ~~~ SECONDARY
        SECONDARY ~~~ SCRATCH
    end

    style STM32F407 fill:#3a4a4a,stroke:#666,stroke-width:1px,color:#fff
    style BOOT fill:#2d5016,stroke:#4a7c2c,stroke-width:1px,color:#fff
    style PRIMARY fill:#1a4d7a,stroke:#2e6da4,stroke-width:1px,color:#fff
    style SECONDARY fill:#7a3d1a,stroke:#a4562e,stroke-width:1px,color:#fff
    style SCRATCH fill:#4a4a4a,stroke:#666,stroke-width:1px,color:#fff
    style B1 fill:#3d6b1f,stroke:#5a9c3c,stroke-width:1px,color:#fff,font-size:12px
    style B2 fill:#3d6b1f,stroke:#5a9c3c,stroke-width:1px,color:#fff,font-size:12px
    style B3 fill:#3d6b1f,stroke:#5a9c3c,stroke-width:1px,color:#fff,font-size:12px
    style B4 fill:#3d6b1f,stroke:#5a9c3c,stroke-width:1px,color:#fff,font-size:12px
    style B5 fill:#3d6b1f,stroke:#5a9c3c,stroke-width:1px,color:#fff,font-size:12px
    style P1 fill:#2563a8,stroke:#3d8ad4,stroke-width:1px,color:#fff,font-size:12px
    style P2 fill:#2563a8,stroke:#3d8ad4,stroke-width:1px,color:#fff,font-size:12px
    style S1 fill:#9c5a2e,stroke:#c47a4a,stroke-width:1px,color:#fff,font-size:12px
    style S2 fill:#9c5a2e,stroke:#c47a4a,stroke-width:1px,color:#fff,font-size:12px
    style SC1 fill:#5a5a5a,stroke:#777,stroke-width:1px,color:#fff,font-size:12px
    style SC2 fill:#5a5a5a,stroke:#777,stroke-width:1px,color:#fff,font-size:12px
    style SC3 fill:#5a5a5a,stroke:#777,stroke-width:1px,color:#fff,font-size:12px
```
