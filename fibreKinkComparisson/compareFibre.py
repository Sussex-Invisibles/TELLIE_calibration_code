import sys
import os
import csv
import numpy as np
import ROOT


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
    return -999999





directory = sys.argv[1]

lowFiles = os.listdir(directory)
dict1 = createDictionaryFromFile(os.path.join(directory,lowFiles[0]))
dict2 = createDictionaryFromFile(os.path.join(directory,lowFiles[1]))
max_index = returnFirstZeroIndex(dict1["area"],dict2["area"])
ratio_photon = np.mean(np.divide(dict1["area"][:max_index],dict2["area"][:max_index]))
print "The ratio of photon count between "+str(lowFiles[0])+" and "+str(lowFiles[1])+" is "+str(ratio_photon)




