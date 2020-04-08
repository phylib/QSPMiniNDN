import pandas

class FileFetcher:
    def __init__(self, csvDirectory):
        self.csvDirectory = csvDirectory

    def getCSVFile(self, numServers, topology, protocol, runNumber, clientConcentration):
        fileDirectory = ("RESULTS_%d_%s_%s_run%d_ChunkChanges-%scsv" %(numServers, topology, protocol, runNumber, clientConcentration))
        filename = fileDirectory + ".csv"
        dataframe = pandas.read_csv(self.csvDirectory+"/"+fileDirectory+"/"+filename, sep="\t", usecols=["syncLatency"])
        dataframe.name = filename
        return dataframe
