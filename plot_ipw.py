#!/usr/bin/env python
################################
# plot_ipw.py
#
# Makes plots for the IPW scan of the chosen 
# channel.  Stores plots in TFile and also 
# creates pdfs.
#
################################

#import waveform_tools
try:
    import utils
except ImportError:
    pass
try:
    import calc_utils
except ImportError:
    pass
import ROOT
import math
import optparse
import os

def read_scope_scan(fname):
    """Read data as read out and stored to text file from the scope.
    Columns are: ipw, pin, width, rise, fall, width (again), area.
    Rise and fall are opposite to the meaning we use (-ve pulse)
    """
    fin = file(fname,'r')
    ipw, ipw_err = [], []
    pin, pin_err = [], []
    width, width_err = [], []
    rise, rise_err = [], []
    fall, fall_err = [], []
    area, area_err = [], []
    mini, mimi_err = [], []
    for line in fin.readlines():
        if line[0]=="#":
            continue
        bits = line.split()
        if len(bits)!=7:
            continue
        ipw.append(int(bits[0]))
        ipw_err.append(int(bits[1]))
        pin.append(int(bits[2]))
        pin_err.append(int(bits[3]))
        width.append(float(bits[4]))
        width_err.append(float(bits[5]))
        rise.append(float(bits[6]))
        rise_err.append(float(bits[7]))
        fall.append(float(bits[8])) #rise in file -> fall
        fall_err.append(float(bits[9]))
        area.append(float(bits[10]))
        area_err.append(float(bits[11]))
        mini.append(float(bits[12]))
        mini_err.append(float(bits[13]))
    return ipw,pin,pin_err,width,width_err,rise,rise_err,fall,fall_err,area,area_err

def get_gain(applied_volts):
    """Get the gain from the applied voltage"""
    gain = None
    if applied_volts < 0.7:
        gain = 15460
    else:
        gain = 192750
    return gain

def get_scope_response(applied_volts):
    """Get the system timing response"""
    scope_response = None
    if applied_volts < 0.7:
        scope_response = 0.6741
    else:
        scope_response = 0.6459
    return scope_response

def adjust_width(seconds,applied_volts):
    """ Adjust the width, removing the scope response time"""
    time_correction = get_scope_response(applied_volts)
    try:
        width =  2.355*math.sqrt(((seconds * seconds)/(2.355*2.355))-time_correction*time_correction)
        return width
    except:
        print 'ERROR: Could not calculate the fall time. Returning 0'
        print seconds,time_correction
        return 0

def adjust_rise(seconds,applied_volts):
    """ Adjust EITHER the rise OR fall time (remove scope response)"""
    time_correction = get_scope_response(applied_volts)    
    try:
        width =  1.687*math.sqrt(((seconds * seconds)/(1.687*1.687))-time_correction*time_correction)
        return width
    except:
        print 'ERROR: Could not calculate the rise/fall time. Returning 0'
        print seconds,time_correction
        return 0

def get_photons(volts_seconds,applied_volts):
    """Use the integral (Vs) from the scope to get the number of photons.
    Can accept -ve or +ve pulse
    """
    impedence = 50.0 
    eV = 1.602e-19
    qe = 0.192 # @ 488nm
    gain = get_gain(applied_volts)
    photons = math.fabs(volts_seconds) / (impedence * eV * gain)
    photons /= qe
    return photons

def set_style(gr,style):
    if style==1:
        gr.SetMarkerColor(ROOT.kBlue+1)
        gr.SetMarkerStyle(4)
    else:
        gr.SetMarkerColor(ROOT.kRed+1)
        gr.SetMarkerStyle(25)
    
if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-f", dest="file")
    parser.add_option("-s", dest="scope", default="Tektronix")
    (options,args) = parser.parse_args()
    
    if options.scope!="Tektronix" and options.scope!="LeCroy":
        print "Can only run for LeCroy or Tektronix"
        sys.exit()

    sweep_type = options.file.split('/')[0]
    file_name = options.file.split('/')[1]
    box = int(file_name.split('_')[0][-2:])
    channel = int(file_name.split('_')[1][-1:])
    logical_channel = (box-1) * 8 + channel

    voltage = 0
    if sweep_type=="low_intensity":
        voltage = 0.8
    elif sweep_type=="broad":
        voltage = 0.6
    else:
        raise Exception,"unknown sweep type %s"%(sweep_type)

    dirname = os.path.join(sweep_type,"channel_%02d"%logical_channel)

    ipw,pin,pin_err,width,width_err,rise,rise_err,fall,fall_err,area,area_err = read_scope_scan(options.file)

    #make plots!
    photon_vs_pin = ROOT.TGraphErrors()
    photon_vs_ipw = ROOT.TGraphErrors()
    width_vs_photon = ROOT.TGraphErrors()
    width_vs_ipw = ROOT.TGraphErrors()
    rise_vs_photon = ROOT.TGraphErrors()
    rise_vs_ipw = ROOT.TGraphErrors()
    fall_vs_photon = ROOT.TGraphErrors()
    fall_vs_ipw = ROOT.TGraphErrors()
    pin_vs_ipw = ROOT.TGraphErrors()

    for i in range(len(ipw)):

        print "IPW: %04d"%(ipw[i])        

        #Plot measured values
        photon = get_photons(area[i],voltage)
        photon_err = get_photons(area_err[i], voltage)
        rise_time = adjust_rise(rise[i]*1e9,voltage)
        rise_time_err = adjust_rise(rise[i]*1e9, voltage)
        fall_time = adjust_rise(fall[i]*1e9,voltage)
        fall_time_err = adjust_rise(fall_err[i]*1e9, voltage)
        width_time = adjust_width(width[i]*1e9,voltage)
        width_time_err = adjust_width(width[i]*1e9, voltage)

        pin_vs_ipw.SetPoint(i,ipw[i],pin[i])

        photon_vs_pin.SetPoint(i,pin[i],photon)
        photon_vs_pin.SetPointError(i,pin_err[i],photon_err)
        photon_vs_ipw.SetPoint(i,ipw[i],photon)
        photon_vs_ipw.SetPointError(i,ipw_err[i],photon_err)
        rise_vs_photon.SetPoint(i,photon,rise_time)
        rise_vs_photon.SetPointError(i,photon_err,rise_time_err)
        rise_vs_ipw.SetPoint(i,ipw[i],rise_time)
        rise_vs_ipw.SetPointError(i,ipw_err[i],rise_time_err)
        fall_vs_photon.SetPoint(i,photon,fall_time)
        fall_vs_photon.SetPointError(i,photon_err,fall_time_err)
        fall_vs_ipw.SetPoint(i,ipw[i],fall_time)
        fall_vs_ipw.SetPointError(i,ipw_err[i],fall_time_err)
        width_vs_photon.SetPoint(i,photon,width_time)
        width_vs_photon.SetPointError(i,photon_err,width_time_err)
        width_vs_ipw.SetPoint(i,ipw[i],width_time)
        width_vs_ipw.SetPointError(i,ipw_err[i],width_time_err)


    set_style(pin_vs_ipw,1)
    set_style(photon_vs_pin,1)
    set_style(photon_vs_ipw,1)
    set_style(rise_vs_photon,1)
    set_style(rise_vs_ipw,1)
    set_style(fall_vs_photon,1)
    set_style(fall_vs_ipw,1)
    set_style(width_vs_photon,1)
    set_style(width_vs_ipw,1)

    photon_vs_pin.SetName("photon_vs_pin")
    photon_vs_ipw.SetName("photon_vs_ipw")
    width_vs_photon.SetName("width_vs_photon")
    width_vs_ipw.SetName("width_vs_ipw")
    rise_vs_photon.SetName("rise_vs_photon")
    rise_vs_ipw.SetName("rise_vs_ipw")
    fall_vs_photon.SetName("fall_vs_photon")
    fall_vs_ipw.SetName("fall_vs_ipw")

    output_dir = os.path.join(dirname,"plots")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    can = ROOT.TCanvas()

    pin_vs_ipw.Draw("ap")
    can.Print("%s/pin_vs_ipw.pdf"%output_dir)
    
    photon_vs_pin.Draw("ap")
    can.Print("%s/photon_vs_pin.pdf"%output_dir)

    photon_vs_ipw.Draw("ap")
    can.Print("%s/photon_vs_ipw.pdf"%output_dir)

    rise_vs_ipw.Draw("ap")
    can.Print("%s/rise_vs_ipw.pdf"%output_dir)

    rise_vs_photon.Draw("ap")
    can.Print("%s/rise_vs_photon.pdf"%output_dir)

    fall_vs_photon.Draw("ap")
    can.Print("%s/fall_vs_photon.pdf"%output_dir)

    fall_vs_ipw.Draw("ap")
    can.Print("%s/fall_vs_ipw.pdf"%output_dir)

    width_vs_photon.Draw("ap")
    can.Print("%s/width_vs_photon.pdf"%output_dir)

    width_vs_ipw.Draw("ap")
    can.Print("%s/width_vs_ipw.pdf"%output_dir)

    fout = ROOT.TFile("%s/plots.root"%output_dir,"recreate")
    
    photon_vs_pin.Write()
    photon_vs_ipw.Write()
    width_vs_photon.Write()
    width_vs_ipw.Write()
    rise_vs_photon.Write()
    rise_vs_ipw.Write()
    fall_vs_photon.Write()
    fall_vs_ipw.Write()

    fout.Close()

