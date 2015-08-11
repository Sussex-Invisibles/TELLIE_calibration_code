# TELLIE_calibration_code
Code set developed to calibrate the light output and PIN response of each of the 95 individual TELLIE channels. The light response is montitored by a calibrated PMT, readout by a Tektronix DPO3000 oscilloscope.

### Pre requisits
 - python > 2.5 (you'll need a 32bit install to be compatable with NI VISA!)
 - NI VISA (it is free)
 - PyVISA
 - 'AcquireTek' - acquisition libraries for Tektronix scope (Available at Sussex-Invisables GitHub)
 - 'TELLIE' - Control software for TELLIE (available at Sussex-Invisibles GitHub)

### env.sh
Environment file to be sourced before running any of the python scipts provided here. The paths within the file should be changed to point to the users specific install location for both AcquireTek and TELLIE (see above). 

### ipw_broad_sweep.py
This script generates a calibration data set by varying the TELLIE pulse width (intensity setting) from 0 to 9000 (12 bit units). All channels show a 0 photon output beyond an IPW setting of 9000. Output includes .pkl files containing the measured 'scope traces for each IPW value (saved in a standardised directory structure created automatically - branching from a user defined starting directory), and a text file containing pulse shape and PIN readings (with errors where possible).

### ipw_low_sweep.py
This script generates a calibration data set by varying the TELLIE pulse width (intensity) about a user defined cut-off point (calculated using ipw_broad_sweep data set). The steps are much finer grain than in ipw_broad_sweep.py so as to well characterise the lower operational range (approximately 0-1e5 photons, exact numbers vary channel to channel). Output includes .pkl files containing the measured 'scope traces for each ipw value (saved in a standardised directory structure created automatically - branching from a user defined starting directory), and a text file containing pulse shape and PIN readings (with errors where possible).

### sweep.py
This file contains custom fuctions called by both ipw_broad_sweep.py and ipw_low_sweep.py scripts.

### plot_ipw.py
Plotting functions for datasets produced by both ipw_broad_sweep.py and ipw_low_sweep.py. Plots are stored as both TFiles and .pdfs for quick reference under broad_sweep/plots and low_intensity/plots for the broad and low sweeps respectively. 

### pulse_continuous.py
This script causes a TELLIE channel to fire at maximum intensity (IPW = 0), continuously. This script is used to give a constant, updating signal when setting up the PIN diode amplifier. A user can select a box and channel within that box with the -b and -c flags respectively. 

### checkMeasurements.py
A function to re-run measurements on a particular .pkl data file. Results will be stored with original measurment files, but with the file name appended with an additional '_checks'.

### readPklFile.py 
Opens and dumps to screen pulses contained within .pkl data files - for sanity checking. 


================================
TO-DO
================================
1/ Update plot_ipw.py to work with updated DAQ code
   Generate: - photons_vs_ipw 
   	     - time_vs_ipw(width, rise, fall)
	     - PIN_vs_IPW
	     - no.photons_vs_PIN
   	     All four plots on the same canvas! 

2/ Write ipw_broad_sweep

3/ Update README (that's right)
