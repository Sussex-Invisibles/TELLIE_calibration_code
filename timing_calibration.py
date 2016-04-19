#!/usr/bin/env python
###################################
# timing_calibration.py
#
#Does the timing calibration of the channels collects 10000 traces
#and caclulates the time difference between the trigger and pmt pulse
#
# Note that the rate is fixed (1 kHz)
#
###################################

import os
import sys
import optparse
import time
import sweep
import scopes
import scope_connections
import utils

if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-b",dest="box",help="Box number (1-12)")
    parser.add_option("-c",dest="channel",help="Channel number (1-8)")
    parser.add_option("-x",dest="cutoff",help="Cutoff (IPW) from Ref sweep (runs -1500 -> +500 of this value)")
    (options,args) = parser.parse_args()

    #Time
    total_time = time.time()
    
    #Set passed TELLIE parameters
    box = int(options.box)
    channel = int(options.channel)
    cutoff = int(options.cutoff)

    #Fixed parameters
    delay = 1.0 # 1ms -> kHz
    widths = range(cutoff-450,cutoff+361,45)
    #widths = range(cutoff-250,cutoff+601,15)

    #run the initial setup on the scope
    usb_conn = scope_connections.VisaUSB()
    scope = scopes.Tektronix3000(usb_conn)

    scope_channels = [1,4] # We're using channel 1 and 3 (1 for PMT 3 for probe point and 2 for the trigger signal)!
    termination = [50,50] # Ohms
    trigger_level = 1.4 # 
    falling_edge = True
    y_div_units = [0.2,0.5] # volts
    x_div_units = 100e-9 # seconds
    x_offset = +2*x_div_units # offset in x (2 divisions to the left)
    record_length = 10e3 # trace is 100e3 samples long
    half_length = record_length / 2 # For selecting region about trigger point
    ###########################################
    scope.unlock()
    scope.set_horizontal_scale(x_div_units)
    scope.set_sample_rate(2.5e9)
    scope.set_horizontal_delay(x_offset) #shift to the left 2 units
    scope.set_single_acquisition() # Single signal acquisition mode
    scope.set_record_length(record_length)
    scope.set_active_channel(1)
    scope.set_active_channel(4)
    scope.set_data_mode(half_length-1500, half_length+900)
    scope.set_edge_trigger(trigger_level, 4 , falling=False) # Rising edge trigger 
    y_offset = [-2.5*y_div_units[0],1.0]
    
    for i in range(len(scope_channels)):
	    scope.set_channel_y(scope_channels[i], y_div_units[i], pos=2.5)
	    scope.set_display_y(scope_channels[i], y_div_units[i], offset=y_offset[i])
	    scope.set_channel_termination(scope_channels[i], termination[i])
    scope.lock()
    scope.begin() # Acquires the pre-amble! 

    #Create a new, timestamped, summary file
    timestamp = time.strftime("%y%m%d_%H.%M",time.gmtime())
    sweep.check_dir('./timingCalibration')
    saveDir = sweep.check_dir("./timingCalibration/Box_%02d/" % (box))
    output_filename = "%s/Chan%02d_timing_%s.dat" % (saveDir,channel,timestamp)
    image_filename = "%s/Chan%02d_timing_%s.png" % (saveDir,channel,timestamp)
    jitterVals = []
    jitterErrs = [] 
    output_file = file(output_filename,'w')
    output_file.write("Width Jitter Error\n")

    #Start scanning!
    tmpResults = None
    t_start = time.time()
    for width in widths:
        min_volt = None
        loopStart = time.time()
        if tmpResults!=None:
            #set a best guess for the trigger and the scale
            #using the last sweeps value
            min_volt = float(tmpResults["peak"])
            if min_volt == 0: # If bad data set, make none
                min_volt = 200e-3 # Used to be None - Changed for speed-up!
        meanJitter, jitterError = sweep.sweep_timing(saveDir,box,channel,width,delay,scope,min_volt)
	jitterVals.append(meanJitter)
        jitterErrs.append(jitterError)
        print "Mean Jitter: "+str(meanJitter)
	output_file.write("%f %f %f\n" %(width,meanJitter,jitterError))
                

        print "WIDTH %d took : %1.1f s" % (width, time.time()-loopStart)
    output_file.close()

    print "Total script time : %1.1f mins"%( (time.time() - total_time) / 60)
    plt.errorbar(widths,jitterVals,yerr=jitterErrs)
    plt.show()
    plt.savefig(image_filename)
    
