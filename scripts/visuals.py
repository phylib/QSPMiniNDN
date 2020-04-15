import numpy
import matplotlib.pyplot as plotter
from scripts.filefetcher import FileFetcher

class Visualizer:

    def __init__(self, data):
        """
        define the values of all possible filter criteria
        and assign a FileFetcher instance for
        getting the necessary data
        """
        self.data = data
        self.fileFetcher = FileFetcher(data)
        self.runNumber = 3
        self.serverNumbers = [4, 16]
        self.topologies = ["cluster", "continent"]
        self.protocols = ["QuadTree", "StateVector", "ZMQ"]
        self.clientConcentrations = ["concentrated", "very-distributed"]
        if not(data == "latencies"):
            self.runNumber = 6
            self.clientConcentrations.append("distributed")
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
        and filter by the appropriate criteria depending on
        whether we analyze network data or sync latencies
        --> return the mean of the filtered values
            in all corresponding files
        """
        values = []
        run = "run%s" %run

        # check for serverNumber --> it is possible that serverNumber = run!
        # so in order to check for the serverNumber put underlines around the number
        for i in range(len(filterCriteria)):
            if filterCriteria[i].isnumeric():
                filterCriteria[i] = "_%s_" %filterCriteria[i]

        # parse the necessary values from the file, depending on
        # whether we want analyze sync latencies or network data
        for file in self.files:
            if self.data == "latencies":
                self.getValues(file, file, [protocol, barGroup, run] + filterCriteria, values)
            else:
                self.getValues(file, file[file['in/out'] == barGroup], [protocol, run] + filterCriteria, values)

        return numpy.mean(values)

    def getValues(self, file, dataframe, filterCriteria, values):
        """
        add the appropriate values of the filtered files
        to the values-list
        """
        if all(criterion in file.name for criterion in filterCriteria):
            for row in dataframe.values:
                value = row[len(row) - 1]
                if value >= 0.0:
                    values.append(float(value))
            print(file.name)


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
        if(len(barGroups)>1):
            self.removeTicks(showLabel=True)
        else:
            self.removeTicks(showLabel=False)
        axis.set_xticks(x_pos + width)
        axis.set_xticklabels(labels)
        axis.set_xlabel("Setting: " + sublabel)
        if(self.data == 'latencies'):
            axis.set_ylabel("Sync Latencies")
            axis.set_title("Sync Latencies of three different protocols")
        else:
            axis.set_ylabel("Bytes of Sync Payload")
            axis.set_title("Bytes of Sync Payload of three different protocols")

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

    visualizer = Visualizer("network")
    visualizer.plotGroups(["16", "concentrated", "cluster"], ["in", "out"], "16 servers in a cluster and high client concentration")

    #visualizer = Visualizer("latencies")
    #visualizer.plotGroups(["16", "concentrated"], ["continent", "cluster"], "16 servers and high client concentration")
    #visualizer.plotGroups(["16", "concentrated"], ["cluster"], "cluster topology and high client concentration")
    #visualizer.plotGroups(["16", "concentrated"], ["continent"], "continent topology and high client concentration")


