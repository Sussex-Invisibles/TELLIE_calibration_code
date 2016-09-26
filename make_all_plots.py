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
			datFileArray = createLatestDatFileArray(dataFiles)
                        for datFil in datFileArray:
			    filePath = os.path.join(boxPath,datFil)
                            print "Making plots from: "+filePath
                            os.system("python plot_ipw.py -f "+filePath[2:])



make_plots("./broad_sweep")
make_plots("./low_intensity")
