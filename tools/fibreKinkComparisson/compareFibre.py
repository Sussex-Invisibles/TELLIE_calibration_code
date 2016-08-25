import sys
import os
import csv
import numpy as np
import ROOT
import matplotlib.pyplot as plt
import glob
import plot_ipw


def createDictionaryFromFile(inFile):
    outDict = {}
    outDict["ipw"] = []
    outDict["PIN"] = []
    outDict["PIN_error"] = []
    outDict["area"] = []
    outDict["area_error"] = []
    
    inputFile = open(inFile,"rb")
    csvIn = csv.reader(inputFile,delimiter="	")
    firstRow = 1
    for row in csvIn:
      if firstRow == 1:
         firstRow = 0
         continue
      outDict["ipw"].append(int(row[0]))
      outDict["PIN"].append(float(row[2]))
      outDict["PIN_error"].append(float(row[3]))
      outDict["area"].append(float(row[10]))
      outDict["area_error"].append(float(row[11]))
    return outDict
    
      
#Return index of array where first element is 0
def returnFirstZeroIndex(array1, array2):
    for i in range(len(array1)):
        if array1[i] == 0 or array2[i] == 0:
           return i
    return len(array1)

#Return index of array where first element is less than value 
def returnFirstLessThanValueIndex(array1, array2, value):
    for i in range(len(array1)):
        if array1[i] <  value or array2[i] < value:
           return i
    return len(array1)

def getDateAndChannel(inFile):
    splitPath = os.path.split(inFile)
    channelName = splitPath[0]
    date = splitPath[1][-16:-10]
    return channelName, date

def fitPhotonPINCompare(PINValues,PINErrors,PhotonValues,PhotonErrors,channel,dates,figureNumber):
    weights1 = [1.0/((PINErrors[0][i]**2)+(PhotonErrors[0][i]**2)) for i in range(len(PINErrors[0]))]
    weights2 = [1.0/((PINErrors[1][i]**2)+(PhotonErrors[1][i]**2)) for i in range(len(PINErrors[1]))]
    fitResult1 = np.polyfit(PINValues[0],PhotonValues[0],1,w=weights1)
    fitResult2 = np.polyfit(PINValues[1],PhotonValues[1],1,w=weights2)
    fitPoly1 = np.poly1d(fitResult1)
    fitPoly2 = np.poly1d(fitResult2)
    chi_sq_1 = np.sum(((np.polyval(fitPoly1,PINValues[0])-PhotonValues[0])**2)*weights1)
    chi_sq_2 = np.sum(((np.polyval(fitPoly2,PINValues[1])-PhotonValues[1])**2)*weights2)
    reduced_chi_sq_1 = chi_sq_1/(len(PINValues[0])-len(fitResult1))
    reduced_chi_sq_2 = chi_sq_2/(len(PINValues[1])-len(fitResult2))
    fig = plt.figure(figureNumber)
    plt.xlabel("PIN Reading")
    plt.ylabel("Photon Count")
    plt.title("Photon count vs PIN reading for channel: "+channel+" and fits")
    plt.errorbar(PINValues[0],PhotonValues[0],xerr=PINErrors[0],yerr=PhotonErrors[0],label=channel+" "+dates[0])
    plt.errorbar(PINValues[1],PhotonValues[1],xerr=PINErrors[1],yerr=PhotonErrors[1],label=channel+" "+dates[1])
    plt.plot(PINValues[0],np.polyval(fitPoly1,PINValues[0]),label="Fit to "+channel+" "+dates[0]+" reduced chi squared is: "+str(reduced_chi_sq_1))
    plt.plot(PINValues[1],np.polyval(fitPoly2,PINValues[1]),label="Fit to "+channel+" "+dates[1]+" reduced chi squared is: "+str(reduced_chi_sq_2))
    plt.legend(loc="upper left")
    fig.show()
    return fitResult1[0]/fitResult2[0]
    

plt.figure(1)
directoryArray =["channel_5", "channel_6", "channel_7", "channel_8", "channel_85", "channel_86", "channel_87", "channel_88"] 
numPlots = len(directoryArray)
colormap = plt.cm.gist_ncar
plt.gca().set_color_cycle([colormap(i) for i in np.linspace(0,0.9,numPlots)])
iterNum = 3
channelDate = []
ratios = []
for directory in directoryArray:
	
	PINValues = []
        PhotonValues = []
	PINErrors = []
        PhotonErrors = []

	lowFiles = glob.glob(directory+"/*.dat")
	dict1 = createDictionaryFromFile(lowFiles[0])
	channel, date1 = getDateAndChannel(lowFiles[0])
	dict2 = createDictionaryFromFile(lowFiles[1])
	channel, date2 = getDateAndChannel(lowFiles[1])
	#max_index = returnFirstZeroIndex(dict1["area"],dict2["area"])
        PhotonValues.append([plot_ipw.get_photons(x,0.7) for x in dict1["area"]])
        PhotonValues.append([plot_ipw.get_photons(x,0.7) for x in dict2["area"]])
	max_index = returnFirstLessThanValueIndex(PhotonValues[0],PhotonValues[1],10000)
        del PhotonValues[:]
        PhotonValues.append([plot_ipw.get_photons(x,0.7) for x in dict1["area"][:max_index]])
        PhotonValues.append([plot_ipw.get_photons(x,0.7) for x in dict2["area"][:max_index]])
	relative_photon_error_1 = np.divide(dict1["area_error"][:max_index],dict1["area"][:max_index])
	relative_photon_error_2 = np.divide(dict2["area_error"][:max_index],dict2["area"][:max_index])
	relative_ratio_error = np.sqrt(np.power(relative_photon_error_1,2)+np.power(relative_photon_error_2,2))
	ratio_photon = (np.divide(dict1["area"][:max_index],dict2["area"][:max_index]))
	mean_ratio_photon = np.mean(ratio_photon)
	print "The ratio of photon count between "+str(lowFiles[0])+" and "+str(lowFiles[1])+" is "+str(mean_ratio_photon)
	plt.errorbar(dict1["ipw"][:max_index],ratio_photon,yerr=np.multiply(ratio_photon,relative_ratio_error),label=str(channel+" "+date1+"/"+date2))
        PINValues.append(dict1["PIN"][:max_index])
        PINValues.append(dict2["PIN"][:max_index])
        PINErrors.append(dict1["PIN_error"][:max_index])
        PINErrors.append(dict2["PIN_error"][:max_index])
        PhotonErrors.append([plot_ipw.get_photons(x,0.7) for x in dict1["area_error"][:max_index]])
        PhotonErrors.append([plot_ipw.get_photons(x,0.7) for x in dict2["area_error"][:max_index]])

        ratioFit = fitPhotonPINCompare(PINValues,PINErrors,PhotonValues,PhotonErrors,channel,[date1,date2],iterNum)
        iterNum+= 1
	plt.figure(1)
        channelDate.append(str(channel+"\n"+date1+"/"+date2))
        ratios.append(ratioFit)
        

plt.title("Ratio between photon counts for various low sweeps on varying channels against IPW")
plt.xlabel("IPW")
plt.ylabel("Ratio")
plt.yscale("log")
plt.grid(True)
plt.legend(loc="upper right")
plt.show()

plt.figure(2)
plt.title("Ratio of gradient of fits to photon vs PIN plots")
plt.ylabel("Ratio")
plt.plot(range(len(ratios)),ratios)
plt.xticks(range(len(ratios)),channelDate)
plt.show()
