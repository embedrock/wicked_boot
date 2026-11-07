#include "Driver_GPIO.h"
#include "stm32f4xx.h"
#include "stm32f4xx_hal.h"
#include "main.h"


void status_led_on(){
    //HAL_GPIO_WritePin(led_status_GPIO_Port, led_status_Pin, GPIO_PIN_SET);
}

void status_led_off(){
    //HAL_GPIO_WritePin(led_status_GPIO_Port, led_status_Pin, GPIO_PIN_RESET);
}

void status_led_toggle(){
    //HAL_GPIO_TogglePin(led_status_GPIO_Port, led_status_Pin);
}