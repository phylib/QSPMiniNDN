import pandas

class FileFetcher:
    def __init__(self, csvDirectory):
        """
        Assign the directory in which the necessary
        files are contained
        """
        self.csvDirectory = csvDirectory

    def getCSVFile(self, numServers, topology, protocol, runNumber, clientConcentration):
        """
        each file lies in another folder inside the csvDirectory
        this folder has the same name as the file (without file extension);
        read the necessary file content in a dataframe and return it
        """
        fileDirectory = ("RESULTS_%d_%s_%s_run%d_ChunkChanges-%scsv" %(numServers, topology, protocol, runNumber, clientConcentration))
        filename = fileDirectory + ".csv"
        dataframe = pandas.read_csv(self.csvDirectory+"/"+fileDirectory+"/"+filename, sep="\t", usecols=["syncLatency"])
        dataframe.name = filename
        return dataframe
