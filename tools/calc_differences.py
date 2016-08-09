#Code to calculate residuals between two files

import sys
import csv
import matplotlib.pyplot as plt
import numpy as np
import plot_ipw

file1 = open(sys.argv[1],"r")
file2 = open(sys.argv[2],"r")

file1Dict = {}
file2Dict = {}

reader = csv.DictReader(file1,delimiter="\t")
firstIter = True
for row in reader:
    if firstIter:
       for key in row.keys():
           file1Dict[key] = [float(row[key])]
       firstIter = False
    
    else:
       for key in row.keys():
            file1Dict[key].append(float(row[key]))

reader = csv.DictReader(file2,delimiter="\t")
firstIter = True
for row in reader:
    if firstIter:
       for key in row.keys():
           file2Dict[key] = [float(row[key])]
       firstIter = False
    
    else:
       for key in row.keys():
           file2Dict[key].append(float(row[key]))


photonCounts1 = plot_ipw.get_photons(file1Dict["AREA"],0.7)
photonCountsError1 = plot_ipw.get_photons(file1Dict["AREA Error"],0.7) 

photonCounts2 = plot_ipw.get_photons(file2Dict["AREA"],0.7)
photonCountsError2 = plot_ipw.get_photons(file2Dict["AREA Error"],0.7) 

plt.errorbar(file1Dict["#PWIDTH"],np.subtract(photonCounts2,photonCounts1),yerr=np.sqrt(np.power(photonCountsError2,2)+np.power(photonCountsError1,2)))
plt.show()
