import sys
import ROOT
import os
import csv
import matplotlib.pyplot as plt


def createDictionaryFromFile(inFile):
    outDict = {}
    outDict["channel"] = []
    outDict["PhotonPINChiSq"] = []
    outDict["PhotonIPWChiSq"] = []
    inputFile = open(inFile,"rb")
    csvIn = csv.reader(inputFile,delimiter=",")
    firstRow = 1
    for row in csvIn:
      if firstRow == 1:
         firstRow = 0
         continue
      outDict["channel"].append(int(row[15]))
      outDict["PhotonPINChiSq"].append(float(row[9]))
      outDict["PhotonIPWChiSq"].append(float(row[7]))
    return outDict



folder = sys.argv[1]
inFile = os.path.join(folder,"resultsOverview.csv")
outDict = createDictionaryFromFile(inFile)
plt.figure(1)
plt.subplot(211)
plt.title("Photon IPW Chi Sq against channel")
plt.xticks(outDict["channel"])
plt.plot(outDict["channel"],outDict["PhotonIPWChiSq"])
plt.subplot(212)
plt.title("Photon PIN  Chi Sq against channel")
plt.xticks(outDict["channel"])
plt.plot(outDict["channel"],outDict["PhotonPINChiSq"])
plt.show()


