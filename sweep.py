#!/usr/bin/env python
#########################
# sweep.py
#  Generic module for running
# IPW sweeps with Tek scope
#
#########################

import os
from core import serial_command
from common import comms_flags
import math
import time
#try:
import utils
#except:
#    pass
import sys
import readPklWaveFile
import calc_utils as calc
import numpy as np

port_name = "/dev/tty.usbserial-FTE3C0PG"
## TODO: better way of getting the scope type
scope_name = "Tektronix3000"
_boundary = [0,1.5e-3,3e-3,7e-3,15e-3,30e-3,70e-3,150e-3,300e-3,700e-3,1000]
#_v_div = [1e-3,2e-3,5e-3,10e-3,20e-3,50e-3,100e-3,200e-3,500e-3,1.0,1000]
_v_div = [1e-3,2e-3,5e-3,10e-3,20e-3,50e-3,100e-3,200e-3,500e-3,1.0]
_v_div_1 = [1e-3,2e-3,5e-3,10e-3,20e-3,50e-3,100e-3,200e-3,500e-3,1.0,2.0]

sc = None
sc = serial_command.SerialCommand(port_name)

#initialise sc here, faster options setting
def start():
    global sc
    sc = serial_command.SerialCommand(port_name)

def set_port(port):
    global port_name
    port_name = port

def set_scope(scope):
    global scope_name
    if scope=="Tektronix3000" or scope=="LeCroy":
        scope_name = scope
    else:
        raise Exception("Unknown scope")

def check_dir(dname):
        """Check if directory exists, create it if it doesn't"""
        direc = os.path.dirname(dname)
        try:
                os.stat(direc)
        except:
                os.mkdir(direc)
                print "Made directory %s...." % dname
        return dname    

def save_scopeTraces(fileName, scope, channel, noPulses):

    scope._get_preamble(channel)
    results = utils.PickleFile(fileName, 1)
    results.add_meta_data("timeform_1", scope.get_timeform(channel))
    
    t_start, loopStart = time.time(),time.time()
    for i in range(noPulses):
        scope.acquire() # Wait for triggered acquisition
        try:
            results.add_data(scope.get_waveform(channel), 1)
        except Exception, e:
            print "Scope died, acquisition lost."
            print e
        if i % 100 == 0 and i > 0:
            print "%d traces collected - This loop took : %1.1f s" % (i, time.time()-loopStart)
            loopStart = time.time()
    print "%d traces collected TOTAL - took : %1.1f s" % (i, (time.time()-t_start))
    results.save()
    results.close()


def find_and_set_scope_y_scale(channel,height,width,delay,scope,scaleGuess=None):
    """Finds best y_scaling for current pulses
    """
    func_time = time.time()
    sc.fire_continuous()
    time.sleep(0.1)
    
    # If no scale guess, try to find reasonable trigger crossings at each y_scale
    if scaleGuess==None:
        for i, val in enumerate(_v_div):
            #print "Setting scope scale to %1.2fV, trigger @ %1.2fV..." % (_v_div[-1*(i+1)], -1*_v_div[-1*(i+1)])
            scope.unlock()
            scope.set_channel_y(channel,_v_div[-1*(i+1)], pos=3) # set scale, starting with largest
            scope.set_edge_trigger( (-1*_v_div[-1*(i+1)]), channel, falling=True)
            scope.lock()
            if i==0:
                time.sleep(0.2) # Need to wait to clear previous triggered state
            ct = scope.acquire_time_check(True) # Wait for triggered acquisition
            if ct == True:
                break
    else: #Else use the guess
        if abs(scaleGuess) > 1:
            guess_v_div = _v_div
        else:
            tmp_idx = np.where( np.array(_v_div) >= abs(scaleGuess) )[0][0]
            guess_v_div = _v_div[0:tmp_idx]
        for i, val in enumerate(guess_v_div):
            #print "Setting scope scale to %1.2fV, trigger @ %1.2fV..." % (guess_v_div[-1*(i+1)], -1*guess_v_div[-1*(i+1)])
            scope.unlock()
            scope.set_channel_y(channel,guess_v_div[-1*(i+1)],pos=3) # set scale, starting with largest
            scope.set_edge_trigger( (-1*guess_v_div[-1*(i+1)]), channel, falling=True)
            scope.lock()
            if i==0:
                time.sleep(0.2) # Need to wait to clear previous triggered state
            ct = scope.acquire_time_check(True) # Wait for triggered acquisition
            if ct == True:
                break

    scope._get_preamble(channel)
    time.sleep(0.2)
    # Calc min value
    mini = np.zeros( 10 )
    for i in range( len(mini) ):
        wave = scope.get_waveform(channel)
        mini[i] = min(wave) #- np.mean(wave[0:50])
    min_volt = np.mean(mini)
    print "MINIMUM MEASUREMENT:", min_volt

    # Set scope
    scale_idx = np.where( np.array(_v_div_1) > -1*(min_volt/6) )[0][0]
    scale = _v_div_1[scale_idx]
    if scale <= 2e-3:
        trig = -1.5*scale
    else:
        trig = -1.*scale
    print "Preticted scale = %1.3fV, actual scale = %1.3fV, trigger @ %1.4fV" % (-1*(min_volt/6.6) , scale, trig)
    scope.unlock()
    scope.set_channel_y( channel, scale, pos=3) # set scale, starting with largest
    scope.set_edge_trigger( trig, channel, falling=True)
    scope.lock()

    print "TOTAL FUNC TIME = %1.2f s" % (time.time() - func_time)
    sc.stop()
    return 0
    

def sweep(dir_out,file_out,box,channel,width,delay,scope,min_volt=None):
    """Perform a measurement using a default number of
    pulses, with user defined width, channel and rate settings.
    """
    print '____________________________'
    print width
    #fixed options
    height = 16383    
    fibre_delay = 0
    trigger_delay = 0
    pulse_number = 1000
    #first select the correct channel and provide settings
    logical_channel = (box-1)*8 + channel
    
    sc.select_channel(logical_channel)
    sc.set_pulse_width(width)
    sc.set_pulse_height(16383)
    sc.set_pulse_number(pulse_number)
    sc.set_pulse_delay(delay)
    sc.set_fibre_delay(fibre_delay)
    sc.set_trigger_delay(trigger_delay)
    
    # first, run a single acquisition with a forced trigger, effectively to clear the waveform
    scope._connection.send("trigger:state ready")
    time.sleep(0.1)
    scope._connection.send("trigger force")
    time.sleep(0.1)
    
    tmp = find_and_set_scope_y_scale(1,height,width,delay,scope,scaleGuess=min_volt)
    #sys.exit('Finished!')
    
    #sc.set_pulse_number(pulse_number)
    time.sleep(0.1)
    sc.fire_averaged() # previously fire_sequence!
    #wait for the sequence to end
    tsleep = pulse_number * (delay*1e-3 + 210e-6)
    time.sleep(tsleep) #add the offset in
    pin = None
   # while not comms_flags.valid_pin(pin,channel):
    while pin==None:
        pin, _ = sc.read_pin_sequence()
    print "PIN (sweep):",pin
    sc.stop()

    directory = check_dir("%s/raw_data/Channel_%02d"%(dir_out,logical_channel))
    fname = "%s/Width%05d" % (directory,width)
    print "Saving raw files to: %s..." % fname
    sc.fire_continuous()
    time.sleep(0.1)
    save_scopeTraces(fname, scope, 1, 100)
    x,y = calc.readPickleChannel(fname, 1)
    sc.stop()
    scope.unlock()

    #have saved a waveform, now save rise,fall,pin et
    #results = {}
    #results["area"], results["area error"] = calc.calcArea(x,y)
    #results["rise"], results["rise error"] = calc.calcRise(x,y)
    #results["fall"], results["fall error"] = calc.calcFall(x,y)
    #results["width"], results["width error"] = calc.calcWidth(x,y)
    #results["minimum"], results["minimum error"] = calc.calcPeak(x,y)
    results = calc.dictionary_of_params(x,y)
    results["pin"] = pin[logical_channel]
    calc.printParamsDict(results, width)
    calc.plot_eg_pulses(x,y,10, fname='./low_intensity/LastMeasuredPulses.png')
    os.system("open ./low_intensity/LastMeasuredPulses.png")

    return results
