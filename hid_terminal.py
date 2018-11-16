#!/usr/bin/python3

"""
  _   _ ___ ___   _  _ ___ ___    _____ ___ ___ __  __ ___ _  _   _   _    
 | | | / __| _ ) | || |_ _|   \  |_   _| __| _ \  \/  |_ _| \| | /_\ | |   
 | |_| \__ \ _ \ | __ || || |) |   | | | _||   / |\/| || || .` |/ _ \| |__ 
  \___/|___/___/ |_||_|___|___/    |_| |___|_|_\_|  |_|___|_|\_/_/ \_\____|
                                                                           

This is a tool for testing USB HID communication with a in and out endpoint.

Copyright 2018 Christoph Swoboda

Permission is hereby granted, free of charge, to any person obtaining a copy 
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights 
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import usb.core
import sys
import time

# ---------------------- Methods ----------------------


def discover_device():
    """ Discover devices and ask user for device selection """

    print("----- HID Devices -----")

    # Find all devices
    devices = usb.core.find(find_all=True)
    all_devices = []

    # List devices
    for device in devices:
        vid = device.idVendor
        pid = device.idProduct

        print(str(len(all_devices)) + ": VID " +
              hex(vid) + "\tPID " + hex(pid))

        all_devices.append(device)

    if len(all_devices) == 0:
        sys.exit("No USB HID Device found!")

    device_number = 0

    # User has to select the device
    while True:
        device_number = input(
            "Select device (0-" + str(len(all_devices)-1) + "): ")

        try:
            device_number = int(device_number)

            if device_number >= 0 and device_number < len(all_devices):
                break
        except ValueError:
            continue

    # Return VID, PID
    return all_devices[device_number].idVendor, all_devices[device_number].idProduct


def detach_device_from_kernel(device):
    """ Detach device from kernel """

    if device.is_kernel_driver_active(0):
        try:
            device.detach_kernel_driver(0)
        except usb.core.USBError as e:
            sys.exit("Could not detatch kernel driver: %s" % str(e))


def get_default_endpoints(device):
    """ Get first input and output endpoint from device """

    cfg = device.get_active_configuration()
    intf = cfg[(0, 0)]

    # Out endpoint
    ep_out = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(
        e.bEndpointAddress) == usb.util.ENDPOINT_OUT)

    # In endpoint
    ep_in = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(
        e.bEndpointAddress) == usb.util.ENDPOINT_IN)

    # return endpoints
    return ep_out, ep_in


def print_hex_array(int_array):
    """ Pretty print array of int as hex values """

    for byte in int_array:
        hex_byte = hex(byte).replace("0x", "")

        if len(hex_byte) == 1:
            hex_byte = "0" + hex_byte

        print(hex_byte + " ", end="")

    print()

# ---------------------- Main ----------------------


def main():
    """ Main Program """

    # Get selected device
    vid, pid = discover_device()
    device = None

    try:
        # Open device & detach
        device = usb.core.find(idVendor=vid, idProduct=pid)
        detach_device_from_kernel(device)
    except:
        sys.exit(
            "Can't access USB device. Please create udev file or start with sudo!")

    # Get endpoints
    ep_out, ep_in = get_default_endpoints(device)

    if device is None:
        sys.exit("Device connection error!")

    if ep_out is None or ep_in is None:
        sys.exit("Couldn'f find default IO endpoints of device!")

    print("\nEnter hex data to send:")

    # Communication
    while 1:
        try:
            # Prompt for input
            msg_in = input('> ').replace(" ", "")
            out_data = []

            # Split into array
            for i in range(0, len(msg_in), 2):
                out_data.append(int(msg_in[i:i+2], base=16))
        except KeyboardInterrupt:
            sys.exit("\n")
        except:
            print("Invalid data!")
            continue

        try:
            print("OUT: ", end="")
            print_hex_array(out_data)

            # Send & receive
            device.write(ep_out.bEndpointAddress, out_data)
            in_data = device.read(ep_in.bEndpointAddress, ep_in.wMaxPacketSize)

            print("IN: ", end="")
            print_hex_array(in_data)

        except usb.core.USBError as e:
            print("Data not sent!")


if __name__ == '__main__':
    main()
