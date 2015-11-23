# this code will be used to search through the already filtered files
# with identified magnetic field rotations.

import os
import csv
import numpy as np
import datetime
from collections import defaultdict
from matplotlib import dates
import prettyplotlib as pp
import matplotlib.pyplot as plt

class magAnalysis():
    class detections():
        def __init__(self):
            self.largeDecrease = list()
            self.smallDecrease = list()
            self.largeIncrease = list()
            self.smallIncrease = list()
            self.location = list()
            self.rotations = list()
            self.rotationTimeTags = list()
            self.results = list()

            
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
        self.calendarDay = self.location[self.location.index('_')-2:self.location.index('_')+4]

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
    
    def rotationData(self):
        """
            Returns the rotation data list with time tags.
        """
        return [self.detections.rotationTimeTags, self.detections.rotations], self.b1, self.b2
        
    def decreaseSearch(self):
        """
            Performs magnetic decrease and increase search. Returns a dictionary with results.
        """

        self.detections = self.detections()
        self.detections.location = self.location
        for index, row in enumerate(self.magdata):

            if row[3] < self.upper*self.background and row[3] < self.background - 2*self.std:
                # less than 50% of background and 2 std
                #print "Large decrease (less than " + str(self.upper*self.background) + ")", row[3]
                self.detections.largeDecrease.append([index,self.timestamps[index], row[3]])
                
            elif row[3] < self.lower*self.background and row[3] < self.background - self.std:
                # less than 25% of background and 1 std
                #print "Decrease (less than " + str(self.lower*self.background) + ")", row[3]
                self.detections.smallDecrease.append([index,self.timestamps[index], row[3]])
                
            elif row[3] > (1 + self.upper)*self.background and row[3] > self.background + 2*self.std:
                # greater than 50% of background
                #print "Large increase (greater than " + str((1 + self.upper)*self.background) + ")", row[3]
                self.detections.largeIncrease.append([index,self.timestamps[index], row[3]])
                
            elif row[3] > (1 + self.lower)*self.background and row[3] > self.background + self.std:
                # greater than 25% of background
                #print "Increase (greater than " + str((1 + self.lower)*self.background) + ")", row[3]
                self.detections.smallIncrease.append([index,self.timestamps[index], row[3]])

               
        if resultCounter(self.detections) == 0:
            self.detections.results.append(None)
            print "No observable jumps/dips in magnetic field strength"
        else:
            for attribute, bins in classIterator(self.detections):
                if 'crease' in attribute:
                    self.detections.results.append('Number of ' + attribute + ': ' + str(len(bins))) 
        
    def rotationDetermination(self):
        """
            Calculates the angular rotations throughout the dataset. Method used is a modified version of the LB critria initially
            used to generate the first datasets.
        """
        
        for index, row in enumerate(self.magdata):
            if index > 11 and index < (len(self.magdata) - 12):
                br1 = [row[0] for row in self.magdata[(index-12):(index-2)]]
                bt1 = [row[1] for row in self.magdata[(index-12):(index-2)]]
                bn1 = [row[2] for row in self.magdata[(index-12):(index-2)]]
                b1 = np.matrix((np.mean(br1), np.mean(bt1), np.mean(bn1)))

                br2 = [row[0] for row in self.magdata[(index+2):(index+12)]]
                bt2 = [row[1] for row in self.magdata[(index+2):(index+12)]]
                bn2 = [row[2] for row in self.magdata[(index+2):(index+12)]]
                b2 = np.matrix((np.mean(br2), np.mean(bt2), np.mean(bn2)))

                theta = np.arccos(np.dot(b1,b2.T)/(np.linalg.norm(b1)*np.linalg.norm(b2)))*180/np.pi

                self.detections.rotations.append(theta[0,0])
                self.detections.rotationTimeTags.append(self.timestamps[index])
                

##        self.b1 = b1
##        self.b2 = b2
        self.detections.rotationBoundary=[]
        if len(self.detections.rotations) != 0:
            
            for index, theta in enumerate(self.detections.rotations):
                if index > 0:
                    if theta > 30 and self.detections.rotations[index-1] < 30:
                        self.detections.rotationBoundary.append(self.detections.rotationTimeTags[index])
                if index < len(self.detections.rotations)-1:
                    if theta > 30 and self.detections.rotations[index+1] < 30:
                        self.detections.rotationBoundary.append(self.detections.rotationTimeTags[index])
         
        
    def classifier(self):
        """
            Classifies the results as a direct hit (magnetic increase/decrease bounded by a rotation), mismatch (decrease not bounded by rotation), or neither. 
        """

        print "Starting Classification"
        self.detections.rotationClass = [ self.detections.rotationTimeTags[index] for index, theta in enumerate(self.detections.rotations) if theta > 30]
        if len(self.detections.rotationClass) < 1:
            print "Too little rotation hits"
            self.detections.classification = "Too little rotation hits"

        else:
        
            for attribute, value in classIterator(self.detections):
                print value[1]
                if 'crease' in attribute:
                    
                    if value[1] > self.detections.rotationClass[0] and value[1] < self.detections.rotationClass[-1]:
                        print "direct hit", attribute, value[1]
                        self.detections.classification = "Direct hit"
                        #if self.detections.
                    else:
                        for angleStamp in self.detections.rotationClass:
                            if secondsCount(value[1],angleStamp).total_seconds < 10:
                                self.detections.classification = "Near miss"
                            
                            else:
                                self.detections.classification = "Nothing impressive"
        print "Ending Classification"

        
    def run(self):
        """
            Main class method.
        """

        #perform decrease/increase search.
        self.decreaseSearch()
        self.rotationDetermination()
        if self.detections.results[0] != None:
            print self.detections.results
            generatePlot(self)

def classIterator(classIter):
    """
        Generator for iterating over contents of a class.
    """
    for attribute, value in classIter.__dict__.iteritems():
        yield attribute, value
        
def generateDataFile(data,location):
    """
        Generates the dataset.
    """
    with open(location, 'w') as outputDataFile:
        writer = csv.writer(outputDataFile)
        writer.writerows(data)
    

def generatePlot(data):
    """
        Generates a plot and stores it in a folder for later inspection.
    """
    addendum = ""
    destination = "D:\\Research\\scripts\\Results\\FullSet1\\$FilteredPlots\\take 4\\"
    if len(data.detections.smallIncrease) != 0:
        addendum = "small increases\\"
    if len(data.detections.smallDecrease) != 0:
        addendum = "small decreases\\"
    if len(data.detections.largeIncrease) != 0:
        addendum = "large increases\\"
    if len(data.detections.largeDecrease) != 0:
        addendum = "large decreases\\"
    if addendum == "":
        addendum = "no decreases\\"
    
    plt.figure(1)
    plt.subplot(211)
    #print np.min(data.magdata), np.max(data.magdata)
    axes = plt.gca()
    axes.set_title("Year: '{year}, Day: {day}".format(year=data.calendarDay[:2], day=data.calendarDay[3:] ))
    axes.set_ylim([np.min(data.magdata)-1.2,np.max(data.magdata)+0.25])
    axes.set_ylabel(r'$\mathbf{B}$ (nT)' )

    #plot formatting
    formats = dates.DateFormatter('%H:%M:%S')
    axes.xaxis.set_major_locator(dates.MinuteLocator())
    axes.xaxis.set_major_formatter(formats)
    
    br, = pp.plot(dates.date2num(data.timestamps),[row[0] for row in data.magdata],label='$B_r$')
    bt, = pp.plot(dates.date2num(data.timestamps),[row[1] for row in data.magdata],label='$B_t$')
    bn, = pp.plot(dates.date2num(data.timestamps),[row[2] for row in data.magdata],label='$B_n$')
    b0, = pp.plot(dates.date2num(data.timestamps),[row[3] for row in data.magdata],label='$B_0$')
    print len(data.detections.rotationBoundary)
    if len(data.detections.rotationBoundary) == 1:
        rotation, = pp.plot([dates.date2num(data.detections.rotationBoundary), dates.date2num(data.detections.rotationBoundary)], [np.min(data.magdata)-1,np.max(data.magdata)+0.25], linestyle='--', color = 'm', alpha = 0.4, label='$RB$')
    else:
        for index, value in enumerate(data.detections.rotationBoundary):
            rotation, = pp.plot([dates.date2num(value), dates.date2num(value)], [np.min(data.magdata)-1,np.max(data.magdata)+0.25], linestyle='--', color = 'm', alpha = 0.4, label='$RB$')
    if len(data.detections.rotationBoundary) != 0:
        pp.legend(handles=[br,bt,bn,b0,rotation], loc='lower left', ncol=4, fancybox=True, framealpha=0.5)
    else:
        pp.legend(handles=[br,bt,bn,b0], loc='lower left', ncol=4, fancybox=True, framealpha=0.5)

    start, end = axes.get_xlim()
    axes.xaxis.set_ticks(np.arange(start, end, (end-start)/5))
    
    

    plt.subplot(212)
    axes2 = plt.gca()
    #plot formatting
    formats = dates.DateFormatter('%H:%M:%S')
    axes2.xaxis.set_major_locator(dates.MinuteLocator())
    axes2.xaxis.set_major_formatter(formats)
    axes2.set_ylabel(r'$\theta$ (deg)' )
    rotations, = pp.plot(dates.date2num(data.detections.rotationTimeTags),data.detections.rotations)
    #pp.legend(handles=[rotations], loc='lower left', ncol=4, fancybox=True, framealpha=0.5)
    

    outplotname =  'Plot ' + str(len(os.listdir(destination+addendum)) + 1)+ ' ' + data.timestamps[0].strftime('%y-%j-%H%M%S') + '.pdf'
    completename = os.path.join(destination+addendum,outplotname)
    plt.savefig(completename, bboxinches='tight')
    plt.clf()

    outplotname =  'Plot ' + str(len(os.listdir(destination+'rawdata\\'+addendum)) + 1)+ ' ' + data.timestamps[0].strftime('%y-%j-%H%M%S') + ' rawdata.csv'
    completename1 = os.path.join(destination+'rawdata\\'+addendum,outplotname)
    generateDataFile(data.rawdata,completename1)

    print "Done generating plot..."

def fileCounter(directory):
    """
        Counts the files in a directory.
    """

def secondsCount(timestamp1, timestamp2):
    """
        returns a time delta in seconds from datetimeobjects
    """
    return timestamp1 - timestamp2
    
def resultCounter(detections):
    """
        Counts results from run.
    """
    counter = 0
    for attribute, value in classIterator(detections):
        if 'crease' in attribute:
            counter += len(value)
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
    counter = 0
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
##        if magData.detections.results[0] != None:
##            break
        
    return magData, rawdata

if __name__ == '__main__':
    magData , rawdata = Main()
    magData.rotationDetermination()
    #test,b1,b2 = magData.rotationData()

    



