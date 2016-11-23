import time
import calc_utils as calc
import os
import make_all_plots
import plot_ipw
import optparse
import numpy as np
import matplotlib.pyplot as plt

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

#Calculate the entry from
def calcEntryFromPklFile(fname,pmt_channel,ipw):
    # Calc and return params
    x1,y1 = calc.readPickleChannel(fname, trig_channel,[trig_channel,pmt_channel])
    x2,y2 = calc.readPickleChannel(fname, pmt_channel,[trig_channel,pmt_channel])
    #x2Cut,y2Cut  = find_pulse_3(x2,y2,step_forward=35)
    # Make sure we see a signal well above noise
    snr = calc.calcSNR(x2, y2)
    print "SNR: ", snr
    if snr > 7:
	# Calculate results
	results = calc.dictionary_of_params(x2,y2)
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

def runChannel(box_dir,channel_num,master_mode=False):
    timestamp = time.strftime("%y%m%d_%H.%M",time.gmtime())
    boxNum = int(box_dir[-2:])
    overall_channel_num = (boxNum-1)*8+channel_num
    directory = "%s/raw_data/Channel_%02d/" % (box_dir,overall_channel_num)
    pmt_channel = -1
    if overall_channel_num >= 24:
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
                print "Using dat file for PIN readings: "+os.path.join(box_dir,correspondingOldDat)
                break
    if "broad_sweep" in box_dir:
        output_filename = "%s/%s_CORRECTED.dat" % (box_dir,correspondingOldDat[:-4])
    if "low_intensity" in box_dir:
    	output_filename = "%s/%s_CORRECTED.dat" % (box_dir,correspondingOldDat[:-4])
    output_file = file(output_filename,'w')
    output_file.write("#PWIDTH\tPWIDTH Error\tPIN\tPIN Error\tWIDTH\tWIDTH Error\tRISE\tRISE Error\tFALL\tFALL Error\tAREA\tAREA Error\tMinimum\tMinimum Error\tTime\tTime Error\n")
    for pkl in files:
        if not pkl.endswith(".pkl"):
            continue
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
            if "Box_01" in fold:
                continue
            boxDirs.append(fold)

    for box in boxDirs:
        boxDir = os.path.join(mainDir,box) 
        if "Box_02" in boxDir:
            print "Skipping first 5 channels of box 2"
            channels = range(6,9)
        for chan in channels:
            runChannel(boxDir,chan)
        channels = range(1,9)

if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-b", dest="boxdir")
    parser.add_option("-c", dest="chan")
    (options,args) = parser.parse_args()
    #runThroughSweep("./broad_sweep")
    runChannel(options.boxdir,int(options.chan),master_mode=True)



