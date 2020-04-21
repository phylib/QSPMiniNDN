import numpy
import pandas
import scipy.stats
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

        # for analyzing sync latencies there are less
        # files to get data from
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


    def getMeanPerRun(self, protocol, barGroup, filterCriteria, run, columnFilter=None):
        """
        check for the files of a certain protocol
        and filter by the appropriate criteria depending on
        what should be analyzed (sync latencies, network or summary = default)
        --> return the mean of the filtered values
            in all corresponding files
        """
        values = []
        run = "run%s" %run

        # check for serverNumber --> it is possible that serverNumber = run!
        # so in order to mark the serverNumber as such put underlines around the number
        for i in range(len(filterCriteria)):
            if filterCriteria[i].isnumeric():
                filterCriteria[i] = "_%s_" %filterCriteria[i]

        # parse the necessary values from the file, depending on
        # whether we want analyze sync latencies, network data or summaries = default
        for file in self.files:
            if self.data == "latencies":
                self.getValues(file.name, file, [protocol, barGroup, run] + filterCriteria, values)
            elif self.data == "network":
                self.getValues(file.name, file[file['in/out'] == barGroup], [protocol, run] + filterCriteria, values)
            elif self.data == "packets" or self.data == "bytes":
                # columnFilter[0] defines if we filter by 'in' or 'out'
                # columnFilter[1] defines the column-name
                frame = file[file['in/out'] == columnFilter[0]]
                #frame = {columnFilter[1]: file[columnFilter[1]]}
                self.getValues(file.name, frame, [protocol, barGroup, run] + filterCriteria, values, columnFilter[1])
            else:
                self.getValues(file.name, file, [protocol, barGroup, run] + filterCriteria, values)

        return numpy.mean(values)

    def getValues(self, filename, dataframe, filterCriteria, values, column_filter=None):
        """
        add the appropriate values of the filtered files
        to the values-list
        """

        if column_filter == None:
            column_filter = dataframe.columns[-1]

        if all(criterion in filename for criterion in filterCriteria):
            vector = dataframe[dataframe[column_filter] >= 0.0][column_filter].to_numpy()
            values += vector.tolist()

    def mean_confidence_interval(self, data, confidence=0.95):
        """
        Calculates the mean and the confidence interval for a given list of values
        """

        a = 1.0 * numpy.array(data)
        n = len(a)
        m, se = numpy.mean(a), scipy.stats.sem(a)
        h = se * scipy.stats.t.ppf((1 + confidence) / 2., n - 1)
        return m, h

    def getProtocolData(self, protocol, filterCriteria, barGroups, columnFilter = None):
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
                if self.data == "packets" or self.data == "bytes":
                    mean = self.getMeanPerRun(protocol, barGroup, filterCriteria, str(i), columnFilter)
                    runmeans.append(mean)
                else:
                    mean = self.getMeanPerRun(protocol, barGroup, filterCriteria, str(i))
                    runmeans.append(mean)

            # get the mean + standard deviation of each bar group for the given protocol
            # by using the means per run for the calculation
            print(runmeans)
            mean_confidence = self.mean_confidence_interval(runmeans)
            means.append(mean_confidence[0])
            stds.append(mean_confidence[1])

            # print the calculated values for each bar group of the defined protocol
            # --> use the last element of the list
            #     because we need the most recently added value
            print("Avg %s: %f" % (protocol, means[len(means) - 1]))
            print("StD %s: %f" % (protocol, stds[len(stds) - 1]))

        return [means, stds]



    def plotSimpleBarChart(self, axis, filterCriteria, barGroups):
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
        sublabel = self.buildLabel(filterCriteria)

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


        # define the bars for each protocol we want to represent in the different bar groups
        quadTree = self.getBar(axis, x_pos, means[0], width, None, stds[0], "black", 10, colors[0], "black")
        stateVector = self.getBar(axis, x_pos + (width+space), means[1], width, None, stds[1], "black", 10, colors[1], "black")
        zmq = self.getBar(axis, x_pos + 2 * (width+space), means[2], width, None, stds[2], "black", 10, colors[2], "black")

        # define the labels, legend and remove the ticks
        if(len(barGroups)>1):
            self.removeTicks(showLabel=True)
        else:
            self.removeTicks(showLabel=False)
        axis.set_xticks(x_pos + width)
        axis.set_xticklabels(labels)
        axis.set_xlabel("Setting: " + sublabel)

        # set the labels according to the data we analyzed
        if(self.data == 'latencies'):
            axis.set_ylabel("Sync Latencies")
            axis.set_title("Sync Latencies of three different protocols")
        elif(self.data == "network"):
            axis.set_ylabel("Bytes of Sync Payload")
            axis.set_title("Bytes of Sync Payload of three different protocols")
        else:
            axis.set_ylabel("Lost Data")
            axis.set_title("Lost Data of three different protocols")

        axis.legend((quadTree[0], stateVector[0], zmq[0]), self.protocols)

        # show a grid along the y-axis and put it behind the bars
        axis.set_axisbelow(True)
        axis.yaxis.grid(True)


    def plotStackedBarChart(self, axis, filterCriteria, barGroups):
        """
        for plotting the stacked bar chart do not
        use error bars --> standard deviation is not needed,
        only the means
        the means are stored in the form (p = protocol):
        [[p_1(#interests), p_1(#data), p_1(#IPSyncPackets)], ...,[p_n(#interests), p_n(#data), p_n(#IPSyncPackets)]]
        """
        means = []
        labels = []
        for barGroup in barGroups:
            labels.append(barGroup.capitalize())
        sublabel = self.buildLabel(filterCriteria)

        if self.data == "packets":
            columnFilters = {
                'QuadTree': [["out", "#data"], ["in", "#interests"]],
                'StateVector': [["out", "#data"], ["in", "#interests"]],
                'ZMQ': [["out", "#IPSyncPackets"]]}
        else:
            columnFilters = {
                'QuadTree': [["out", "bytesData"], ["in", "bytesInterests"]],
                'StateVector': [["out", "bytesData"], ["in", "bytesInterests"]],
                'ZMQ': [["out", "bytesIPSyncPackets"]]}

        for protocol in self.protocols:
            columnmeans = []
            for columnFilter in columnFilters[protocol]:
                data = self.getProtocolData(protocol, filterCriteria, barGroups, columnFilter)
                columnmeans.append(data[0])
            means.append(columnmeans)

        print(means)

        # define the starting position ( = position of first bar) for each bar group
        # as well as the width and color for the bars
        # if only one bar group is plotted, add a space of 0.1 between the bars
        x_pos = numpy.arange(len(barGroups))
        width = 0.25
        space = 0
        if (len(barGroups) == 1):
            space = 0.1
        colors = [(1, 1, 1, 1), (0.6, 0.6, 0.6, 1), (0.2, 0.2, 0.2, 1)]

        # define the bars for each protocol we want to represent in the different bar groups
        quadTree_data = self.getBar(axis, x_pos, means[0][0], width, 0, None, None, 10, colors[0], "black")
        quadTree_interests = self.getBar(axis, x_pos, means[0][1], width, means[0][0], None, None, 10, colors[0], "black", "//")

        stateVector_data = self.getBar(axis, x_pos + (width + space), means[1][0], width, 0, None, None, 10, colors[1], "black")
        stateVector_interests = self.getBar(axis, x_pos + (width + space),means[1][1], width, means[1][0], None, None, 10, colors[1], "black", "//")


        zmq = self.getBar(axis, x_pos + 2 * (width + space), means[2][0], width, 0, None, None, 10, colors[2], "black")

        # define the labels, legend and remove the ticks
        if (len(barGroups) > 1):
            self.removeTicks(showLabel=True)
        else:
            self.removeTicks(showLabel=False)
        axis.set_xticks(x_pos + width)
        axis.set_xticklabels(labels)
        axis.set_xlabel("Setting: " + sublabel)

        # set the labels according to the data we analyzed
        if self.data == "packets":
            axis.set_ylabel("Number of packets")
            axis.set_title("Number of packets for three different protocols")
        else:
            axis.set_ylabel("Number of bytes")
            axis.set_title("Number of bytes for three different protocols")

        legendlabels = ["QuadTree Interests", "QuadTree Data", "StateVector Interests", "StateVector Data", "ZMQ outgoing IP-Packets"]
        axis.legend((quadTree_interests[0], quadTree_data, stateVector_interests[0], stateVector_data[0], zmq[0]), legendlabels)

        # show a grid along the y-axis and put it behind the bars
        axis.set_axisbelow(True)
        axis.yaxis.grid(True)


    def getBar(self, axis, position, mean, width, bottom, error, errorcolor, capsize, color, edgecolor, hatch=None):
        """
        return a bar, defined by the given parameters
        """
        return axis.bar(position, mean, width, bottom = bottom, yerr=error, ecolor=errorcolor, capsize=capsize, color=color, edgecolor=edgecolor, hatch=hatch)

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


    def buildLabel(self, filterCriteria):
        """
        build the label under the x_axis based on
        the passed filterCriteria
        """
        label = ""

        # put all criteria in the label somehow
        for i in range(len(filterCriteria)):
            criterion = filterCriteria[i]

            # if it is a number, it stands for the number of servers
            if criterion.isnumeric() and int(criterion) in self.serverNumbers:
                label += "%s servers" %criterion

            # define the concentration level of clients
            elif criterion in self.clientConcentrations:
                if(criterion == "concentrated"):
                    concentrationLevel = "high"
                elif(criterion == "distributed"):
                    concentrationLevel = "low"
                else:
                    concentrationLevel = "very low"
                label += "%s client concentration" %concentrationLevel

            # if the criterion is a topology do not put a space in front of
            # it, if it is the first criterion used in the label
            elif criterion in self.topologies:
                if i > 0:
                    label += " "
                label += "in a %s" %criterion

            # if the current criterion is not the last one --> add 'and' to label
            # do not add 'and' if the current criterion is the first one
            # and it is also a topology, use 'with' instead
            # example: "cluster with 16 servers.....", instead of "cluster and 16 servers...."
            if i < (len(filterCriteria)-1) and not(filterCriteria[i+1] in self.topologies)\
                    and not(criterion in self.topologies and i == 0):
                label += " and "
            elif i < (len(filterCriteria)-1) and not(filterCriteria[i+1] in self.topologies)\
                    and (criterion in self.topologies and i == 0):
                label += " with "

        return label

if __name__ == "__main__":

    # visualize packets
    #visualizer = Visualizer("packets")
    #figure, axes = plotter.subplots(nrows=2, ncols=2)
    #figure.set_size_inches(15, 7)
    #visualizer.plotStackedBarChart(axes[0, 0], ["16", "very-distributed"], ["cluster", "continent"])
    #visualizer.plotStackedBarChart(axes[0, 1], ["16", "concentrated"], ["cluster", "continent"])
    #visualizer.plotStackedBarChart(axes[1, 0], ["4", "very-distributed"], ["cluster", "continent"])
    #visualizer.plotStackedBarChart(axes[1, 1], ["4", "concentrated"], ["cluster", "continent"])


    #visualize bytes
    # visualizer = Visualizer("bytes")
    # figure, axes = plotter.subplots(nrows=2, ncols=2)
    # figure.set_size_inches(15, 7)
    # visualizer.plotStackedBarChart(axes[0, 0], ["16", "very-distributed"], ["cluster", "continent"])
    # visualizer.plotStackedBarChart(axes[0, 1], ["16", "concentrated"], ["cluster", "continent"])
    # visualizer.plotStackedBarChart(axes[1, 0], ["4", "very-distributed"], ["cluster", "continent"])
    # visualizer.plotStackedBarChart(axes[1, 1], ["4", "concentrated"], ["cluster", "continent"])


    #visualize summary
    visualizer = Visualizer("summary")
    figure, axes = plotter.subplots(nrows=2, ncols=3)
    figure.set_size_inches(15, 7)
    visualizer.plotSimpleBarChart(axes[0, 0], ["16", "very-distributed"], ["cluster", "continent"])
    visualizer.plotSimpleBarChart(axes[0, 1], ["16", "distributed"], ["cluster", "continent"])
    visualizer.plotSimpleBarChart(axes[0, 2], ["16", "concentrated"], ["cluster", "continent"])
    visualizer.plotSimpleBarChart(axes[1, 0], ["4", "very-distributed"], ["cluster", "continent"])
    visualizer.plotSimpleBarChart(axes[1, 1], ["4", "distributed"], ["cluster", "continent"])
    visualizer.plotSimpleBarChart(axes[1, 2], ["4", "concentrated"], ["cluster", "continent"])


    #visualize in/out network-traffic
    #visualizer = Visualizer("network")
    #figure, axis = plotter.subplots()
    #visualizer.plotSimpleBarChart(axis, ["16", "very-distributed", "cluster"], ["in", "out"])

    #visualize sync latencies
    #visualizer = Visualizer("latencies")
    #figure, axis = plotter.subplots()
    #visualizer.plotSimpleBarChart(axis, ["16", "very-distributed"], ["continent", "cluster"])

    # prevent overlapping of elements and show the plot
    plotter.tight_layout()

    plotter.show()
    #plotter.savefig("loss.pdf")

