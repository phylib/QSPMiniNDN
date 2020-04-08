import numpy
import matplotlib.pyplot as plotter
import csv
from scripts.filefetcher import FileFetcher
import re

class Visualizer:

    def __init__(self):
        self.fileFetcher = FileFetcher("../result-csv-files")
        self.runNumber = 3;
        self.serverNumbers = [4]
        self.topologies = ["cluster", "continent"]
        self.protocols= ["QuadTree", "StateVector"]
        self.clientConcentrations = ["concentrated", "very-distributed"]
        self.files = []

    def fetchAllFiles(self, topology):
        for serverNumber in self.serverNumbers:
            for protocol in self.protocols:
                for clientConcentration in self.clientConcentrations:
                    for i in range(self.runNumber):
                        file = self.fileFetcher.getCSVFile(serverNumber, topology, protocol, i, clientConcentration)
                        self.files.append(file)

    def closeAllFiles(self):
        for file in self.files:
            file.close()

    def getMeanAndStandardDeviation(self, protocol, clientConcentration):
        sync_latencies = []
        for file in self.files:
           if protocol in file.name and clientConcentration in file.name:
                rows = csv.reader(file, delimiter='\t')
                for row in rows:
                    value = row[len(row) - 1]

                    # check if value is integer or float
                    if(re.fullmatch(r'[0-9]+(\.[0-9]+){0,1}', value)):
                        sync_latencies.append(float(value))


        return [numpy.mean(sync_latencies), numpy.std(sync_latencies)]

    def plotGroup(self, topology, clientConcentration):

        self.fetchAllFiles(topology)
        means = []
        stds = []
        for protocol in self.protocols:
            values = self.getMeanAndStandardDeviation(protocol, clientConcentration)
            print("Avg %s: %f" % (protocol, values[0]))
            print("StD %s: %f" % (protocol, values[1]))
            means.append(values[0])
            stds.append(values[1])

        self.closeAllFiles()

        x_pos = numpy.arange(len(self.protocols))
        figure, axis = plotter.subplots()
        axis.bar(x_pos, means, yerr=stds, align="center", alpha=0.8, ecolor="black", capsize=10)
        axis.set_ylabel("Sync Latencies")
        axis.set_xticks(x_pos)
        axis.set_xticklabels(self.protocols)
        axis.set_title("Sync Latencies of two different protocols with\nhigh concentration of clients")
        axis.yaxis.grid(True)

        plotter.tight_layout()
        plotter.show()




if __name__ == "__main__":

    visualizer = Visualizer()
    visualizer.plotGroup("continent", "very-distributed")




