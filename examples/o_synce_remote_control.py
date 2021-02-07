# ANT - Set up master to connect to o_synce Remote Control
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
Example showing to setup ANT+ connection to o_synce Remote Control
This script will act as Master and o_synce Remote Control will act as Slave

Prerequisites:
- Garmin Ant+ USB Stick (ID_VENDOR = 0x0FCF, ID_PRODUCT = 0x1009)
  https://www.thisisant.com/directory/usb-ant-stick/
- Or Garmin previous long version (ID_VENDOR = 0x0FCF, ID_PRODUCT = 0x1008)

- o_synce Remote Control
  https://www.thisisant.com/directory/antremote
  https://www.o-synce-shop.de/shop/en/accessories/remotes/81/ant-remote-wireless-remote-control?c=32

Related docs:
https://www.thisisant.com/resources/ant-message-protocol-and-usage/
https://www.thisisant.com/resources/audio-controls/
https://www.thisisant.com/resources/common-data-pages/

Usage:
python3 o_synce_remote_control.py

Expected output when pressing the buttons:
    Acknowledge Data: Normal push: "Up" button
    Acknowledge Data: Long push: "Up" button
    Acknowledge Data: Normal push: "Down" button
    Acknowledge Data: Long push: "Down" button
    Acknowledge Data: Normal push: "Middle" button
    Acknowledge Data: Long push: "Middle" button
    Page 80: HW Revision= 2 | Manufacturer ID= 38 | Model Number= 65535
    Page 81: SW Revision= 93 | Serial Number= 347885590
    Page 82: Battery Voltage= 0.99609375 | Battery Status= New | Cumulative Operating Time [s]= 294
Use Ctrl-C to quit
'''

from ant.easy.node import Node
from ant.easy.channel import Channel

import array
import logging

NETWORK_KEY = [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]

class OsynceRemoteControl:
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
        self.channel.on_acknowledge_data = self.on_acknowledge_data
        self.channel.on_broadcast_data = self.on_broadcast_data

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
            payload = array.array('B', [0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10])
            if self.count == 129:
                self.count = -1

        self.count += 1

        self.channel.send_broadcast_data(payload)

# Callback to handle the button press events
    def on_acknowledge_data(self, data):
#        print('ac data=', data)
        page = data[0]
        
        if page == 73:
            commandNo = data[6] + (data[7] << 8)
            if commandNo == 0:
                print('Acknowledge Data: Normal push: "Up" button')
            elif commandNo == 3:
                print('Acknowledge Data: Long push: "Up" button')
            elif commandNo == 1:
                print('Acknowledge Data: Normal push: "Down" button')
            elif commandNo == 36:
                print('Acknowledge Data: Long push: "Down" button')
            elif commandNo == 2:
                print('Acknowledge Data: Normal push: "Middle" button')
            elif commandNo == 32:
                print('Acknowledge Data: Long push: "Middle" button')

# Callback to receive page 80-82
    def on_broadcast_data(self, data):
        print('bc data=', data)
        page = data[0]
        
        if page == 80:
            print('Page 80: HW Revision=', data[3],
                '| Manufacturer ID=', data[4] + (data[5] << 8),
                '| Model Number=', data[6] + (data[7] << 8)
            )
        elif page == 81:
            print('Page 81: SW Revision=', data[3],
                '| Serial Number=', data[4] + (data[5] << 8) +
                (data[6] << 16) + (data[7] << 24)
            )
        elif page == 82:
            battFract = data[6] / 256
            battcoarse = data[7] & 0x0F
            battVoltage = battcoarse + battFract
            battStatus = (data[7] >> 4) & 0x7
            battStatusMsg = ['Reserved for future use',
                'New',
                'Good',
                'Ok',
                'Low',
                'Critical',
                'Reserved for future use',
                'Invalid'
            ]
            
            timeResolutionBit = (data[7] >> 7)
            if timeResolutionBit == 0:
                timeResolution = 16
            else:
                timeResolution = 2
                
            cumulativeOperatingTime = (data[3] +
                (data[4] << 8) + (data[5] << 16)) * timeResolution

            print('Page 82: Battery Voltage=', battVoltage,
                '| Battery Status=', battStatusMsg[battStatus],
                '| Cumulative Operating Time [s]=', cumulativeOperatingTime
            )

def main():
    OsynceRemoteControl()

if __name__ == "__main__":
    main()
