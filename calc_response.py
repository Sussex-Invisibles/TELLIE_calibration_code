#################################################
# calc_response.py
#
# This script calculates the photon an PIN response
# constants for each of the 96 channels.
#################################################
import plot_ipw
import ROOT
import numpy as np 
import optparse
import time
import datetime
import os

def find_most_recent_file(files):
    '''Find the most recent file from passed array
    '''
    dt = []
    for idx, f in enumerate(files):
        s = f[14:26]
        formatted = "20%s %s %s %s:%s" % (s[0:2], s[2:4], s[4:6], s[7:9], s[10:12])
        current = datetime.datetime.strptime(formatted, '%Y %m %d %H:%M')
        dt.append(current)
        if current == max(dt):
            index = idx
    return files[index]

def return_files(base, box):
    '''Return an array containing the most up-to-date data files for a given box and sweep type
    '''
    base_path = "%s/Box_%02d/" % (base, box)
    allFiles = [ f for f in os.listdir(base_path) if os.path.isfile(os.path.join(base_path,f)) ]
    mostRecentFiles = []
    for i in range(1,9,1):
        filesForChan = []
        for f in allFiles:
            if int(f[5]) == i:
                filesForChan.append(f)
        if len(filesForChan) == 1:
            mostRecentFiles.append("%s%s" % (base_path, filesForChan[0]))
        else:
            mostRecentFiles.append("%s%s" %(base_path, find_most_recent_file(filesForChan)))
    return mostRecentFiles
  
def return_boxes():
    '''Find which boxes we have data for.
    '''
    box = []
    for i in range(1,13,1):
        if os.path.exists("low_intensity/Box_%02d"%i):
            box.append(i)
    return box

if __name__ == "__main__":
    parser = optparse.OptionParser()
    #parser.add_option("-b", dest="box", default="all")
    (options,args) = parser.parse_args()
    
    fout = ROOT.TFile("fits/rootFiles.root","recreate")
    ipwCan = ROOT.TCanvas()
    pinCan = ROOT.TCanvas()
    #ipwCan.Divide(2,1)
    #pinCan.Divide(2,1)
    
    boxes = return_boxes()
    for box in boxes:
        # broadFiles = return_files("broad_sweep", box)
        lowFiles = return_files("low_intensity", box)
        for j in range(len(lowFiles)):
            # broadVals = plot_ipw.read_scope_scan(broadFiles[j])
            lowVals = plot_ipw.read_scope_scan(lowFiles[j])
            # Creat plots
            # photonVsPIN_broad = ROOT.TGraphErrors()
            # photonVsIPW_broad = ROOT.TGraphErrors()
            photonVsPIN_low = ROOT.TGraphErrors()
            photonVsIPW_low = ROOT.TGraphErrors()
            for i in range(len(lowVals)):
                # photonBroad = plot_ipw.get_photons(broadVals[i]["area"], 0.7)
                # photonErrBroad = plot_ipw.get_photons(broadVals[i]["area_err"], 0.7)
                photonLow = plot_ipw.get_photons(lowVals[i]["area"], 0.7)
                photonErrLow = plot_ipw.get_photons(lowVals[i]["area_err"], 0.7)
        
                # Fill plots with data
                # Note: Data points are returned as mean and stdev(rms)
                #       for fitting uncertainties should be given as standard error. 
                # photonVsPIN_broad.SetPoint(i,broadVals[i]["pin"],photonBroad)
                # photonVsPIN_broad.SetPointError(i,broadVals[i]["pin_err"]/np.sqrt(100),photonErrBroad/np.sqrt(100))
                # photonVsIPW_broad.SetPoint(i,broadVals[i]["ipw"],photonBroad)
                # photonVsIPW_broad.SetPointError(i,0,photonErrBroad/np.sqrt(100)) 
                photonVsPIN_low.SetPoint(i,lowVals[i]["pin"],photonLow)
                photonVsPIN_low.SetPointError(i,lowVals[i]["pin_err"]/np.sqrt(100),photonErrLow/np.sqrt(100))
                photonVsIPW_low.SetPoint(i,lowVals[i]["ipw"],photonLow)
                photonVsIPW_low.SetPointError(i,0,photonErrLow/np.sqrt(100)) 

            # Add titles and labels
            logical_channel = (int(lowFiles[j][-33:-31])-1)*8 + int(lowFiles[j][-26:-24])
            # photonVsPIN_broad.SetName("Chan%02d_PIN_broad"%logical_channel)
            # photonVsPIN_broad.GetXaxis().SetTitle("PIN reading (16 bit)")
            # photonVsPIN_broad.GetYaxis().SetTitle("No. photons")
            # photonVsIPW_broad.SetName("Chan%02d_IPW_broad"%logical_channel) 
            # photonVsIPW_broad.GetXaxis().SetTitle("IPW (14 bit)")
            # photonVsIPW_broad.GetYaxis().SetTitle("No. photons")
            photonVsPIN_low.SetName("Chan%02d_PIN_low"%logical_channel)
            photonVsPIN_low.GetXaxis().SetTitle("PIN reading (16 bit)")
            photonVsPIN_low.GetYaxis().SetTitle("No. photons")
            photonVsIPW_low.SetName("Chan%02d_IPW_low"%logical_channel)
            photonVsIPW_low.GetXaxis().SetTitle("IPW (14 bit)")
            photonVsIPW_low.GetYaxis().SetTitle("No. photons")

            # plot_ipw.set_style(photonVsPIN_broad,1)
            # plot_ipw.set_style(photonVsIPW_broad,1)
            plot_ipw.set_style(photonVsPIN_low,1)
            plot_ipw.set_style(photonVsIPW_low,1)

            pinCan.Clear()
            # pinCan.cd(1) 
            # photonVsPIN_broad.Draw("ap")
            # pinCan.cd(2)
            photonVsPIN_low.Draw("ap")
        
            ipwCan.Clear()
            # ipwCan.cd(1)
            # photonVsIPW_broad.Draw("ap")
            # ipwCan.cd(2)
            photonVsIPW_low.Draw("ap")

            pdf_dir = "fits/pdfs"
            if not os.path.exists(pdf_dir):
                os.makedirs(pdf_dir)
            pinCan.Print("%s/Chan%02d_PIN.pdf"%(pdf_dir,logical_channel))
            ipwCan.Print("%s/Chan%02d_IPW.pdf"%(pdf_dir,logical_channel))
            # photonVsPIN_broad.Write()
            photonVsPIN_low.Write()
            # photonVsIPW_broad.Write()
            photonVsIPW_low.Write()
