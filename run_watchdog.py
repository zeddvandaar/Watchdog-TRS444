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

import platform

import time

import argparse

# settings 
DEFAULT_VID = 0x5131
DEFAULT_PID = 0x2007
DEFAULT_REBOOT_TIMEOUT = 360*2 # sec
DEFAULT_WATCHDOG_RESET_TIMEOUT = 5 # sec
#

# commands
BUFFER_SIZE = 0x40
COMMAND_TEST_INVALID_RESPONCE = b'\xff' * BUFFER_SIZE

COMMAND_WATCHDOG_RESET_REQUEST = b'\x00' * BUFFER_SIZE
COMMAND_WATCHDOG_RESET_RESPONSE = COMMAND_WATCHDOG_RESET_REQUEST

def redefine_commands(reboot_timeout):
    global COMMAND_WATCHDOG_RESET_REQUEST
    COMMAND_WATCHDOG_RESET_REQUEST = \
            (0x0C + reboot_timeout // 10).to_bytes(1, byteorder='big') + b'\x00' * (BUFFER_SIZE - 1)
    global COMMAND_WATCHDOG_RESET_RESPONSE
    COMMAND_WATCHDOG_RESET_RESPONSE = COMMAND_WATCHDOG_RESET_REQUEST

COMMAND_REBOOT_REQUEST = b'\xff\x55' + b'\x00' * (BUFFER_SIZE - 2)
COMMAND_REBOOT_RESPONSE = COMMAND_REBOOT_REQUEST #COMMAND_TEST_INVALID_RESPONCE

COMMAND_INIT_REQUEST = b'\x80' + b'\x00' * (BUFFER_SIZE - 1)
COMMAND_INIT_RESPONSE = b'\x81' + b'\x00' * (BUFFER_SIZE - 1)
#

RESULT_OK = True
RESULT_FAIL = False

def send_command(device, input_endpoint, output_endpoint, command_request, valid_responce) -> bool:

    input_endpoint.write(command_request)
    buffer = device.read(output_endpoint.bEndpointAddress, BUFFER_SIZE)
    
    for i in range(BUFFER_SIZE):

        if buffer[i] != valid_responce[i]:
            return RESULT_FAIL

    return RESULT_OK

def main():

    # arguments work

    parser = argparse.ArgumentParser(prog='Watchdog TRS444', description='Client software for Watchdog TRS444.')
    parser.add_argument('--vid', type=ascii, default=hex(DEFAULT_VID), help='device VID (default ' + hex(DEFAULT_VID) + ')')
    parser.add_argument('--pid', type=ascii, default=hex(DEFAULT_PID), help='device PID (default ' + hex(DEFAULT_PID) + ')')
    parser.add_argument('--reset-watchdog-timeout', type=int, default=DEFAULT_WATCHDOG_RESET_TIMEOUT, 
            help='watchdog reset timeout (default ' + str(DEFAULT_WATCHDOG_RESET_TIMEOUT) + ')')
    parser.add_argument('--reboot-timeout', type=int, default=DEFAULT_REBOOT_TIMEOUT, 
            help='timeout before reboot (if watchdog down) (default ' + str(DEFAULT_REBOOT_TIMEOUT) + ')')

    parser.add_argument('command', nargs='?', help='reset watchdog with timeout (wait - default, reboot)')

    args = parser.parse_args()
    
    VID = int(args.vid.replace("'", ""), 16)
    PID = int(args.pid.replace("'", ""), 16)

    REBOOT_TIMEOUT = args.reboot_timeout
    redefine_commands(REBOOT_TIMEOUT)

    WATCHDOG_RESET_TIMEOUT = args.reset_watchdog_timeout

    need_reboot = args.command == 'reboot'

    # find device

    device = usb.core.find(idVendor=VID, idProduct=PID)
    if (platform.system() == 'Linux') and device.is_kernel_driver_active(0):
        device.detach_kernel_driver(0)

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

        elif need_reboot:

            result = send_command(
                device, input_endpoint, output_endpoint, 
                COMMAND_REBOOT_REQUEST, COMMAND_REBOOT_RESPONSE)

            if result != RESULT_OK:
                print('Error COMMAND_REBOOT_REQUEST')
            else:
                print('Command COMMAND_REBOOT_REQUEST - OK')

            return 0

        elif step % WATCHDOG_RESET_TIMEOUT == (WATCHDOG_RESET_TIMEOUT - 1):

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