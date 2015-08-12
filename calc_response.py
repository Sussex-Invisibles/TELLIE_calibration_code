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
import csv

def find_most_recent_file(files):
    '''Find the most recent file from passed array
    '''
    dt = []
    for idx, f in enumerate(files):
        s = f[-16:]
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
            if f == '.DS_Store':
                continue
            if int(f[5]) == i:
                filesForChan.append(f)
        if len(filesForChan) == 1:
            mostRecentFiles.append("%s%s" % (base_path, filesForChan[0]))
        elif len(filesForChan) > 1:
            mostRecentFiles.append("%s%s" %(base_path, find_most_recent_file(filesForChan)))
    return mostRecentFiles
  
def return_boxes(path):
    '''Find which boxes we have data for.
    '''
    box = []
    for i in range(1,13,1):
        if os.path.exists("%s/Box_%02d"%(path, i)):
            box.append(i)
    return box

def check_data(vals):
    '''Check calcualted values for anomalies. Return array containing non-anomalous results
    '''
    idx = []
    for i in range(len(vals)):
        if i > 0:
            if vals[i]["area"] > vals[i-1]["area"]:
                idx.append(i)
        elif vals[i]["area"] != 0: # In one case the first value is zero
            idx.append(i)
    return map(vals.__getitem__, idx)

def fit_ipw(plot, can):
    '''Function to fit IPW_vs_Photons plot. Returns the fit object and fitted TGraphErrors.
    '''
    fit = ROOT.TF1("total", "[0] + [1]*x + [2]*(x*x)")
    fit.SetLineColor(2)
    plot.Fit(fit, "FMQ") # Use minut with 'improved fit'
    can.Update()
    return fit, plot, can

def fit_pin(plot, can):
    '''Function to fit PIN_vs_Photons plot. Returns the fit object and fitted TGraphErrors.
    '''
    fit = ROOT.TF1("f1","[0] + [1]*x")
    x,y = get_xy(plot)
    grad = (y[-1]-y[0])/(x[-1]-x[0])
    fit.SetParameter(0, -1e4)
    fit.SetParameter(1, grad)
    fit.SetLineColor(2)
    plot.Fit(fit, "FMQ") # Use minut with 'improved fit'
    can.Update()
    st = plot.GetListOfFunctions().FindObject("stats")
    st.SetX1NDC(0.32)
    st.SetX2NDC(0.67)    
    return fit, plot, can

def get_xy(plot):
    '''Return  x, y arrays from TGraph
    '''
    x_buff = plot.GetX()
    y_buff = plot.GetY()
    N = plot.GetN()
    x_buff.SetSize(N)
    y_buff.SetSize(N)
    return np.array(x_buff,copy=True), np.array(y_buff,copy=True)

def channel_results_dict(chan, ipwFit, pinFit, pinPlot):
    '''A few checks so we can flag unusual channels
    '''
    ipwPars, pinPars = ipwFit.GetParameters(), pinFit.GetParameters()
    test_results = {}
    # For easy reference when reading csv file
    test_results["channel"] = chan
    ################
    # ipw stuff
    ################
    # Add parameters
    test_results["ipw_p0"] = ipwFit.GetParameter(0)
    test_results["ipw_p0_err"] = ipwFit.GetParError(0)
    test_results["ipw_p1"] = ipwFit.GetParameter(1)
    test_results["ipw_p1_err"] = ipwFit.GetParError(1)
    test_results["ipw_p2"] = ipwFit.GetParameter(2)
    test_results["ipw_p2_err"] = ipwFit.GetParError(2)
    # Check reducedChi2 is not too large - fit isn't great so set arbitraty = 15 limit.
    chi2 = ipwFit.GetChisquare() / ipwFit.GetNDF()
    test_results["ipwChi2"] = chi2
    # Check we can request 1000 photons - our bottom limit
    minimum_ipw = (-ipwPars[1])/(2*ipwPars[2])
    y_min = ipwPars[0] + ipwPars[1]*minimum_ipw + ipwPars[2]*(minimum_ipw*minimum_ipw)
    test_results["minPhotonSetting"] = y_min
    ################
    # pin stuff
    ################
    # Add parameters
    test_results["pin_p0"] = pinFit.GetParameter(0)
    test_results["pin_p0_err"] = pinFit.GetParError(0)
    test_results["pin_p1"] = pinFit.GetParameter(1)
    test_results["pin_p1_err"] = pinFit.GetParError(1)
    # Check PIN response linearity, again fit isn't ideal. Use redChi2 < 2.5
    pinChi2 = pinFit.GetChisquare() / pinFit.GetNDF()
    test_results["pinChi2"] = pinChi2
    # PIN saturation 
    xarr, yarr = get_xy(pinPlot)
    test_results["pinSaturation"] = yarr[np.where(xarr == max(xarr))[0][0]]
    # Get pin rms on smallest photon measure
    N=pinPlot.GetN()
    rms = pinPlot.GetErrorX(N-1)*np.sqrt(100) # Needs to be scaled back
    test_results["PINrms"] = rms
    # Maximum photon output for this channel
    test_results["maxPhotonOutput"] = max(yarr)
    return test_results


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-d", dest="direc", default="./")
    (options,args) = parser.parse_args()
    
    ROOT.gStyle.SetOptFit(1111) # Formatting for fit parameters
    ROOT.TGaxis.SetMaxDigits(4) # Axis formatting

    rootDirec = options.direc
    if not os.path.exists("%s/fits"%rootDirec):
        os.makedirs("%s/fits"%rootDirec)
    fout = ROOT.TFile("%s/fits/rootFiles.root"%rootDirec,"recreate")
    ipwCan = ROOT.TCanvas()
    pinCan = ROOT.TCanvas()
    ipwCan.SetCanvasSize(1000,400)
    pinCan.SetCanvasSize(1000,400)
    ipwCan.Divide(2,1)
    pinCan.Divide(2,1)
    
    # Loop over all data using standarised directory structure
    resultsList = []
    boxes = return_boxes("%s/broad_sweep/"%rootDirec)
    for box in boxes:
        broadFiles = return_files("%s/broad_sweep"%rootDirec, box)
        lowFiles = return_files("%s/low_intensity"%rootDirec, box)
        for j in range(len(lowFiles)):
            broadVals = check_data(plot_ipw.read_scope_scan(broadFiles[j]))
            lowVals = check_data(plot_ipw.read_scope_scan(lowFiles[j]))
            # Creat plots
            photonVsPIN_broad = ROOT.TGraphErrors()
            photonVsIPW_broad = ROOT.TGraphErrors()
            photonVsPIN_low = ROOT.TGraphErrors()
            photonVsIPW_low = ROOT.TGraphErrors()
            print len(broadVals), len(lowVals), broadFiles[j], lowFiles[j]
            for i in range(len(broadVals)):
                photonBroad = plot_ipw.get_photons(broadVals[i]["area"], 0.5)
                photonErrBroad = plot_ipw.get_photons(broadVals[i]["area_err"], 0.5)
                # Fill plots with data
                # Note: Data points are returned as mean and stdev(rms)
                #       for fitting, uncertainties should be given as standard error. 
                photonVsPIN_broad.SetPoint(i,broadVals[i]["pin"],photonBroad)
                #photonVsPIN_broad.SetPointError(i,broadVals[i]["pin_err"]/np.sqrt(1),photonErrBroad/np.sqrt(1))
                photonVsPIN_broad.SetPointError(i,0,photonErrBroad/np.sqrt(1))

                photonVsIPW_broad.SetPoint(i,broadVals[i]["ipw"],photonBroad)
                photonVsIPW_broad.SetPointError(i,0,photonErrBroad/np.sqrt(1))
                if i < len(lowVals):
                    photonLow = plot_ipw.get_photons(lowVals[i]["area"], 0.7)
                    photonErrLow = plot_ipw.get_photons(lowVals[i]["area_err"], 0.7)
                    photonVsPIN_low.SetPoint(i,lowVals[i]["pin"],photonLow)
                    #photonVsPIN_low.SetPointError(i,lowVals[i]["pin_err"]/np.sqrt(1),photonErrLow/np.sqrt(1))
                    photonVsPIN_low.SetPointError(i,0,photonErrLow/np.sqrt(1))

                    photonVsIPW_low.SetPoint(i,lowVals[i]["ipw"],photonLow)
                    photonVsIPW_low.SetPointError(i,0,photonErrLow/np.sqrt(1))
            # Add titles, labels and styling
            logical_channel = (int(lowFiles[j][-33:-31])-1)*8 + int(lowFiles[j][-26:-24])
            photonVsPIN_broad.SetName("Chan%02d_PIN_broad"%logical_channel)
            photonVsPIN_broad.GetXaxis().SetTitle("PIN reading (16 bit)")
            photonVsPIN_broad.GetYaxis().SetTitle("No. photons")
            photonVsIPW_broad.SetName("Chan%02d_IPW_broad"%logical_channel) 
            photonVsIPW_broad.GetXaxis().SetTitle("IPW (14 bit)")
            photonVsIPW_broad.GetYaxis().SetTitle("No. photons")
            photonVsPIN_low.SetName("Chan%02d_PIN_low"%logical_channel)
            photonVsPIN_low.GetXaxis().SetTitle("PIN reading (16 bit)")
            photonVsPIN_low.GetYaxis().SetTitle("No. photons")
            photonVsIPW_low.SetName("Chan%02d_IPW_low"%logical_channel)
            photonVsIPW_low.GetXaxis().SetTitle("IPW (14 bit)")
            photonVsIPW_low.GetYaxis().SetTitle("No. photons")
            plot_ipw.set_style(photonVsPIN_broad,1)
            plot_ipw.set_style(photonVsIPW_broad,1)
            plot_ipw.set_style(photonVsPIN_low,1)
            plot_ipw.set_style(photonVsIPW_low,1)
            # Draw
            pinCan.cd(1) 
            photonVsPIN_broad.Draw("ap")
            pinCan.cd(2)
            photonVsPIN_low.Draw("ap")
            ipwCan.cd(1)
            photonVsIPW_broad.Draw("ap")
            ipwCan.cd(2)
            photonVsIPW_low.Draw("ap")
            # Fits
            ipwFit, photonVsIPW_low, ipwCan = fit_ipw(photonVsIPW_low,ipwCan)
            pinFit, photonVsPIN_low, pinCan = fit_pin(photonVsPIN_low,pinCan)
            ipwCan.Update(); pinCan.Update()
            # Results
            chan = int(lowFiles[j][-25]) + (box-1)*8
            chanResDict = channel_results_dict(chan, ipwFit, pinFit, photonVsPIN_broad)
            resultsList.append(chanResDict)
            # Save
            pdf_dir = "%s/fits/pdfs"%rootDirec
            if not os.path.exists(pdf_dir):
                os.makedirs(pdf_dir)
            pinCan.Print("%s/Chan%02d_PIN.pdf"%(pdf_dir,logical_channel))
            ipwCan.Print("%s/Chan%02d_IPW.pdf"%(pdf_dir,logical_channel))
            photonVsPIN_broad.Write()
            photonVsPIN_low.Write()
            photonVsIPW_broad.Write()
            photonVsIPW_low.Write()
            #print 'Only the first plot for now...'
            #break
        #break
    # Save results list to file
    with open('%s/resultsOverview.csv'%rootDirec, 'wb') as f:
        w = csv.DictWriter(f, resultsList[0].keys())
        w.writeheader()
        w.writerows(resultsList)
