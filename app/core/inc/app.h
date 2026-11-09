/*
 * app.h
 *
 *  Created on: Jun 28, 2026
 *      Author: evgeny
 */

#ifndef INC_APP_H_
#define INC_APP_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

int flash_device_base(uint8_t fd_id, uintptr_t *ret);

void init(void);
void setup(void);

#ifdef __cplusplus
}
#endif

#endif /* INC_APP_H_ */
