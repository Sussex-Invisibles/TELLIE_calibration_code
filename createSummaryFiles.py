import os
import plot_ipw
import numpy as np
import matplotlib.pyplot as plt
from time import gmtime, strftime
import json
from matplotlib.ticker import ScalarFormatter, FormatStrFormatter
import optparse

def get_box_and_channel_num(overallChannelNum):
    chanNum = overallChannelNum % 8
    if chanNum == 0:
        chanNum = 8
    boxNum = ((overallChannelNum - chanNum)/8)+1
    return boxNum, chanNum


class summaryFile:
   
    def __init__(self):
        self.channels = []
        self.IPWS = []
        self.PINReadings = []
        self.PINErrors = []
        self.PhotonCounts = []
        self.PhotonErrors = []
        self.TimingOffsets = []

    
    def find_dat_files(self,overallChannelNum,topDir="."):
        boxNum, chanNum = get_box_and_channel_num(overallChannelNum)
#First find broad sweep file
        broadFile = os.path.join(topDir,"broad_sweep")
#Searching for Box directory first
        for fil in os.listdir(broadFile):
            if "Box_%02d" % boxNum in fil:
                broadFile = os.path.join(broadFile,fil)
                break
#Now searching for channel file
        for fil in os.listdir(broadFile):
            if "Chan%02d" % chanNum in fil and "CORRECTED" in fil:
                broadFile = os.path.join(broadFile,fil)
                break
        
    #Now doing the same for the low intensity file
#First find broad sweep file
        lowFile = os.path.join(topDir,"low_intensity")
#Searching for Box directory first
        for fil in os.listdir(lowFile):
            if "Box_%02d" % boxNum in fil:
                lowFile = os.path.join(lowFile,fil)
                break
#Now searching for channel file
        for fil in os.listdir(lowFile):
            if "Chan%02d" % chanNum in fil and "CORRECTED" in fil:
                lowFile = os.path.join(lowFile,fil)
                break
        
        return broadFile, lowFile
    #Now doing the same for the low intensity file

    
    def create_channel_summary(self,overallChannelNum,topDir=".",masterMode=False):
#Add channel to data structure
        self.channels.append(overallChannelNum)
        
#create arrays to store IPW, photon PIN and timing
        ipws = []
        photons = []
        photonError = []
        PINS = []
        PINError = []
        times = []


#Obtain Dat files
        broadFile, lowFile = self.find_dat_files(overallChannelNum,topDir)
        print "Reading Files: "+str(lowFile)+"     "+str(broadFile)
#Read in dat files using plot ipw script and clean the data of any nans
        dataBroad = plot_ipw.read_scope_scan(broadFile)
        dataBroad= plot_ipw.clean_data(dataBroad)
        dataLow = plot_ipw.read_scope_scan(lowFile)
        dataLow = plot_ipw.clean_data(dataLow)
#Sort data based on increasing IPW
        dataLow.sort(key=lambda x: int(x["ipw"]))
        dataBroad.sort(key=lambda x: int(x["ipw"]))
#Compare start point of low sweep with point where broad sweep stops
        broadStopIndex = 0
#Check where photon/timing is set to 0
        for i in range(len(dataBroad)):
            if dataBroad[i]["area"] == 0:
                broadStopIndex = i
                break
            if not masterMode:
                if dataBroad[i]["time"] == 0:
                    broadStopIndex = i
                    break
            broadStopIndex = i
         
        broadStopIPW = dataBroad[broadStopIndex]["ipw"]
#Look at first point of low sweep 
        lowStartIPW = dataLow[0]["ipw"]
#If gap between broad sweep and low sweep print message and add all broad sweep data to arrays

        if lowStartIPW > broadStopIPW:
            print "There is a gap between the low and broad sweeps for channel "+str(overallChannelNum)+" broad stop IPW: "+str(broadStopIPW)+ " low start IPW: "+str(lowStartIPW)
            for i in range(0,broadStopIndex):
                ipws.append(dataBroad[i]["ipw"]) 
                PINS.append(dataBroad[i]["pin"]) 
                PINError.append(dataBroad[i]["pin_err"])
                photons.append(plot_ipw.get_photons(dataBroad[i]["area"],0.5))
                photonError.append(plot_ipw.get_photons(dataBroad[i]["area_err"],0.5))
                times.append(dataBroad[i]["time"])
        #Otherwise write out broad sweep dat upto the IPW before the low sweep starts
        else:
            i = 0
            while(dataBroad[i]["ipw"] <= lowStartIPW):
                ipws.append(dataBroad[i]["ipw"]) 
                PINS.append(dataBroad[i]["pin"]) 
                PINError.append(dataBroad[i]["pin_err"])
                photons.append(plot_ipw.get_photons(dataBroad[i]["area"],0.5))
                photonError.append(plot_ipw.get_photons(dataBroad[i]["area_err"],0.5))
                times.append(dataBroad[i]["time"])
                i = i+1
#Now print out low intensity data until area or timing goes to 0
        for i in range(len(dataLow)):
            if dataLow[i]["area"] == 0:
                break
            if not masterMode:
                if dataLow[i]["time"] == 0:
                    break
            ipws.append(dataLow[i]["ipw"]) 
            PINS.append(dataLow[i]["pin"]) 
            PINError.append(dataLow[i]["pin_err"])
            photons.append(plot_ipw.get_photons(dataLow[i]["area"],0.7))
            photonError.append(plot_ipw.get_photons(dataLow[i]["area_err"],0.7))
            times.append(dataLow[i]["time"])
#Find closest point to 1000 photons and use this to set the timing
        closestPhoton = 1e6 
        closestIndex = 1000 
        for i, photon in enumerate(photons):
            if np.fabs(photon-1000) < np.fabs(closestPhoton-1000):
                closestPhoton = photon
                closestIndex = i

                 
#Now append data to class arrays
        self.IPWS.append(ipws)
        self.PINReadings.append(PINS)
        self.PINErrors.append(PINError)
        self.PhotonCounts.append(photons)
        self.PhotonErrors.append(photonError)
        try:
            self.TimingOffsets.append(times[closestIndex])
        except IndexError:
            self.TimingOffsets.append(0)



    def write_calibration_file(self,filename):
        with open(filename,"w") as outfile:
            #Create output dictionary
            for i in range(len(self.channels)):
                outDict = {}
                outDict["index"] = i
                outDict["timestamp"] = strftime("%y-%m-%d %h:%m:%s", gmtime())
                outDict["channel"] = self.channels[i]
                outDict["ipws"] = self.IPWS[i]
                outDict["pins"] = self.PINReadings[i]
                outDict["pin_errors"] = self.PINErrors[i]
                outDict["photon_counts"] = self.PhotonCounts[i]
                outDict["photon_count_errors"] = self.PhotonErrors[i]
                outDict["timing_offset"] = self.TimingOffsets[i]
                json.dump(outDict,outfile)




    def unit_tests(self):
        box7, chan7 = get_box_and_channel_num(7)
        print "Channel "+str(7)+" is in box "+str(box7)+" with channel "+str(chan7)
        box65, chan65 = get_box_and_channel_num(65)
        print "Channel "+str(65)+" is in box "+str(box65)+" with channel "+str(chan65)
        box92, chan92 = get_box_and_channel_num(92)
        print "Channel "+str(92)+" is in box "+str(box92)+" with channel "+str(chan92)
        print "Dat files for channel 7 are: "
        print self.find_dat_files(7)
        print "Dat files for channel 65  are: "
        print self.find_dat_files(65)
        print "Dat files for channel 92 are: "
        print self.find_dat_files(92)
        print "Creating channel summary for channel 7"
        self.create_channel_summary(40)
        plt.figure(1)
        plt.title("Photon vs IPW for channel"+str(self.channels[0]))
        plt.xlabel("IPW")
        plt.ylabel("Photon Count")
        plt.plot(self.IPWS[0],self.PhotonCounts[0],"bo")
        plt.figure(2)
        plt.title("Photon vs PIN for channel"+str(self.channels[0]))
        plt.xlabel("PIN Readings")
        plt.ylabel("Photon Counts")
        plt.plot(self.PINReadings[0],self.PhotonCounts[0],"bo")
        plt.figure(4) 
        plt.title("PIN vs IPW for channel"+str(self.channels[0]))
        plt.xlabel("IPW")
        plt.ylabel("PIN")
        plt.plot(self.IPWS[0],self.PINReadings[0],"bo")
        plt.show()



        


if __name__=="__main__":
    testSlave = summaryFile()
    testMaster = summaryFile()
    parser = optparse.OptionParser()
    parser.add_option("-m",help="Top directory for master dat files",dest="masterDir")
    parser.add_option("-s",help="Top directory for slave dat files",dest="slaveDir")
    (options, args) = parser.parse_args()

    #test.unit_tests()
    for chan in range(1,96):
        print "Adding channel %d " % chan
        testSlave.create_channel_summary(chan,topDir=options.slaveDir)
        testMaster.create_channel_summary(chan,topDir=options.masterDir,masterMode=True)
        plt.figure(chan)
        plt.plot(testMaster.IPWS[-1],testMaster.PhotonCounts[-1],"bo")
        plt.show()
    
    testMaster.TimingOffsets = testSlave.TimingOffsets
    testSlave.write_calibration_file("testSlave.dat")
    testMaster.write_calibration_file("testMaster.dat")
    
    
    '''f, (ax1, ax2) = plt.subplots(2, sharex=True)
    ax1.set_ylabel("Photon Count")
    print "CHANNEL NUM: "+str(test.channels[12])
    ax1.errorbar(test.IPWS[12],np.multiply(test.PhotonCounts[12],1.0/1e6),yerr=np.multiply(test.PhotonErrors[12],10./1e6),fmt="bo")
    ax2.set_ylabel("PIN Reading")
    ax2.errorbar(test.IPWS[12],np.divide(test.PINReadings[12],1e3),yerr=np.multiply(test.PINErrors[12],10./1e3),fmt="bo")
    ax1.set_ylim(0,1.2) 
    ax2.set_ylim(0.5,70)
    ax1.get_yaxis().set_major_formatter(FormatStrFormatter('%.1f M'))
    ax2.get_yaxis().set_major_formatter(FormatStrFormatter('%.0f k'))
    plt.xlabel("IPW")
    f.subplots_adjust(hspace=0.06)
    plt.setp([a.get_xticklabels() for a in f.axes[:-1]], visible=False)
    plt.show()'''


