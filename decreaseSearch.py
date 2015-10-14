# this code will be used to search through the already filtered files
# with identified magnetic field rotations.

import os
import csv
import numpy as np
import datetime
from collections import defaultdict

class magAnalysis():
    def __init__(self, data, tol1, tol2, location):
        self.rawdata = data
        self.timestamps = timeStamps(data)
        self.magdata = [[float(item) for index, item in enumerate(row) if index > 4] for row in data]
        self.background = np.mean([float(row[3]) for row in self.magdata])
        self.std = np.std([float(row[3]) for row in self.magdata])
        # 50%
        self.upper = tol1
        # 25%
        self.lower = tol2
        #file location
        self.location = location

    def background(self):
        """
            Calculate background field for data set.
        """
        return self.background

    def std(self):
        """
            Calculate the standard deviation.
        """
        return self.std

    def detected(self):
        """
            Returns the detections dictionary.
        """
        return self.detections

    def run(self):
        """
            Main class method.
        """
        detections = defaultdict(list)
        detections['location'] = self.location
        for index, row in enumerate(self.magdata):

            if row[3] < self.upper*self.background:
                # less than 50% of background
                print "Large decrease (less than " + str(self.upper*self.background) + ")", row[3]
                detections['large decreases'].append([index,self.timestamps[index]])
                
            elif row[3] < self.lower*self.background:
                # less than 25% of background
                print "Decrease (less than " + str(self.lower*self.background) + ")", row[3]
                detections['small decreases'].append([index,self.timestamps[index]])
                
            elif row[3] > (1 + self.upper)*self.background:
                # greater than 50% of background
                print "Large increase (greater than " + str((1 + self.upper)*self.background) + ")", row[3]
                detections['large increases'].append([index,self.timestamps[index]])
                
            elif row[3] > (1 + self.lower)*self.background:
                # greater than 25% of background
                print "Increase (greater than " + str((1 + self.lower)*self.background) + ")", row[3]
                detections['small increases'].append([index,self.timestamps[index]])
                
        if resultCounter(detections) == 0:
            detections['Results'].append(None)
            print "No observable jumps/dips in magnetic field strength"
        else:
            for keys, bins in detections.items():
                if keys != 'location':
                    detections['Results'].append('Number of ' + keys + ': ' + str(len(bins))) 
        self.detections = detections

def resultCounter(detections):
    """
        Counts results from run.
    """
    counter = 0
    for keys, bins in detections.items():
        if keys != 'location':
            counter += len(bins)
    return counter

        
def timeStamps(dataset):
    """
        Creates a datetime object for the dataset thats inputted into the function. The list must be structured as 
    """
    
    timestamps = []
    
    for index, row in enumerate(dataset):
        try:
            timeObj = datetime.datetime.strptime(timeStampFix(row), '%y:%j:%H:%M:%S')
        except ValueError:
            print('Failed to create datetime object for ' + timeStampFix(row))
        timestamps.append(timeObj)
        
    return timestamps
    
def timeStampFix(row):
    """
        This function puts together the time info into a single string. It also fixes issues with bad times, such as 60 seconds, 60 minutes, etc.
    """
    try:
        if (int(np.floor(float(row[4]))) is 60) and ((int(row[3])) is 60):
            stamp = str(row[0]) + ':' + str(row[1]) + ':' + str(row[2]+1) + ':' + str(0*int(row[3])+1) + ':' + str(0*int(np.floor(float(row[4]))))
        elif (int(np.floor(float(row[4]))) is 60) and ((int(row[3])) is 59):
            stamp = str(row[0]) + ':' + str(row[1]) + ':' + str(int(row[2])+1) + ':' + str(0*int(row[3])+1) + ':' + str(0*int(np.floor(float(row[4]))))
        elif (int(row[3])) is 60:
            stamp = str(row[0]) + ':' + str(row[1]) + ':' + str(int(row[2])+1) + ':' + str(0*int(row[3])) + ':' + str(int(np.floor(float(row[4]))))
        elif int(np.floor(float(row[4]))) is 60:
            stamp = str(row[0]) + ':' + str(row[1]) + ':' + str(row[2]) + ':' + str(int(row[3])+1) + ':' + str(0*int(np.floor(float(row[4]))))
        else:
            stamp = str(row[0]) + ':' + str(row[1]) + ':' + str(row[2]) + ':' + str(int(row[3])) + ':' + str(int(np.floor(float(row[4]))))
    except IndexError:
        print "Failed to create string. Issue with " + str(row)
    return stamp



def dirGenerator(datadirectory):
    """
        Generates a list of the files in the raw dataset subdirectories in directory.
    """

    subdirectories = [row for row in os.listdir(datadirectory) if '$' not in row]

    #iterate through subdirectories
    for day in subdirectories:

        #collect raw data set file names in sub directories
        fileNames = [row for row in os.listdir(datadirectory + day + '\\RawDataFiles\\')]

        #iterate over the raw datasets
        print 'There are ' + str(len(fileNames)) + ' datasets in ' + day
        for index, datafile in enumerate(fileNames):
            yield datadirectory + day + '\\RawDataFiles\\' + datafile, day, datafile, index
            

def Main():
    datadirectory = 'D:\\Research\\scripts\\Results\\FullSet1\\'
    
    for fileNameAndPath, day, datafile, index in dirGenerator(datadirectory):
        print 'Opening ' + fileNameAndPath
        rawdata = []
        with open(fileNameAndPath,'rt') as rawfile:
            rawfiledata = csv.reader(rawfile, delimiter = ',',)
            for row in rawfiledata:
                rawdata.append(row)
        
        print 'There are ' + str(len(rawdata)) + ' samples in ' + day + ' ' + datafile

        magData = magAnalysis(rawdata, .5, .25, fileNameAndPath)
        magData.run()
        
        if magData.detections['Results'][0] != None:
            break
        
    return magData.detections

if __name__ == '__main__':
    detections = Main()

##    datadirectory = 'D:\\Research\\scripts\\Results\\FullSet1\\'
##    subdirectories = [row for row in os.listdir(datadirectory) if '$' not in row]
##
##    #iterate through subdirectories
##    for day in subdirectories:
##
##        #collect raw data set file names in sub directories
##        fileNames = [row for row in os.listdir(datadirectory + day + '\\RawDataFiles\\')]
##
##        #iterate over the raw datasets
##        rawdata = []
##        print 'There are ' + str(len(fileNames)) + ' datasets in ' + day
##        for datafile in fileNames:
##            fileNameAndPath = datadirectory + day + '\\RawDataFiles\\' + datafile
##            print 'Opening ' + datafile + ' from ' + day
##            with open(fileNameAndPath,'rt') as rawfile:
##                rawfiledata = csv.reader(rawfile, delimiter = ',',)
##                for row in rawfiledata:
##                    rawdata.append(row)
##
##            print 'There are ' + str(len(rawdata)) + ' samples in ' + day + ' ' + datafile
##        break
