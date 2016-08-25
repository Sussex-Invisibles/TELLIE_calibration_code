######################################
# Python script to re-calculate 
# stored measurements using raw data
#
# Author: Ed Leming
# Date  : 11/05/15
#######################################
import calc_utils as calc
import plot_ipw
import optparse
import os

if __name__ == "__main__":
    parser = optparse.OptionParser("Usage: python checkMeasurements.py [option]")
    parser.add_option("-f", "--file",
                      dest="file",
                      default=False,
                      help="Pass path to data file to be checked")
    (options,args) = parser.parse_args()

    res_list = plot_ipw.read_scope_scan(options.file)

    p = options.file.split('/')
    print p 
    box  = int(p[2][4:6])
    chan  = int(p[3][4:6])
    print chan
    overallChan = ((box-1)*8)+chan 
    dataPath = os.path.join(p[0],p[1],"Box_%02d/raw_data/channel_%02d/" % (box,overallChan))
    files = [ f for f in os.listdir(dataPath) if os.path.isfile(os.path.join(dataPath,f)) ]

    output_filename = "%s_check.dat" % options.file[0:-4]
    output_file = file(output_filename,'w')
    output_file.write("#PWIDTH\tPWIDTH Error\tPIN\tPIN Error\tWIDTH\tWIDTH Error\tRISE\tRISE Error\tFALL\tFALL Error\tAREA\tAREA Error\t\
Minimum\tMinimum Error\n")
    
    for i, file in enumerate(files): 
        fname = os.path.join(dataPath,file)
        x,y = calc.readPickleChannel(fname, 1)
        width = fname[-8:-4]
        #if int(width) == 8500:
            #calc.plot_eg_pulses(x,y,66,show=True)
        tmpResults = calc.dictionary_of_params(x,y)
        calc.printParamsDict(tmpResults, width)
        
        if i < 7:
            iter = i
        else:
            iter = i-1
        output_file.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n"%(width, 0,
                                            res_list[iter]["pin"], res_list[iter]["pin_err"],
                                            tmpResults["width"], tmpResults["width error"],
                                            tmpResults["rise"], tmpResults["rise error"],
                                            tmpResults["fall"], tmpResults["fall error"],
                                            tmpResults["area"], tmpResults["area error"],
                                            tmpResults["peak"], tmpResults["peak error"] ))

        calc.plot_eg_pulses(x,y,100,show=True)
    output_file.close()
