#!/usr/bin/python
#
# Example program to send packets between 2 NRF24L01+ radios
#
# Demonstrates:  2 x NRF24 radios both operating from SPI on one virt-GPIO, doing 2-way radio data transfer
#                Dynamic payload size both ways (to 32 bytes).
#                "Auto-Ack" mode, with "ack-payload" carrying the return data.
#                Forward payload and return ack-payload data content is rather arbitrary, but is identifiable.
#                (Single PTX-PRX link is demonstrated, although PRX has 6-channel capacity.)

# Setup: 2 x NRF24L01+ (each with 5V to 3.3V "adapter plate") (total eBay cost under $5, "8 pin" types)
#        Radio1 in PTX (master) mode, radio2 in PRX (slave/server) mode.
#        Pins: Radio1  Arduino pin9 as NRF24-CSN (spi CE), Tie RF24-CE to HIGH (+3 or +5)
#              Radio2  Arduino pin10 as NRF24-CSN, Tie RF24-CE to HIGH (+3 or +5)
#                  (VirtGPIO/arduino uses notation "CE" differently from NRF24 usage!)
#              Both radios: Arduino pin11 = MOSI,  pin12 = MISO,  pin13 = SCLK
#        Note: NRF24 power MUST be 3.3V, NOT 5v. (Its data pins may operate at 3.3V or 5V.)

#        Optionally, a LED on pin6, as switched-across "activity Led".


import virtGPIO as GPIO
from lib_nrf24 import NRF24
import time


pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]

# Comment re multiple SPIDEV devices:
# Official spidev documentation is sketchy. Implementation in virtGPIO allows multiple SpiDev() objects.
# This may not work on RPi? Probably RPi uses alternating open() / xfer2() /close() within one SpiDev() object???
# On virtGPIO each of multiple SpiDev() stores its own mode and cePin. Multiple RF24 used here becomes easy.
# This issue affects only using MULTIPLE Spi devices.

##################################################################
# SET UP RADIO1 - PTX

radio1 = NRF24(GPIO, GPIO.SpiDev())
radio1.begin(9)       # SPI-CE=RF24-CSN=pin9, no RF24-CE pin
time.sleep(1)
radio1.setRetries(15,15)
radio1.setPayloadSize(32)
radio1.setChannel(0x62)
radio1.setDataRate(NRF24.BR_2MBPS)
radio1.setPALevel(NRF24.PA_MIN)
radio1.setAutoAck(True)
radio1.enableDynamicPayloads()
radio1.enableAckPayload()

radio1.openWritingPipe(pipes[1])
radio1.openReadingPipe(1, pipes[0])

if not radio1.isPVariant():
    # If radio configures correctly, we confirmed a "plus" (ie "variant") nrf24l01+
    # Else print diagnostic stuff & exit.
    radio1.printDetails()
    # (or we could always just print details anyway, even on good setup, for debugging)
    print ("NRF24L01+ not found.")
    exit()


##################################################################
# AND THEN RADIO2 - PRX  - VIRTUALLY IDENTICAL !

radio2 = NRF24(GPIO, GPIO.SpiDev())
radio2.begin(10)    # SPI-CE=RF24-CSN=pin10, no RF24-CE pin
time.sleep(1)
radio2.setRetries(15,15)

radio2.setPayloadSize(32)
radio2.setChannel(0x62)
radio2.setDataRate(NRF24.BR_2MBPS)
radio2.setPALevel(NRF24.PA_MIN)

radio2.setAutoAck(True)
radio2.enableDynamicPayloads()
radio2.enableAckPayload()

radio2.openWritingPipe(pipes[0])
radio2.openReadingPipe(1, pipes[1])

radio2.startListening()

if not radio2.isPVariant():
    radio2.stopListening()
    radio2.printDetails()
    print ("NRF24L01+ not found.")
    exit()


##################################################################
c1 = 1
def serviceRadio1():
    # Let's deal with PTX - radio1:

    print ("TX:")
    global c1
    global radio1
    buf = ['H', 'E', 'L', 'O',(c1 & 255)]   # something to recognise at other end
    c1 += 1
    # send a packet to receiver
    radio1.write(buf)
    # RF24 handles all timeouts, retries and ACKs and ACK-payload
    # So the call to radio.write() only returns after ack and its payload have finished
    print ("\033[31;1mPTX Sent:\033[0m"),
    print (buf)
    # did a payload come back with the ACK?
    if radio1.isAckPayloadAvailable():
        pl_buffer=[]
        radio1.read(pl_buffer, radio1.getDynamicPayloadSize())
        print ("\033[31;1mPTX Received back:\033[0m"),
        print (pl_buffer)
    else:
        print ("PTX Received: Ack only, no payload")

##################################################################
c2 = 1
def serviceRadio2():
    # Now deal separately with  PRX - radio 2
    print ("RX?")
    global c2
    global radio2
    akpl_buf = [(c2& 255),1, 2, 3,4,5,6,7,8,9,0,1, 2, 3,4,5,6,7,8]  # We should see this returned to PTX
    pipe = [0]
    if not radio2.available(pipe):
        return

    recv_buffer = []
    radio2.read(recv_buffer, radio2.getDynamicPayloadSize())
    print ("\033[32;1mPRX Received:\033[0m") ,
    print (recv_buffer)
    c2 += 1
    if (c2&1) == 0:   # alternate times - so we can see difference beteeen ack-payload and no ack-payload
        radio2.writeAckPayload(1, akpl_buf, len(akpl_buf))
        print ("PRX Loaded payload reply:"),
        print (akpl_buf)
    else:
        print ("PRX: (No return payload)")


##################################################################
# We could experiment with differing payload lengths above, up to max 32 bytes each way.


c=0
while True:
    c += 1
    print ("Loop %d" % c),
    if not (c % 3):    # only once per x loops
        serviceRadio1()   # send something
        time.sleep(0.01)
    else:
        serviceRadio2()    # has it arrived? (if so, maybe send return data)
        time.sleep(2)   # 1 sec per loop
