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

    def getMeanPerRun(self, protocol, group, criteria, run):
        sync_latencies = []
        for file in self.files:
            if protocol in file.name and group in file.name and criteria in file.name and run in file.name:

                for row in file.values:
                    value = row[0]
                    if(value >= 0.0):
                        sync_latencies.append(float(value))

        return numpy.mean(sync_latencies)


    def plotGroup(self, group, criteria, sublabel):
        means = []
        stds = []
        for protocol in self.protocols:
            runmeans = []
            for i in range(self.runNumber):
                mean = self.getMeanPerRun(protocol, group, criteria, str(i))
                runmeans.append(mean)
            means.append(numpy.mean(runmeans))
            stds.append(numpy.std(runmeans))
            print("Avg %s: %f" % (protocol, means[len(means)-1]))
            print("StD %s: %f" % (protocol, stds[len(stds)-1]))


        x_pos = numpy.arange(len(self.protocols))
        colors = [(1, 1, 1, 1), (0.6, 0.6, 0.6, 1), (0.2, 0.2, 0.2, 1)]
        figure, axis = plotter.subplots()
        axis.bar(x_pos, means, yerr=stds, ecolor="black", capsize=10, color = colors, edgecolor='black')
        axis.set_ylabel("Sync Latencies")
        axis.set_xticks(x_pos)
        axis.set_xticklabels(self.protocols)
        axis.set_title("Sync Latencies of three different protocols")
        axis.set_xlabel(sublabel)
        axis.yaxis.grid(True)

        plotter.tight_layout()
        plotter.show()

    def getProtocolData(self, protocol, criteria, groups):
        means = []
        stds = []
        for group in groups:
            runmeans = []
            for i in range(self.runNumber):
                mean = self.getMeanPerRun(protocol, group, criteria, str(i))
                runmeans.append(mean)
            means.append(numpy.mean(runmeans))
            stds.append(numpy.std(runmeans))
            print("Avg %s: %f" % (protocol, means[len(means) - 1]))
            print("StD %s: %f" % (protocol, stds[len(stds) - 1]))

        return [means, stds]

    def plotAll(self, criteria, groups):
        means = []
        stds = []

        for protocol in self.protocols:
            data = self.getProtocolData(protocol, criteria, groups)
            means.append(data[0])
            stds.append(data[1])

        x_pos = numpy.arange(len(groups))
        width = 0.25
        colors = [(1, 1, 1, 1), (0.6, 0.6, 0.6, 1), (0.2, 0.2, 0.2, 1)]
        figure, axis = plotter.subplots()
        quadTree = axis.bar(x_pos, means[0], width, yerr=stds[0], ecolor="black", capsize=10, color = colors[0], edgecolor='black')
        stateVector = axis.bar(x_pos+width, means[1], width,yerr=stds[1], ecolor="black", capsize=10, color = colors[1], edgecolor='black')
        zmq = axis.bar(x_pos+2*width, means[2], width, yerr=stds[2], ecolor="black", capsize=10, color = colors[2], edgecolor='black')

        axis.set_ylabel("Sync Latencies")
        axis.set_xticks(x_pos+width)
        axis.set_xticklabels(groups)
        axis.set_title("Sync Latencies of three different protocols\nusing two different topologies")
        axis.legend((quadTree[0], stateVector[0], zmq[0]), self.protocols)

        axis.yaxis.grid(True)

        plotter.tight_layout()
        plotter.show()

if __name__ == "__main__":

    visualizer = Visualizer()
    visualizer.plotAll("concentrated", ["cluster", "continent"])

    ''' Use the following statements to plot the data by ONE topology'''
    #visualizer.plotGroup("cluster", "concentrated", "concentrated cluster")
    #visualizer.plotGroup("continent", "concentrated", "concentrated continent")




