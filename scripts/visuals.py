import numpy
import matplotlib.pyplot as plotter
from scripts.filefetcher import FileFetcher

class Visualizer:

    def __init__(self):
        """
        define the values of all possible filter criteria
        and assign a FileFetcher instance for
        getting the necessary data
        """
        self.fileFetcher = FileFetcher("../result-csv-files")
        self.runNumber = 3
        self.serverNumbers = [4, 16]
        self.topologies = ["cluster", "continent"]
        self.protocols = ["QuadTree", "StateVector", "ZMQ"]
        self.clientConcentrations = ["concentrated", "very-distributed"]
        self.files = []
        self.fetchAllFiles()

    def fetchAllFiles(self):
        """
        fetch all csv-files which contain the data to analyze
        """
        for serverNumber in self.serverNumbers:
            for topology in self.topologies:
                for protocol in self.protocols:
                    for clientConcentration in self.clientConcentrations:
                        for i in range(self.runNumber):
                            file = self.fileFetcher.getCSVFile(serverNumber, topology, protocol, i, clientConcentration)
                            self.files.append(file)

    def getMeanPerRun(self, protocol, barGroup, filterCriteria, run):
        """
        check for the files of a certain protocol
        and filter by barGroup, filterCriteria and run number
        --> return the mean of the sync latencies
            in all corresponding files
        """
        sync_latencies = []

        for file in self.files:

            # check if file matches the pattern we search for
            if protocol in file.name \
                    and barGroup in file.name \
                    and all(criterion in file.name for criterion in filterCriteria) \
                    and run in file.name:

                # if there is a match add the sync latency value to the list
                for row in file.values:
                    value = row[0]
                    if value >= 0.0:
                        sync_latencies.append(float(value))

        return numpy.mean(sync_latencies)


    def getProtocolData(self, protocol, filterCriteria, barGroups):
        """
        return the means + standard deviations per bar group
        of a certain protocol
        """
        means = []
        stds = []

        # calculate the mean of each run of the given protocol per bar group
        # and calculate the mean + standard deviation
        # of each bar group based on the means per run
        for barGroup in barGroups:
            runmeans = []

            # calculate the means per run of each bar group for a certain protocol
            for i in range(self.runNumber):
                mean = self.getMeanPerRun(protocol, barGroup, filterCriteria, str(i))
                runmeans.append(mean)

            # get the mean + standard deviation of each bar group for the given protocol
            # by using the means per run for the calculation
            means.append(numpy.mean(runmeans))
            stds.append(numpy.std(runmeans))

            # print the calculated values for each bar group of the defined protocol
            # --> use the last element of the list
            #     because we need the most recently added value
            print("Avg %s: %f" % (protocol, means[len(means) - 1]))
            print("StD %s: %f" % (protocol, stds[len(stds) - 1]))

        return [means, stds]



    def plotGroups(self, filterCriteria, barGroups, sublabel):
        """
        calculate the mean + standard deviation per protocol for each bar group
        that should be plotted;
        each protocol is represented #(barGroups) times --> one bar + error bar per bar group
        for each protocol
        --> #(barGroups) bar groups are plotted, therefore
            each protocol has #(barGroups) means/standard deviations
        """
        means = []
        stds = []
        labels = []
        for barGroup in barGroups:
            labels.append(barGroup.capitalize())

        # calculate the means + standard deviations per bar group
        # for each protocol ( #(means) = #(standard deviations) = #(barGroups) * #(protocols))
        for protocol in self.protocols:
            data = self.getProtocolData(protocol, filterCriteria, barGroups)
            means.append(data[0])
            stds.append(data[1])

        # define the starting position ( = position of first bar) for each bar group
        # as well as the width and color for the bars
        # if only one bar group is plotted, add a space of 0.1 between the bars
        x_pos = numpy.arange(len(barGroups))
        width = 0.25
        space = 0
        if(len(barGroups) == 1):
            space = 0.1
        colors = [(1, 1, 1, 1), (0.6, 0.6, 0.6, 1), (0.2, 0.2, 0.2, 1)]
        figure, axis = plotter.subplots()

        # define the bars for each protocol we want to represent in the different bar groups
        quadTree = self.getBar(axis, x_pos, means[0], width, stds[0], "black", 10, colors[0], "black")
        stateVector = self.getBar(axis, x_pos + (width+space), means[1], width, stds[1], "black", 10, colors[1], "black")
        zmq = self.getBar(axis, x_pos + 2 * (width+space), means[2], width, stds[2], "black", 10, colors[2], "black")

        # define the labels, legend and remove the ticks
        axis.set_ylabel("Sync Latencies")
        if(len(barGroups)>1):
            self.removeTicks(showLabel=True)
        else:
            self.removeTicks(showLabel=False)
        axis.set_xticks(x_pos + width)
        axis.set_xticklabels(labels)
        axis.set_xlabel("Setting: " + sublabel)
        axis.set_title("Sync Latencies of three different protocols")
        axis.legend((quadTree[0], stateVector[0], zmq[0]), self.protocols)

        # show a grid along the y-axis and put it behind the bars
        axis.set_axisbelow(True)
        axis.yaxis.grid(True)

        # prevent overlapping of elements and show the plot
        plotter.tight_layout()
        plotter.show()

    def getBar(self, axis, position, mean, width, error, errorcolor, capsize, color, edgecolor):
        """
        return a bar, defined by the given parameters
        """
        return axis.bar(position, mean, width, yerr=error, ecolor=errorcolor, capsize=capsize, color=color, edgecolor=edgecolor)

    def removeTicks(self, showLabel):
        """
        remove the ticks along the x-axis, and show a label if necessary
        """
        plotter.tick_params(
            axis='x',      # changes apply to the x-axis
            which='both',  # both major and minor ticks are affected
            bottom=False,  # ticks along the bottom edge are off
            top=False,     # ticks along the top edge are off
            labelbottom=showLabel)

if __name__ == "__main__":

    visualizer = Visualizer()

    #visualizer.plotGroups(["16", "concentrated"], ["continent", "cluster"], "16 servers and high client concentration")
    #visualizer.plotGroups(["16", "concentrated"], ["cluster"], "cluster topology and high client concentration")
    visualizer.plotGroups(["16", "concentrated"], ["continent"], "continent topology and high client concentration")


