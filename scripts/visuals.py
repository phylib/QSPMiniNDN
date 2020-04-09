import numpy
import matplotlib.pyplot as plotter
from scripts.filefetcher import FileFetcher

class Visualizer:

    def __init__(self):
        self.fileFetcher = FileFetcher("../result-csv-files")
        self.runNumber = 3
        self.serverNumbers = [4, 16]
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

    def getMeanPerRun(self, protocol, group, criterias, run):
        sync_latencies = []
        for file in self.files:
            if protocol in file.name \
                    and group in file.name \
                    and all(criteria in file.name for criteria in criterias) \
                    and run in file.name:

                for row in file.values:
                    value = row[0]
                    if value >= 0.0:
                        sync_latencies.append(float(value))

        return numpy.mean(sync_latencies)


    def plotGroup(self, criterias, group, sublabel):
        means = []
        stds = []
        for protocol in self.protocols:
            runmeans = []
            for i in range(self.runNumber):
                mean = self.getMeanPerRun(protocol, group, criterias, str(i))
                runmeans.append(mean)
            means.append(numpy.mean(runmeans))
            stds.append(numpy.std(runmeans))
            print("Avg %s: %f" % (protocol, means[len(means)-1]))
            print("StD %s: %f" % (protocol, stds[len(stds)-1]))


        x_pos = numpy.arange(len(self.protocols))
        colors = [(1, 1, 1, 1), (0.6, 0.6, 0.6, 1), (0.2, 0.2, 0.2, 1)]
        figure, axis = plotter.subplots()
        bar = self.getBar(axis, x_pos, means, 0.75, stds, "black", 10, colors, "black")
        axis.set_ylabel("Sync Latencies")

        self.removeTicks(showLabel=False)
        axis.legend((bar[0],bar[1],bar[2]), self.protocols)
        axis.set_title("Sync Latencies of three different protocols")
        axis.set_xlabel(sublabel)

        axis.set_axisbelow(True)
        axis.yaxis.grid(True)

        plotter.tight_layout()
        plotter.show()

    def getProtocolData(self, protocol, criterias, groups):
        means = []
        stds = []
        for group in groups:
            runmeans = []
            for i in range(self.runNumber):
                mean = self.getMeanPerRun(protocol, group, criterias, str(i))
                runmeans.append(mean)
            means.append(numpy.mean(runmeans))
            stds.append(numpy.std(runmeans))
            print("Avg %s: %f" % (protocol, means[len(means) - 1]))
            print("StD %s: %f" % (protocol, stds[len(stds) - 1]))

        return [means, stds]

    def plotAll(self, criterias, groups):
        means = []
        stds = []

        for protocol in self.protocols:
            data = self.getProtocolData(protocol, criterias, groups)
            means.append(data[0])
            stds.append(data[1])

        x_pos = numpy.arange(len(groups))
        width = 0.25
        colors = [(1, 1, 1, 1), (0.6, 0.6, 0.6, 1), (0.2, 0.2, 0.2, 1)]
        figure, axis = plotter.subplots()

        quadTree = self.getBar(axis, x_pos, means[0], width, stds[0], "black", 10, colors[0], "black")
        stateVector = self.getBar(axis, x_pos + width, means[1], width, stds[1], "black", 10, colors[1], "black")
        zmq = self.getBar(axis, x_pos + 2*width, means[2], width, stds[2], "black", 10, colors[2], "black")

        axis.set_ylabel("Sync Latencies")
        self.removeTicks(showLabel=True)
        axis.set_xticks(x_pos+width)
        axis.set_xticklabels(groups)
        axis.set_title("Sync Latencies of three different protocols")
        axis.legend((quadTree[0], stateVector[0], zmq[0]), self.protocols)

        axis.set_axisbelow(True)
        axis.yaxis.grid(True)

        plotter.tight_layout()
        plotter.show()

    def getBar(self, axis, position, mean, width, error, errorcolor, capsize, color, edgecolor):
        return axis.bar(position, mean, width, yerr=error, ecolor=errorcolor, capsize=capsize, color=color, edgecolor=edgecolor)

    def removeTicks(self, showLabel):
        plotter.tick_params(
            axis='x',      # changes apply to the x-axis
            which='both',  # both major and minor ticks are affected
            bottom=False,  # ticks along the bottom edge are off
            top=False,     # ticks along the top edge are off
            labelbottom=showLabel)

if __name__ == "__main__":

    visualizer = Visualizer()
    visualizer.plotAll(["16", "concentrated"], ["continent", "cluster"])
    #visualizer.plotAll([], ["4", "16"])

    ''' Use the following statements to plot the data by ONE topology'''
    #visualizer.plotGroup(["16","concentrated"], "cluster", "concentrated cluster")
    #visualizer.plotGroup(["16", "concentrated"], "continent", "concentrated continent")




