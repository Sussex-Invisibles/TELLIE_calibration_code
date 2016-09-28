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
pmt_channel = 4

#Copied from sweep, cant import sweep as it messes with the TELLIE calibration scripts when they are running and causes them to crash
def find_pulse_2(x, y, step_back = 100, step_forward = 100):
    """Method to find the pulse by looking for the minima of the trace"""
    meany = np.mean(y,axis=0)
    minIndex = np.argmin(meany)
    return x[minIndex-step_back:minIndex+step_forward], y[:,minIndex-step_back:minIndex+step_forward]

#Calculate the entry from
def calcEntryFromPklFile(fname):
    # Calc and return params
    x1,y1 = calc.readPickleChannel(fname, trig_channel,[trig_channel,pmt_channel])
    x2,y2 = calc.readPickleChannel(fname, pmt_channel,[trig_channel,pmt_channel])
    x2,y2 = find_pulse_2(x2,y2)
    # Make sure we see a signal well above noise
    snr = calc.calcSNR(x2, y2)
    print "SNR: ", snr
    if snr > 7:
	# Calculate results
	results = calc.dictionary_of_params(x2,y2)
	mean, std, sterr = calc.calcJitter(x2, y2, x1, y1, threshold=0.4)
	results["time"] = mean
	results["time error"] = std
    else:
	# No signal observerd, return zero
	results = return_zero_result()
	results['pin'] = pin
	results['pin error'] = rms
    return results




def runChannel(box_dir,channel_num):
    timestamp = time.strftime("%y%m%d_%H.%M",time.gmtime())
    boxNum = int(box_dir[-2:])
    overall_channel_num = (boxNum-1)*8+channel_num
    directory = "%s/raw_data/Channel_%02d/" % (box_dir,overall_channel_num)
    files = os.listdir(directory)
    output_filename="./should_not_get_here"
    pin = None
    pin_error = None
    results = None
    #Read in the old dat file for PIN readings
    oldDats = make_all_plots.createLatestDatFileArray(os.listdir(box_dir)) 
    correspondingOldDat = None
    for oldDat in oldDats:
	    if "Chan%02d" % (channel_num) in oldDat:
		results = plot_ipw.read_scope_scan(os.path.join(box_dir,oldDat))
                correspondingOldDat = oldDat
    if "broad_sweep" in box_dir:
    	output_filename = "%s/Chan%02d_IPWbroad_%s.dat" % (box_dir,channel_num,timestamp)
    if "low_intensity" in box_dir:
    	output_filename = "%s/%s_CORRECTED.dat" % (box_dir,correspondingOldDat[:-4])
    output_file = file(output_filename,'w')
    output_file.write("#PWIDTH\tPWIDTH Error\tPIN\tPIN Error\tWIDTH\tWIDTH Error\tRISE\tRISE Error\tFALL\tFALL Error\tAREA\tAREA Error\tMinimum\tMinimum Error\tTime\tTime Error\n")
    for pkl in files:
        ipw = int(pkl[5:-4])
        for i in range(len(results)):
            if ipw == int(results[i]["ipw"]):
                pin = results[i]["pin"]
                pin_error = results[i]["pin_err"]
               
        #Some pkl files are from old sweeps with smaller stepsize so they havent been overwritten, if we enounter one we should skip it
        if pin == None:
       	    print "Cant find PIN value for IPW: "+str(ipw)
            continue
        tmpResults = calcEntryFromPklFile(os.path.join(directory,pkl))
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
    

if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-d", dest="boxDir")
    parser.add_option("-c", dest="channel")
    (options,args) = parser.parse_args()
    runChannel(options.boxDir,int(options.channel))



