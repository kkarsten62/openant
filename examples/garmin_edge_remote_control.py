# ANT - Set up master to connect to Garmin Edge Remote Control
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
'''
Example showing to setup ANT+ connection to Garmin Remote Control device
This script will act as Master and Garmin Remote Control will act as Slave

Prerequisites:
- Garmin Ant+ USB Stick (ID_VENDOR = 0x0FCF, ID_PRODUCT = 0x1009)
  https://www.thisisant.com/directory/usb-ant-stick/
- Or Garmin previous long version (ID_VENDOR = 0x0FCF, ID_PRODUCT = 0x1008)

- Garmin Edge Remote Control device
  https://www.thisisant.com/directory/edge-remote-control/

Related docs:
https://www.thisisant.com/resources/ant-message-protocol-and-usage/
https://www.thisisant.com/resources/audio-controls/

Usage:
python3 garmin_edge_remote_control.py

Expected output when pressing the buttons:
    Opening ANT+ Channel ...
    Normal push: "Lap" button
    Normal push: "Page Forward" button
    Long push: "Page Backward" button
    Normal push: "Customize" button
    Long push: "Customize" button
    ^CClosing ANT+ Channel ...

Use Ctrl-C to quit
'''

from ant.easy.node import Node
from ant.easy.channel import Channel

import array
import logging

NETWORK_KEY = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

class GarminEdgeRemoteControl:
    def __init__(self):
        self.count = 0
        
        logging.basicConfig(filename="example.log", level=logging.DEBUG)

        node = Node()
        node.set_network_key(0x00, NETWORK_KEY)

# Master channel configuration for Generic Control Device
        self.channel = node.new_channel(Channel.Type.BIDIRECTIONAL_TRANSMIT)
        self.channel.set_id(1, 16, 5)
        self.channel.set_period(8192)
        self.channel.set_rf_freq(57)

# Callbacks
        self.channel.on_broadcast_tx_data = self.on_tx_data
        self.channel.on_acknowledge_data = self.on_ack_data

        try:
            print("Opening ANT+ Channel ...")
            self.channel.open()
            node.start()
        except KeyboardInterrupt:
            print("Closing ANT+ Channel ...")
            self.channel.close()
            node.stop()
        finally:
            logging.shutdown() 

# Callback to broadcast master payload pages
    def on_tx_data(self, data):
        if self.count == 0:
            payload = array.array('B', [0x50, 0xFF, 0xFF, 0x01, 0x0F, 0x00, 0x85, 0x83])
        elif self.count == 65:
            payload = array.array('B', [0x51, 0xFF, 0xFF, 0x01, 0x01, 0x00, 0x00, 0x00])
        else:
            payload = array.array('B', [0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x50])
            if self.count == 129:
                self.count = -1

        self.count += 1

        self.channel.send_broadcast_data(payload)

# Callback to handle the button press events
    def on_ack_data(self, data):
        page = data[0]
        
        if page == 73:
            commandNo = data[6] + (data[7] << 8)
            if commandNo == 36:
                print('Normal push: "Lap" button')
            elif commandNo == 1:
                print('Normal push: "Page Forward" button')
            elif commandNo == 0:
                print('Long push: "Page Backward" button')
            elif commandNo == 32768:
                print('Normal push: "Customize" button')
            elif commandNo == 32769:
                print('Long push: "Customize" button')

def main():
    GarminEdgeRemoteControl()

if __name__ == "__main__":
    main()
