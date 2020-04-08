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
        self.protocols = ["QuadTree", "StateVector", "ZMQ"]
        self.clientConcentrations = ["concentrated", "very-distributed"]
        self.files = []
        self.fetchAllFiles()

    def fetchAllFiles(self):
        for serverNumber in self.serverNumbers:
            for topology in self.topologies:
                for protocol in self.protocols:
                    for clientConcentration in self.clientConcentrations:
                        for i in range(self.runNumber):
                            file = self.fileFetcher.getCSVFile(serverNumber, topology, protocol, i, clientConcentration)
                            self.files.append(file)

    def getMeanPerRun(self, protocol, criteria, run):
        sync_latencies = []
        for file in self.files:
            if protocol in file.name and criteria in file.name and run in file.name:

                for row in file.values:
                    value = row[0]
                    if(value >= 0.0):
                        sync_latencies.append(float(value))

        return numpy.mean(sync_latencies)


    def plotGroup(self, criteria, sublabel):
        means = []
        stds = []
        for protocol in self.protocols:
            runmeans = []
            for i in range(self.runNumber):
                mean = self.getMeanPerRun(protocol, criteria, str(i))
                runmeans.append(mean)
            means.append(numpy.mean(runmeans))
            stds.append(numpy.std(runmeans))
            print("Avg %s: %f" % (protocol, means[len(means)-1]))
            print("StD %s: %f" % (protocol, stds[len(stds)-1]))


        x_pos = numpy.arange(len(self.protocols))
        colors = ['red', 'green', 'blue']
        figure, axis = plotter.subplots()
        axis.bar(x_pos, means, yerr=stds, align="center", alpha=0.8, ecolor="black", capsize=10, color = colors)
        axis.set_ylabel("Sync Latencies")
        axis.set_xticks(x_pos)
        axis.set_xticklabels(self.protocols)
        axis.set_title("Sync Latencies of three different protocols")
        axis.set_xlabel(sublabel)
        axis.yaxis.grid(True)

        plotter.tight_layout()
        plotter.show()

if __name__ == "__main__":

    visualizer = Visualizer()
    visualizer.plotGroup("continent", "Continent")




