import pandas

class FileFetcher:
    def __init__(self, data):
        """
        Assign the directory in which the necessary
        files are contained
        """
        self.data = data
        if data == "latencies":
            self.csvDirectory = "../result-csv-files"
        elif self.data == "network" or self.data == "packets" or self.data == "bytes":
            self.csvDirectory = "../2020-04-14_network-stats"
        else:
            self.csvDirectory = "../2020-04-08-all-summaries"

    def getCSVFile(self, numServers, topology, protocol, runNumber, clientConcentration):
        """
        each file lies in another folder inside the csvDirectory
        this folder has the same name as the file (without file extension);
        read the necessary file content in a dataframe and return it
        """
        fileDirectory = ("RESULTS_%d_%s_%s_run%d_ChunkChanges-%scsv" % (numServers, topology, protocol, runNumber, clientConcentration))

        # check what should be analyzed and get the correct files
        if self.data == "latencies":
            filename = fileDirectory + ".csv"
            dataframe = pandas.read_csv(self.csvDirectory+"/"+fileDirectory+"/"+filename, sep="\t", usecols=["syncLatency"])
            dataframe.name = filename
        elif self.data == "network":
            filename = "network-stats.csv"
            dataframe = pandas.read_csv(self.csvDirectory + "/" + fileDirectory + "/" + filename, sep="\t",
                                        usecols=["in/out", "bytesSyncPayload"])
            dataframe.name = fileDirectory + ".csv"
        elif self.data == "packets":
            filename = "network-stats.csv"
            dataframe = pandas.read_csv(self.csvDirectory + "/" + fileDirectory + "/" + filename, sep="\t",
                                        usecols=["in/out", "#interests", "#data", "#IPSyncPackets"])
            dataframe.name = fileDirectory + ".csv"
        elif self.data == "bytes":
            filename = "network-stats.csv"
            dataframe = pandas.read_csv(self.csvDirectory + "/" + fileDirectory + "/" + filename, sep="\t",
                                        usecols=["in/out", "bytesInterests", "bytesData", "bytesIPSyncPackets"])
            dataframe.name = fileDirectory + ".csv"
        else:
            filename = "summary.csv"
            dataframe = pandas.read_csv(self.csvDirectory + "/" + fileDirectory + "/" + filename, sep="\t",
                                        usecols=["lost"])
            dataframe.name = fileDirectory + ".csv"


        return dataframe
