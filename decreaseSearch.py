# this code will be used to search through the already filtered files
# with identified magnetic field rotations.

import os


def Main():
    datadirectory = 'D:\\Research\\scripts\\Results\\FullSet1\\'

    
if __name__ == '__main__':
    #Main()

    datadirectory = 'D:\\Research\\scripts\\Results\\FullSet1\\'
    subdirectories = [row for row in os.listdir(datadirectory) if '$' not in row]
    
    
