###############################################################################
# Spin Down
# This script reads the spinning photogate and writes the number of
# counts to a file. 
#
# OUTPUT (to file): times = the time elapsed at each data reading
#                   counts = the photogate counter reading at each time
#
# CHANGEABLE PARAMETERS: filename = where the data is written (prompted)
#                        deltaT   = time (s) between each 1 second sample
#                        numPts   = number of points to record 
# Original MATLAB version by Bruce Thompson, 6/18/2003
# Later updates by: Emily Backus (6/2012)
#                   Matt Sullivan (Fall 2015)
#                   Kelley Sullivan (Spring 2019)
#
# This version by Eric Leibensperger (Spring 2021)
###############################################################################
 
import numpy as np # for math functions
import time # for timing
import os.path # for testing file for i/o
import nidaqmx # for interfacing with NI DAQ

# Function to retrieve data from DAQ
def getDAQ(rate,numSample,channel):
    # We are using an NI DAQ, nidaqmx library contains routines to interact
    # with DAQ.
    # Run a data acquisition task:
    with nidaqmx.Task() as task:
        # Set the channel
        task.ai_channels.add_ai_voltage_chan(channel)
        # Set the rate of observations to be retrieved and the total number
        # of samples to be taken. This will measure for numSample/rate seconds.
        # We usually set the two to 48000, so it is 48000 measurements over
        # the course of 1 second.
        task.timing.cfg_samp_clk_timing(rate,samps_per_chan=numSample)
        # Changing the range doesn't seem to do anything. Same story for the
        # offset. The DAQ returns -1.39173206 when it should be 0V. Add this on
        # to make it zero
        #task.ai_rng_high=5
        #task.ai_rng_low=-5
        #task.ai_dc_offset=1.39173206
        p=np.array(task.read(numSample))+1.39173206 # change so no signal = 0, signal =+5V 
    return p

# Count the number of leading edges.
#
#          _________      __________
# ________|         |_____|
#       Here             Here
# This is a python version of the matlab function originally written bt
# Bruce Thompson and edited by Emily Backus, Matt Sullivan, and Kelley Sullivan
def countEdges(p):
    # Strategy: loop through
    ind=0 # Set looping index to 0
    maxInd=len(p)-1 # maximum index
    count=0 # number of edges found thus far
    
    # while we're not at the end... note that this is < maxInd and not <= maxInd
    # this is because we won't accept a new edge in the last piece of data
    while ind<maxInd:
        # Find low level
        # While the value is bigger than 2.5, then increment the index. If
        # we get to the end, then stop
        while p[ind]>2.5:
            ind+=1
            if ind>maxInd: break
        # If we're not at the end, look for when it goes higer again.
        if ind<maxInd:
            while p[ind] <3.5:
                ind+=1 
                # if made it to end, let's get out of here
                if ind>maxInd: break
            if ind<maxInd: count+=1
    return count

##############
# This is the main function that does everything.
# Important parameters to be set:
deltaT=10 # time (seconds) between 1 second sample periods
numPts=11 # number of sample periods
rate=48000 # Frequency (Hz) of measurements
numSample=48000 # number of samples to take per measurement
channel='Dev2/ai1' # channel on daq

# Get the output file 
outFile=input("Enter filename to write the file: ") 
# Test if the file exists. If so, ask if you really want to overwrite
if os.path.isfile(outFile): 
    keepGoing=True 
    while keepGoing:
        # Ask if user wants to clobber file or not
        yayOrNay=input("This file exists, do you want to overwrite? [Y or y for yes]")
        # if yes, then we're done here
        if yayOrNay=='Y' or yayOrNay=='y':
            keepGoing=False
            #os.remove(outFile) # don't need to manually remove file..
        else:
            # if no, then ask for a new filename
            outFile=input("Enter filename other than \""+outFile+"\" to write the file: ")  
            # double check that this one doesn't exist. if it doesn't, we're done here.
            # if it does, we have to go back up the beginning of this loop...
            if not os.path.isfile(outFile): keepGoing=False 
    
# Let the world know what is happening
print('\nOutput will be written to: '+outFile)
# Set up the file for output by writing the header. 'w' will clobber an existing file
fId = open(outFile,"w")
fId.write("Sample  Times     Counts\n")
fId.close()
# Initialize some variables 
pts = 0 # to count/index number of samples
counts = np.zeros(numPts)
last = 0

    
input('Spin up disk, press enter to start')
print("    Time (s), Counts")
firstT=time.time()
# Keep going until all requested data is recorded
while pts < numPts:
    ##### GET DATA #####
    now=time.time()
    p=getDAQ(rate,numSample,channel)   
    
    # Get number of edges
    #counts[ind]=countEdges(p) #older method
    # Newer method:
    nP=len(p)
    counts[pts]=np.sum((p[0:(nP-2)]<2.5) & (p[1:(nP-1)]>3.5))
        
    # Print to screen and file what is happening
    print("%3d %8.1f %8.0f" % (pts,last,counts[pts]))
    fId = open(outFile,"a")
    fId.write("%3d %8.1f %8.0f\n" % (pts,last,counts[pts]))
    fId.close()

    # Wait until we're at least 10 seconds after last entry. Wait in 0.1 
    # increments
    while time.time() < (now+deltaT):
        time.sleep(0.1)
            
    # Update counter and last time
    pts+=1    
    last+=deltaT

    


           


    