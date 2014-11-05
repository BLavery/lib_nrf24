#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Example program to send packets to the radio link
#


import virtGPIO as GPIO
from lib_nrf24 import NRF24
import time



pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]

radio = NRF24(GPIO, GPIO.SpiDev())
radio.begin(10, 8) #Set spi-ce pin10, and rf24-CE pin 8
time.sleep(1)
radio.setRetries(15,15)
radio.setPayloadSize(32)
radio.setChannel(0x60)

radio.setDataRate(NRF24.BR_2MBPS)
radio.setPALevel(NRF24.PA_MIN)
radio.setAutoAck(True)
radio.enableDynamicPayloads()
radio.enableAckPayload()


radio.openWritingPipe(pipes[1])
radio.openReadingPipe(1, pipes[0])
radio.printDetails()


c=1
while True:
    buf = ['H', 'E', 'L', 'O',c]
    c = (c + 1) & 255
    # send a packet to receiver
    radio.write(buf)
    print ("Sent:"),
    print (buf)
    # did it return with a payload?
    if radio.isAckPayloadAvailable():
        pl_buffer=[]
        radio.read(pl_buffer, radio.getDynamicPayloadSize())
        print ("Received back:"),
        print (pl_buffer)
    else:
        print ("Received: Ack only, no payload")
    time.sleep(10)
