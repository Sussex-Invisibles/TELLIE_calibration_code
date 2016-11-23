import os

#Method to parse data file names to obtain the latest list of plots
def createLatestDatFileArray(dataFiles):
    	chanList = ["Chan01","Chan02","Chan03","Chan04","Chan05","Chan06","Chan07","Chan08"]
        outFiles = []
	for chan in chanList:
            chanFiles = []
            for fil in dataFiles:
		if chan in fil:
		   chanFiles.append(fil)
            if len(chanFiles) > 0:
            	outFiles.append(chanFiles[-1])

	return outFiles		

def make_plots(base_dir):
	for boxFolder in os.listdir(base_dir):
		if boxFolder.startswith("Box"):
 			boxPath = os.path.join(base_dir,boxFolder)
			dataFiles = os.listdir(boxPath)
                        dataFiles.sort(key=lambda x: os.path.getmtime(os.path.join(boxPath,x)))
			datFileArray = createLatestDatFileArray(dataFiles)
                        for datFil in datFileArray:
                            if "CORRECTED" not in datFil:
                                print "NOT CORRECTED FILE IN: "+datFil
                                return 1
			    filePath = os.path.join(boxPath,datFil)
                            print "Making plots from: "+filePath
                            os.system("python plot_ipw.py -f "+filePath[2:])



if __name__=="__main__":
	make_plots("./broad_sweep")
	make_plots("./low_intensity")
