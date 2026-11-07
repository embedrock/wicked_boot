#ifndef DRIVER_GPIO_H_
#define DRIVER_GPIO_H_

#include <stdint.h>

#ifdef  __cplusplus
extern "C"
{
#endif


void status_led_on();
void status_led_off();
void status_led_toggle();

#ifdef  __cplusplus
}
#endif

#endif /* DRIVER_LED_H_ */