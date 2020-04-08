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




if __name__ == "__main__":

    visualizer = Visualizer()
    visualizer.fetchAllFiles("cluster")

    quadTree_values = visualizer.getMeanAndStandardDeviation("QuadTree", "concentrated")
    print("Avg QuadTree: %f" %quadTree_values[0])
    print("StD QuadTree: %f" % quadTree_values[1])
    stateVector_values = visualizer.getMeanAndStandardDeviation("StateVector", "concentrated")
    print("Avg StateVector: %f" %stateVector_values[0])
    print("StD StateVector: %f" % stateVector_values[1])
    visualizer.closeAllFiles()

    x_pos = numpy.arange(len(visualizer.protocols))
    means = [quadTree_values[0], stateVector_values[0]]
    stds = [quadTree_values[1], stateVector_values[1]]

    figure, axis = plotter.subplots()
    axis.bar(x_pos, means, yerr=stds, align="center", alpha=0.5, ecolor="black", capsize=10)
    axis.set_ylabel("Sync Latencies")
    axis.set_xticks(x_pos)
    axis.set_xticklabels(visualizer.protocols)
    axis.set_title("Sync Latencies of two different protocols with\nhigh concentration of clients")
    axis.yaxis.grid(True)

    plotter.tight_layout()
    plotter.show()





