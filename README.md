# TELLIE_calibration_code
Code set developed to calibrate the light output and PIN response of each of the 96 individual TELLIE channels. The light response is montitored by a calibrated PMT, readout by a Tektronix DPO3000 oscilloscope.

### Pre requisits
 - python > 2.5 (you'll need a 32bit install to be compatable with NI VISA!)
 - NI VISA (it is free)
 - PyVISA
 - 'AcquireTek' - acquisition libraries for Tektronix scope (Available at Sussex-Invisables GitHub)
 - 'TELLIE' - Control software for TELLIE (available at Sussex-Invisibles GitHub)

### env.sh
Environment file to be sourced before running any of the python scipts provided here. The paths within the file should be changed to point to the users specific install location for both AcquireTek and TELLIE (see above). 

### ipw_low_sweep.py
This script generates a calibration data set by varying the TELLIE pulse width (intensity) about a user defined cut-off point (calculated using ipw_broad_sweep data set). Output includes .pkl files containing the measured 'scope traces for each ipw value (saved in a standardised directory structure), and a text file containing pulse shape and PIN readings (with errors where possible).

### sweep.py
This file contains custom fuctions called by both ipw_broad_sweep.py and ipw_low_sweep.py scripts.

### plot_ipw.py
Plotting functions for datasets produced by both ipw_broad_sweep.py and ipw_low_sweep.py. Plots are stored as both TFiles and .pdfs for quick reference. 

### readPklFile.py 
Opens and dumps to screen pulses contained within .pkl data files - for sanity checking. 
