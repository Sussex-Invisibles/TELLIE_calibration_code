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
import numpy as np
import optparse
import os

def read_scope_scan(fname):
    """Read data as read out and stored to text file from the scope.
    Columns are: ipw, pin, width, rise, fall, width (again), area.
    Rise and fall are opposite to the meaning we use (-ve pulse)
    """
    fin = file(fname,'r')
    resultsList = []
    for line in fin.readlines():
        if line[0]=="#":
            continue
        bits = line.split()
        if len(bits)!=14:
            continue
        # Append needs to all be done in one. If we make a dict 'results = {}' which we 
        # re-write and append it fills with all the same object and so we have multiple copies
        # of the same result.
        resultsList.append({"ipw":int(bits[0]),"ipw_err": int(bits[1]),"pin":int(bits[2]),"pin_err":int(bits[3]),"width":float(bits[4]),"width_err":float(bits[5]),"rise":float(bits[6]),"rise_err":float(bits[7]),"fall":float(bits[8]),"fall_err":float(bits[9]),"area":float(bits[10]),"area_err":float(bits[11]),"mini":float(bits[12]),"mini_err":float(bits[13])})
    return resultsList

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
    return seconds
    time_correction = get_scope_response(applied_volts)
    try:
        width =  2.355*np.sqrt(((seconds * seconds)/(2.355*2.355))-time_correction*time_correction)
        return width
    except:
        print 'ERROR: Could not calculate the fall time. Returning 0'
        print seconds,time_correction
        return 0

def adjust_rise(seconds,applied_volts):
    """ Adjust EITHER the rise OR fall time (remove scope response)"""
    return seconds
    time_correction = get_scope_response(applied_volts)    
    try:
        width =  1.687*np.sqrt(((seconds * seconds)/(1.687*1.687))-time_correction*time_correction)
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
    photons = np.fabs(volts_seconds) / (impedence * eV * gain)
    photons /= qe
    return photons

def set_style(gr,style=1,title_size=0.04):
    gr.GetXaxis().SetTitleSize(title_size)
    gr.GetYaxis().SetTitleSize(title_size)
    if style==1:
        gr.SetMarkerStyle(8)
        gr.SetMarkerSize(0.5)
    if style==2:
        gr.SetMarkerColor(ROOT.kRed+1)
        gr.SetLineColor(ROOT.kRed+1)
        gr.SetMarkerStyle(8)
        gr.SetMarkerSize(0.5)
    if style==3:
        gr.SetMarkerColor(ROOT.kBlue+1)
        gr.SetLineColor(ROOT.kBlue+1)
        gr.SetMarkerStyle(8)
        gr.SetMarkerSize(0.5)        

def master_plot(fname, ph_ipw, w_ipw, r_ipw, f_ipw, pin_ipw, ph_pin):
    # Create nea canvas and split it into four
    nCan = ROOT.TCanvas()
    nCan.Divide(2,2)
    nCan.cd(1)
    set_style(ph_ipw, title_size=0.053)
    ph_ipw.Draw("AP")

    nCan.cd(2)
    multi = ROOT.TMultiGraph()
    set_style(w_ipw)
    set_style(r_ipw, style=2)
    set_style(f_ipw,style=3)
    multi.Add(w_ipw)
    multi.Add(r_ipw)
    multi.Add(f_ipw)
    multi.Draw("APL")
    multi.GetXaxis().SetTitle("IPW (14 bit)")
    multi.GetYaxis().SetTitle("Time (ns)")
    multi.GetXaxis().SetTitleSize(0.053)
    multi.GetYaxis().SetTitleSize(0.053)
    multi.Draw("AP")

    nCan.cd(3)
    set_style(pin_ipw, title_size=0.053)
    pin_ipw.Draw("AP")

    nCan.cd(4)
    set_style(ph_pin, title_size=0.053)
    ph_pin.Draw("AP")

    nCan.Print(fname)    
    
    
if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-f", dest="file")
    parser.add_option("-s", dest="scope", default="Tektronix")
    (options,args) = parser.parse_args()
    
    if options.scope!="Tektronix" and options.scope!="LeCroy":
        print "Can only run for LeCroy or Tektronix"
        sys.exit()

    p =  options.file.split('/')
    sweep_type = p[0]
    file_name = p[1]
    box = int(p[1][-2:])
    channel = int(p[2][4:6])
    logical_channel = (box-1) * 8 + channel
    print sweep_type, file_name, box, channel, logical_channel

    voltage = 0
    if sweep_type=="low_intensity":
        voltage = 0.8
    elif sweep_type=="broad":
        voltage = 0.6
    else:
        raise Exception,"unknown sweep type %s"%(sweep_type)

    dirname = os.path.join(sweep_type,"plots/channel_%02d"%logical_channel)

    res_list = read_scope_scan(options.file)

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

    for i in range(len(res_list)):

        print "IPW: %04d"%(res_list[i]["ipw"])

        #Plot measured values
        photon = get_photons(res_list[i]["area"],voltage)
        photon_err = get_photons(res_list[i]["area_err"], voltage)
        rise_time = adjust_rise(res_list[i]["rise"]*1e9,voltage)
        rise_time_err = res_list[i]["rise_err"]*1e9
        fall_time = adjust_rise(res_list[i]["fall"]*1e9,voltage)
        fall_time_err = res_list[i]["fall_err"]*1e9
        width_time = adjust_width(res_list[i]["width"]*1e9,voltage)
        width_time_err = res_list[i]["width_err"]*1e9

        pin_vs_ipw.SetPoint(i,res_list[i]["ipw"],res_list[i]["pin"])

        photon_vs_pin.SetPoint(i,res_list[i]["pin"],photon)
        photon_vs_pin.SetPointError(i,res_list[i]["pin_err"],photon_err)
        photon_vs_ipw.SetPoint(i,res_list[i]["ipw"],photon)
        photon_vs_ipw.SetPointError(i,res_list[i]["ipw_err"],photon_err)
        rise_vs_photon.SetPoint(i,photon,rise_time)
        rise_vs_photon.SetPointError(i,photon_err,rise_time_err)
        rise_vs_ipw.SetPoint(i,res_list[i]["ipw"],rise_time)
        rise_vs_ipw.SetPointError(i,res_list[i]["ipw_err"],rise_time_err)
        fall_vs_photon.SetPoint(i,photon,fall_time)
        fall_vs_photon.SetPointError(i,photon_err,fall_time_err)
        fall_vs_ipw.SetPoint(i,res_list[i]["ipw"],fall_time)
        fall_vs_ipw.SetPointError(i,res_list[i]["ipw_err"],fall_time_err)
        width_vs_photon.SetPoint(i,photon,width_time)
        width_vs_photon.SetPointError(i,photon_err,width_time_err)
        width_vs_ipw.SetPoint(i,res_list[i]["ipw"],width_time)
        width_vs_ipw.SetPointError(i,res_list[i]["ipw_err"],width_time_err)


    set_style(pin_vs_ipw,1)
    set_style(photon_vs_pin,1)
    set_style(photon_vs_ipw,1)
    set_style(rise_vs_photon,1)
    set_style(rise_vs_ipw,1)
    set_style(fall_vs_photon,1)
    set_style(fall_vs_ipw,1)
    set_style(width_vs_photon,1)
    set_style(width_vs_ipw,1)

    # Add titles and labels
    pin_vs_ipw.SetName("pin_vs_ipw")
    pin_vs_ipw.GetXaxis().SetTitle("IPW (14 bit)")
    pin_vs_ipw.GetYaxis().SetTitle("PIN reading (16 bit)")
    photon_vs_pin.SetName("photon_vs_pin")
    photon_vs_pin.GetXaxis().SetTitle("PIN reading (16 bit)")
    photon_vs_pin.GetYaxis().SetTitle("No. photons")
    photon_vs_ipw.SetName("photon_vs_ipw")
    photon_vs_ipw.GetXaxis().SetTitle("IPW (14 bit)")
    photon_vs_ipw.GetYaxis().SetTitle("No. photons")
    width_vs_photon.SetName("width_vs_photon")
    width_vs_photon.GetXaxis().SetTitle("No. photons")
    width_vs_photon.GetYaxis().SetTitle("Pulse FWHM (ns)")
    width_vs_ipw.SetName("width_vs_ipw")
    width_vs_ipw.GetXaxis().SetTitle("IPW (14 bit)")
    width_vs_ipw.GetYaxis().SetTitle("Pulse FWHM (ns)")
    rise_vs_photon.SetName("rise_vs_photon")
    rise_vs_photon.GetXaxis().SetTitle("No. photons")
    rise_vs_photon.GetYaxis().SetTitle("Rise time (ns)")
    rise_vs_ipw.SetName("rise_vs_ipw")
    rise_vs_ipw.GetXaxis().SetTitle("IPW (14 bit)")
    rise_vs_ipw.GetYaxis().SetTitle("Rise time (ns)")
    fall_vs_photon.SetName("fall_vs_photon")
    fall_vs_photon.GetXaxis().SetTitle("No. photons")
    fall_vs_photon.GetYaxis().SetTitle("Fall time (ns)")
    fall_vs_ipw.SetName("fall_vs_ipw")
    fall_vs_ipw.GetXaxis().SetTitle("IPW (14 bit)")
    fall_vs_ipw.GetYaxis().SetTitle("Fall time (ns)")

    output_dir = os.path.join(dirname)
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

    out_dir = os.path.join(sweep_type,"plots/")
    master_name = "%s/Chan%02d_%s.pdf" % (out_dir, logical_channel, sweep_type)
    master_plot(master_name, photon_vs_ipw, width_vs_ipw, rise_vs_ipw, fall_vs_ipw, pin_vs_ipw, photon_vs_pin)

    fout.Close()

