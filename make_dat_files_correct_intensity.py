#Same as make_dat files, simply has some additional functionality to remove the large jumps in IPW
import time
import calc_utils as calc
import os
import make_all_plots
import plot_ipw
import optparse
import numpy as np

trig_channel = 1
#Channels 23 and after have the PMT plugged into channel 4 of the scope
#pmt_channel = 2
#pmt_channel = 4

#Copied from sweep, cant import sweep as it messes with the TELLIE calibration scripts when they are running and causes them to crash
def find_pulse_2(x, y, step_back = 100, step_forward = 100):
    """Method to find the pulse by looking for the minima of the trace"""
    meany = np.mean(y,axis=0)
    minIndex = np.argmin(meany)
    return x[minIndex-step_back:minIndex+step_forward], y[:,minIndex-step_back:minIndex+step_forward]

def find_pulse_3(x,y, noise_factor=1.5, step_back=5, step_forward=5):
    """Method to find the pulse by looking for the minima of the trace"""
    meany = np.mean(y,axis=0)
    minIndex = np.argmin(meany)
    #Look at noise by examining trace 40ns before PMT pulse
    noiseIndex = minIndex-100
    maxNoise = np.amax(np.fabs(y[:,:noiseIndex]))
    lowerIndex = 0
    upperIndex = 0
    #Find lower limit
    for ind in range(minIndex,-1,-1):
        if np.fabs(meany[ind]) < noise_factor*maxNoise:
           lowerIndex = ind-step_back
           break
    
    for ind in range(minIndex,len(meany)):
        if np.fabs(meany[ind]) < noise_factor*maxNoise:
           upperIndex = ind+step_forward
           break
	
    return x[lowerIndex:upperIndex], y[:,lowerIndex:upperIndex]

def return_zero_result():
    r = {}
    r['pin'], r['pin error'] = 0, 0
    r['width'], r['width error'] = 0, 0
    r['rise'], r['rise error'] = 0, 0
    r['fall'], r['fall error'] = 0, 0
    r['area'], r['area error'] = 0, 0
    r['peak'], r['peak error'] = 0, 0
    r['time'], r['time error'] = 0, 0
    return r

tolerance = 0.2
#Calculate the entry from
def calcEntryFromPklFile(fname,pmt_channel,scaleFactor):
    # Calc and return params
    x1,y1 = calc.readPickleChannel(fname, trig_channel,[trig_channel,pmt_channel])
    x2,y2 = calc.readPickleChannel(fname, pmt_channel,[trig_channel,pmt_channel])
    y2 = y2*scaleFactor
    #x2Cut,y2Cut  = find_pulse_3(x2,y2,step_forward=40)
    mean, std, sterr = calc.calcJitterNew2(x1, y1, x2, y2)
    # Make sure we see a signal well above noise
    snr = calc.calcSNR(x2, y2)
    print "SNR: ", snr
    if snr > 7:
	# Calculate results
	results = calc.dictionary_of_params(x2,y2)
	#mean, std, sterr = calc.calcJitter(x2Cut, y2Cut, x1, y1, threshold=0.4)
	mean, std, sterr = calc.calcJitterNew2(x1, y1, x2, y2)
	results["time"] = mean
	results["time error"] = std
    else:
	# No signal observerd, return zero
	results = return_zero_result()
    return results

def calcEntryFromPklFileMasterMode(fname,pmt_channel,ipw):
    # Calc and return params
    #x1,y1 = calc.readPickleChannel(fname, trig_channel,[trig_channel,pmt_channel])
    x2,y2 = calc.readPickleChannel(fname, pmt_channel,[pmt_channel])
    #x2Cut,y2Cut  = find_pulse_3(x2,y2,step_forward=35)
    # Make sure we see a signal well above noise
    snr = calc.calcSNR(x2, y2)
    print "SNR: ", snr
    if snr > 1.5:
	# Calculate results
	results = calc.dictionary_of_params_master(x2,y2)
	#mean, std, stderr = calc.calcJitterNew2(x1, y1, x2, y2)
	results["time"] = 0
	results["time error"] = 0
    else:
	# No signal observerd, return zero
	results = return_zero_result() 
    return results

scaleRatios = [10.0,5.0,2.5,2.0]

def runChannel(box_dir,channel_num,master_mode=False):
    timestamp = time.strftime("%y%m%d_%H.%M",time.gmtime())
    boxNum = int(box_dir[-2:])
    overall_channel_num = (boxNum-1)*8+channel_num
    directory = "%s/raw_data/Channel_%02d/" % (box_dir,overall_channel_num)
    pmt_channel = -1
    if overall_channel_num >= 23 or overall_channel_num == 4:
        pmt_channel = 4
    else:
        pmt_channel = 2
    files = []
    try: 
        files = os.listdir(directory)
    except OSError:
        print "Could not find folder: "+directory
        return 1
    output_filename="./should_not_get_here"
    pin = None
    pin_error = None
    results = None
    #Read in the old dat file for PIN readings
    datFiles = os.listdir(box_dir)
    datFiles.sort(key=lambda x: os.path.getmtime(os.path.join(box_dir,x)))
    oldDats = make_all_plots.createLatestDatFileArray(datFiles) 
    correspondingOldDat = None
    for oldDat in oldDats:
	    if "Chan%02d" % (channel_num) in oldDat:
                if master_mode:
                    results = plot_ipw.read_scope_scan_master(os.path.join(box_dir,oldDat))
                else:
                    results = plot_ipw.read_scope_scan(os.path.join(box_dir,oldDat))
                correspondingOldDat = oldDat
                print "Using dat file for PIN readings: "+correspondingOldDat
                break
    if "broad_sweep" in box_dir:
        output_filename = "%s/%s_CORRECTED.dat" % (box_dir,correspondingOldDat[:-4])
    if "low_intensity" in box_dir:
    	output_filename = "%s/%s_CORRECTED.dat" % (box_dir,correspondingOldDat[:-4])
    output_file = file(output_filename,'w')
    output_file.write("#PWIDTH\tPWIDTH Error\tPIN\tPIN Error\tWIDTH\tWIDTH Error\tRISE\tRISE Error\tFALL\tFALL Error\tAREA\tAREA Error\tMinimum\tMinimum Error\tTime\tTime Error\n")
    for iFil, fil in enumerate(files):
        if not fil.endswith(".pkl"):
            files.pop(iFil)
    files.sort(key=lambda x: int(x[5:-4]))
    for iPkl,pkl in enumerate(files):
        ipw = int(pkl[5:-4])
        for i in range(len(results)):
            if ipw == int(results[i]["ipw"]):
                pin = results[i]["pin"]
                pin_error = results[i]["pin_err"]
               
        #Some pkl files are from old sweeps with smaller stepsize so they havent been overwritten, if we enounter one we should skip it
        if pin == None:
       	    print "Cant find PIN value for IPW: "+str(ipw)
            continue
        if master_mode:
            pmt_channel = 1
            tmpResults = calcEntryFromPklFileMasterMode(os.path.join(directory,pkl),pmt_channel,ipw)
        else:
            tmpResults = calcEntryFromPklFile(os.path.join(directory,pkl),pmt_channel,ipw)
        
        #First reading can only use value after to scale
        if iPkl == 0:
            if master_mode:
                pmt_channel = 1
                tmpResultsNext = calcEntryFromPklFileMasterMode(os.path.join(directory,files[1]),pmt_channel,ipw)
            else:
                tmpResultsNext = calcEntryFromPklFile(os.path.join(directory,files[1]),pmt_channel,1.0)
            peakRatio = tmpResults["peak"]/tmpResultsNext["peak"]
            for scaleRatio in scaleRatios:
                if np.abs(peakRatio-scaleRatio)/scaleRatio < 0.1:
                    print "Scaling IPW: "+str(ipw)+" by: "+str(1.0/scaleRatio)
                    tmpResults = calcEntryFromPklFile(os.path.join(directory,pkl),pmt_channel,1.0/scaleRatio)
        
        #Last reading can only use previous value
        elif iPkl == len(files)-1:
            if master_mode:
                pmt_channel = 1
                tmpResultsPrev = calcEntryFromPklFileMasterMode(os.path.join(directory,files[iPkl]),pmt_channel,ipw)
            else:
                tmpResultsPrev = calcEntryFromPklFile(os.path.join(directory,files[iPkl]),pmt_channel,1.0)
            peakRatio = tmpResults["peak"]/tmpResultsPrev["peak"]
            for scaleRatio in scaleRatios:
                if np.abs(peakRatio-scaleRatio)/scaleRatio < 0.1:
                    print "Scaling IPW: "+str(ipw)+" by: "+str(1.0/scaleRatio)
                    tmpResults = calcEntryFromPklFile(os.path.join(directory,pkl),pmt_channel,1.0/scaleRatio)
        
        #Otherwise we can use both sides to estimate a midpoint then round using this
        else:
            if master_mode:
                pmt_channel = 1
                tmpResultsNext = calcEntryFromPklFileMasterMode(os.path.join(directory,files[iPkl+1]),pmt_channel,ipw)
                tmpResultsPrev = calcEntryFromPklFileMasterMode(os.path.join(directory,files[iPkl-1]),pmt_channel,ipw)
            else:
                tmpResultsNext = calcEntryFromPklFile(os.path.join(directory,files[iPkl+1]),pmt_channel,1.0)
                tmpResultsPrev = calcEntryFromPklFile(os.path.join(directory,files[iPkl-1]),pmt_channel,1.0)
            midPointPeak = 0.5*(tmpResultsNext["peak"]+tmpResultsPrev["peak"])
            peakRatio = tmpResults["peak"]/midPointPeak
            for scaleRatio in scaleRatios:
                if np.abs(peakRatio-scaleRatio)/scaleRatio < 0.1:
                    print "Scaling IPW: "+str(ipw)+" by: "+str(1.0/scaleRatio)
                    tmpResults = calcEntryFromPklFile(os.path.join(directory,pkl),pmt_channel,1.0/scaleRatio)
	
        output_file.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n"%(ipw, 0,
                                            pin, pin_error,
                                            tmpResults["width"], tmpResults["width error"],
                                            tmpResults["rise"], tmpResults["rise error"],
                                            tmpResults["fall"], tmpResults["fall error"],
                                            tmpResults["area"], tmpResults["area error"],
                                            tmpResults["peak"], tmpResults["peak error"],
                                            tmpResults["time"], tmpResults["time error"]))
        pin = None
        pin_error = None
    output_file.close()

def runThroughSweep(mainDir):
    folds = os.listdir(mainDir)
    channels = range(1,9)
    boxDirs = []
    for fold in folds:
        if "Box_" in fold:
            boxDirs.append(fold)

    for box in boxDirs:
        boxDir = os.path.join(mainDir,box) 
        for chan in channels:
            runChannel(boxDir,chan)

if __name__=="__main__":

    parser = optparse.OptionParser()
    parser.add_option("-b", dest="boxdir")
    parser.add_option("-c", dest="chan")
    (options,args) = parser.parse_args()
    #runThroughSweep("./broad_sweep")
    runChannel(options.boxdir,int(options.chan),master_mode=True)



