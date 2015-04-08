#!/usr/bin/env python
#########################
# PIN_check.py
#
# Check PIN output for each
# board in TELLIE rack.
#########################

import os
from core import serial_command
from common import comms_flags
import time

#def check_boxes(full_dict):
    #channels = full_dict.keys()
#    for idx, dict_ent in enumerate(full_dict):
#        channel = idx+1
#        print idx, dict_ent[channel]

if __name__=="__main__":

    # Counter
    script_time = time.time()
    
    # Set-up boxes and channels
    box = range(1,13)
    channel = range(1,9)
    full_dict = []
    working_channels = []
    dead_channels = []
    
    # Standard settings
    IPW = 3000 # Pulse well below the max IPW for all boards
    height = 16383
    delay = 1 # ms -> 1 kHz
    fibre_delay = 0
    trigger_delay = 0
    pulse_number = 100

    # Set up serial connection
    sc = serial_command.SerialCommand("/dev/tty.usbserial-FTE3C0PG")

    for box_no in box:
        for channel_no in channel:
            logical_channel = (box_no-1)*8 + channel_no
            if logical_channel < 96:
                
                sc.select_channel(logical_channel)
                sc.set_pulse_width(IPW)
                sc.set_pulse_height(height)
                sc.set_pulse_number(pulse_number)
                sc.set_pulse_delay(delay)
                sc.set_fibre_delay(fibre_delay)
                sc.set_trigger_delay(trigger_delay)

                time.sleep(0.1)
                sc.fire_sequence()
                #wait for the sequence to end
                tsleep = pulse_number * (delay*1e-3 + 210e-6)
                #time.sleep(tsleep) #add the offset in
                pin = None
                # while not comms_flags.valid_pin(pin,channel):
                while pin==None:
                    pin, _ = sc.read_pin_sequence()
                    #pin, _ = sc.read_pin()
                full_dict.append(pin)
                pin_read = int(pin[_[0]])
                print "Channel : %2d \t PIN : %d"%(logical_channel, pin_read)
            
                if pin_read is not 0:
                    working_channels.append(logical_channel)
                else:
                    dead_channels.append(logical_channel)

    # Save results to file .txt
    #timestamp = time.strftime("%y%m%d_%H.%M.%S",time.gmtime())
    timestamp = time.strftime("%d%m%y_%H.%M",time.gmtime())
    dir = "./PIN_response"
    output_filename = "%s/PIN_readings_%s.dat" % (dir,timestamp)
    # Write header
    f=open(output_filename,'w')
    f.write("Channel\tMeasure at IPW = %d\n"%IPW)
    for idx, dict_ent in enumerate(full_dict):
        channel = idx+1
        if (idx % 8 == 0):
            f.write("------Box%2d-------\n"%((idx/8)+1))
        f.write("%d\t%d\n"%(channel,int(dict_ent.values()[0])))
        #if (dict_ent.values()[0] == 0):
        #    f.write("%d\t0\n"%channel)
        #else:
        #    f.write("%d\t1\n"%channel)
        
    f.close()
    print "Script took : %1.2f mins"%( (time.time() - script_time)/60 )


