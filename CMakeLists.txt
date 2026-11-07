cmake_minimum_required(VERSION 3.22)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")

file(READ "${CMAKE_SOURCE_DIR}/VERSION" FW_VERSION_RAW)
string(STRIP "${FW_VERSION_RAW}" FW_VERSION)

project(wicked_boot VERSION ${FW_VERSION} LANGUAGES C CXX ASM)

if(FOR_QEMU)
    add_compile_definitions(PRINTF_UART)
    add_compile_definitions(FOR_QEMU)
else()
    add_compile_definitions(PRINTF_UART)
#    add_compile_definitions(PRINTF_RTT)
endif()

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON) 

if(NOT DEFINED TARGET)
    message(FATAL_ERROR "TARGET not specified: ${TARGET}")#    set(TARGET "stm32f4" CACHE STRING "Target hardware platform")
endif()

set(MAIN_EXECUTABLE "wicked_boot")
add_executable(${MAIN_EXECUTABLE})

target_compile_definitions(${MAIN_EXECUTABLE} PRIVATE
    MAIN_TIME_RESOLUTION=${MAIN_TIME_RESOLUTION}
)

include(cmake/version.cmake)
generate_version_header()

#if(PRINTF_RTT)
    set(SEGGER_LIBS segger_rtt )
#else()
#    set(SEGGER_LIBS "")
#endif()

add_subdirectory(targets)
add_subdirectory(modules)
add_subdirectory(support)
add_subdirectory(app)

target_link_libraries(${MAIN_EXECUTABLE}
    ${SEGGER_LIBS}
    segger_rtt         
    tinyusb_support
    app_version
    bootutil
    mcuboot_support
    bsp_drivers
)

find_program(CMAKE_OBJCOPY NAMES arm-none-eabi-objcopy REQUIRED)

add_custom_command(TARGET ${MAIN_EXECUTABLE} POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O ihex $<TARGET_FILE:${MAIN_EXECUTABLE}> ${MAIN_EXECUTABLE}.hex
    BYPRODUCTS ${MAIN_EXECUTABLE}.hex
    COMMENT "Generating Intel HEX file: ${MAIN_EXECUTABLE}.hex"
)
add_custom_command(TARGET ${MAIN_EXECUTABLE} POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE:${MAIN_EXECUTABLE}> ${MAIN_EXECUTABLE}.bin
    BYPRODUCTS ${MAIN_EXECUTABLE}.bin
    COMMENT "Generating binary file: ${MAIN_EXECUTABLE}.bin"
)
