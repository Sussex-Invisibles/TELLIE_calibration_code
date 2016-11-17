import os
import plot_ipw
import numpy as np
import matplotlib.pyplot as plt
from time import gmtime, strftime

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
        self.PhotonCounts = []
        self.TimingOffsets = []

    
    def find_dat_files(self,overallChannelNum):
        boxNum, chanNum = get_box_and_channel_num(overallChannelNum)
#First find broad sweep file
        broadFile = ("./broad_sweep")
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
        lowFile = ("./low_intensity")
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

    
    def create_channel_summary(self,overallChannelNum):
#Add channel to data structure
        self.channels.append(overallChannelNum)
        
#create arrays to store IPW, photon PIN and timing
        ipws = []
        photons = []
        PINS = []
        times = []

#Obtain Dat files
        broadFile, lowFile = self.find_dat_files(overallChannelNum)
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
                photons.append(plot_ipw.get_photons(dataBroad[i]["area"],0.5))
                times.append(dataBroad[i]["time"])
        #Otherwise write out broad sweep dat upto the IPW before the low sweep starts
        else:
            i = 0
            while(dataBroad[i]["ipw"] <= lowStartIPW):
                ipws.append(dataBroad[i]["ipw"]) 
                PINS.append(dataBroad[i]["pin"]) 
                photons.append(plot_ipw.get_photons(dataBroad[i]["area"],0.5))
                times.append(dataBroad[i]["time"])
                i = i+1
#Now print out low intensity data until area or timing goes to 0
        for i in range(len(dataLow)):
            if dataLow[i]["area"] == 0:
                break
            if dataLow[i]["time"] == 0:
                break
            ipws.append(dataLow[i]["ipw"]) 
            PINS.append(dataLow[i]["pin"]) 
            photons.append(plot_ipw.get_photons(dataLow[i]["area"],0.7))
            times.append(dataLow[i]["time"])
#Find closest point to 1000 photons and use this to set the timing
        closestPhoton = 1e6 
        closestPhotonIndex = 1000 
        for i, photon in enumerate(photons):
            if np.fabs(photon-1000) < np.fabs(closestPhoton-1000):
                closestPhoton = photon
                closestIndex = i

                 
#Now append data to class arrays
        self.IPWS.append(ipws)
        self.PINReadings.append(PINS)
        self.PhotonCounts.append(photons)
        self.TimingOffsets.append(times[closestIndex])


    def write_calibration_file(self,filename):
        with open(filename,"w") as outfile:
           #Write header
           outfile.write("#TELLIE Calibration file created on "+strftime("%Y-%m-%d %H:%M:%S", gmtime())+"\n")
#Now iterate through channels and write out calibration data
           for i in range(len(self.channels)):
               outfile.write("{\n")
               outfile.write("channel: %d,\n" % self.channels[i])
               outfile.write("timing_offset: %.14f,\n" % self.TimingOffsets[i])
               outfile.write("ipw: "+str(self.IPWS[i])+",\n")
               outfile.write("pin: "+str(self.PINReadings[i])+",\n")
               outfile.write("photon_counts: "+str(self.PhotonCounts[i])+",\n")
               outfile.write("}\n")




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
        self.create_channel_summary(9)
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
    test = summaryFile()
    #test.unit_tests()
    for chan in range(1,96):
        print "Adding channel %d " % chan
        test.create_channel_summary(chan)
        test.write_calibration_file("testSlave.dat")


