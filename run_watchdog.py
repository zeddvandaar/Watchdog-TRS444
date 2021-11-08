# /**
#  *  Project name: Watchdog TRS444
#  *  Description: Client software for Watchdog TRS444
#  *  Version: 1.0
#  *  Author: Eugene Makarov
#  *  License: GPL-3.0-or-later
#  *  License URI: https://spdx.org/licenses/GPL-3.0-or-later.html
#  */

# Copyright (C) 2021 Eugene Makarov

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import usb.core
import usb.util

import time

# settings 
VID = 0x5131
PID = 0x2007
WATCHDOG_TIMEOUT = 360 # sec
#

# commands
BUFFER_SIZE = 0x40
COMMAND_TEST_INVALID_RESPONCE = b'\xff' * BUFFER_SIZE

COMMAND_WATCHDOG_RESET_REQUEST = \
        (0x0C + WATCHDOG_TIMEOUT // 10).to_bytes(1, byteorder='big') + b'\x00' * (BUFFER_SIZE - 1)
COMMAND_WATCHDOG_RESET_RESPONSE = COMMAND_WATCHDOG_RESET_REQUEST

COMMAND_RESET_REQUEST = b'\xff\x55' + b'\x00' * (BUFFER_SIZE - 2)
COMMAND_RESET_RESPONSE = COMMAND_RESET_REQUEST #COMMAND_TEST_INVALID_RESPONCE

COMMAND_INIT_REQUEST = b'\x80' + b'\x00' * (BUFFER_SIZE - 1)
COMMAND_INIT_RESPONSE = b'\x81' + b'\x00' * (BUFFER_SIZE - 1)
#

RESULT_OK = True
RESULT_FAIL = False

def send_command(device, input_endpoint, output_endpoint, command_request, valid_responce):

    input_endpoint.write(command_request)
    buffer = device.read(output_endpoint.bEndpointAddress, BUFFER_SIZE)
    
    for i in range(BUFFER_SIZE):

        if buffer[i] != valid_responce[i]:
            return RESULT_FAIL

    return RESULT_OK

def main():

    device = usb.core.find(idVendor=VID, idProduct=PID)
    if device is None:
        raise ValueError('Device not found')

    cfg = device.get_active_configuration()

    input_endpoint = usb.util.find_descriptor(
		cfg[(0,0)],
		custom_match = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)

    assert input_endpoint is not None

    output_endpoint = usb.util.find_descriptor(
		cfg[(0,0)],
		custom_match = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)

    assert output_endpoint is not None

    step = 0

    while True:

        time.sleep(1)

        if step == 0:

            result = send_command(
                device, input_endpoint, output_endpoint, 
                COMMAND_INIT_REQUEST, COMMAND_INIT_RESPONSE)

            if result != RESULT_OK:
                print('Error COMMAND_INIT_REQUEST')
            else:
                print('Command COMMAND_INIT_REQUEST - OK')

        # elif step % 60 == 59:

        #     result = send_command(
        #         device, input_endpoint, output_endpoint, 
        #         COMMAND_RESET_REQUEST, COMMAND_RESET_RESPONSE)

        #     if result != RESULT_OK:
        #         print('Error COMMAND_RESET_REQUEST')
        #     else:
        #         print('Command COMMAND_RESET_REQUEST - OK')

        elif step % 5 == 4:

            result = send_command(
                device, input_endpoint, output_endpoint, 
                COMMAND_WATCHDOG_RESET_REQUEST, COMMAND_WATCHDOG_RESET_RESPONSE)

            if result != RESULT_OK:
                print('Error COMMAND_WATCHDOG_RESET_REQUEST')
            else:
                print('Command COMMAND_WATCHDOG_RESET_REQUEST - OK')

        step += 1

    return 1

if __name__ == '__main__':
    main()