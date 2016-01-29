import matplotlib.pyplot as plt
import sys
import argparse 

class data:
    def __init__(self,dataName):
        self.name = dataName
        self.values = []

    def addDataPoint(self,dataPoint):
        #try:
        self.values.append(float(dataPoint))
        #except:
        #    print "Unable to convert data point to float skipping: ",dataPoint

    def getName(self):
        return self.name

    def getData(self):
        return self.values

class dataSet:
    def __init__(self):
        self.dataList = []

    def getDataList(self):
        return self.dataList

    #Method to get data object for certain value name
    def findData(self,dataName):
        for dat in self.dataList:
            if dataName == dat.getName():
                return dat
        print "Unable to find data Item: ",dataName
        return 0

    def parseFile(self,filename):
        inFile = open(filename)
	print filename
        firstLine = True
        for line in inFile:
            dataVals = (line.strip()).split(",")
            if firstLine:
                for element in dataVals:
                    self.dataList.append(data(element))
                firstLine = False
            else:
                for i in range(len(dataVals)-1,-1,-1):
                    self.dataList[i].addDataPoint(dataVals[i])
		    if (i == 8 or i == 10)  and (int(dataVals[14]) in range(41,49)):
			    print self.dataList[14].getName()+" "+str(dataVals[14])+" "+self.dataList[i].getName()+" "+str(dataVals[i])



#Method to to a simple x vs y plot with optional error bars
def simplePlot(fileData,xName,yName,iter,xError=0,yError=0):
    xDat =  fileData.findData(xName)
    yDat =  fileData.findData(yName)
    cols = ["r","g","b"]
    colour = cols[iter%len(cols)]
    xErr = 0
    yErr = 0
    if xError != 0 and yError == 0:
        xErr = fileData.findData(xError)
        plt.errorbar(xDat.getData(),yDat.getData(),xerr=xErr.getData(),c=colour)
	plt.ylim(0,1)
	plt.gca().set_marker('o')
        plt.ylabel(yName)
        plt.xlabel(xName)
        plt.title("Plot of "+yName+" vs. "+xName+" with errors given by "+xError)
        #plt.show()
        
    elif xError == 0 and yError != 0:
        yErr = fileData.findData(yError)
        plt.errorbar(xDat.getData(),yDat.getData(),yerr=yErr.getData(),c=colour)
        plt.ylabel(yName)
        plt.xlabel(xName)
        plt.title("Plot of "+yName+" vs. "+xName+" with errors given by "+yError)
        #plt.show()

    elif xError != 0 and yError != 0:
        xErr = fileData.findData(xError)
        yErr = fileData.findData(yError)
        plt.errorbar(xDat.getData(),yDat.getData(),yerr=yErr.getData(),xerr=xErr.getData(),c=colour)
	plt.gca().set_marker('o')
        plt.ylabel(yName)
        plt.xlabel(xName)
        plt.title("Plot of "+yName+" vs. "+xName+" with errors given by y: "+yError+" and x: "+xError)
        #plt.show()

    elif xError == 0 and yError == 0:
        plt.plot(xDat.getData(),yDat.getData(),'ro',c=colour)
	#plt.ylim(0,1)
        plt.ylabel(yName)
        plt.xlabel(xName)
        plt.title("Plot of "+yName+" vs. "+xName)
        #plt.show()

#Method to plot 2 yValues against a Single x value with optional error bars
def doublePlot(xData,y1Data,y2Data,x1Error=0,x2Error=0,y1Error=0,y2Error=0):
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f",dest="file",nargs="*",help="Results file to be read in")
    parser.add_argument("-o",dest="parameter",default="ipwChi2",help="The parameter to be plotted against channel no. Default: ipwChi2")
    args = parser.parse_args() 
    plt.figure(0)
    file = args.file
    for i in range(len(file)):
	    fileData = dataSet()
	    fileData.parseFile(file[i])
	    if fileData.findData(args.parameter) == 0:
		raise ValueError("Parameter [%s] does not exist in file %s" % (args.parameter, args.file[i]))
	    simplePlot(fileData,"channel",args.parameter,i)
    plt.show()
