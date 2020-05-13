import numpy
import pandas
import argparse
import scipy.stats
import os
import matplotlib
import matplotlib.pyplot as plotter
from scripts.filefetcher import FileFetcher

matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
matplotlib.rcParams.update({'font.size': 15})

class Visualizer:

    def __init__(self, data, directory, compareP2P = False):
        """
        define the values of all possible filter criteria
        and assign a FileFetcher instance for
        getting the necessary data
        """
        self.data = data
        self.fileFetcher = FileFetcher(data, directory)
        self.compareP2P = compareP2P
        self.y_limits = []
        self.legendLabels = []
        self.legendHandles = []


        # responses can only be compared for P2P and QuadTree
        # --> set compareP2P = True
        if self.data == "responses":
            compareP2P = True

        if not(compareP2P) and self.data == "latencies":
            self.setSettings(3, [4, 16], ["cluster", "continent"],
                             ["QuadTree", "StateVector", "ZMQ"], ["concentrated", "very-distributed"])
        elif not(compareP2P):
            self.setSettings(6, [4, 16], ["cluster", "continent"], ["QuadTree", "StateVector", "ZMQ"],
                             ["concentrated", "very-distributed", "distributed"])
        elif compareP2P:
            self.setSettings(6, [16], ["cluster"], ["QuadTree", "P2P"],
                             ["concentrated", "very-distributed", "distributed"])
        self.files = []
        self.fetchAllFiles()
        self.transformationFactor = self.getTransformationFactor()
        self.labelDictionary = {
            'QuadTree': 'QSP',
            'StateVector': 'SVS',
            'ZMQ': 'ZMQ Pub-/Sub',
            'P2P': 'Region-based QSP',
            'cluster': 'Data Center',
            'continent': 'GEANT Topology',
            'concentrated': 'concentrated scenario',
            'distributed': 'widespread scenario',
            'very-distributed': 'max-distance scenario',
            'in': 'ingoing',
            'out': 'outgoing',
            '#interests': '(Interests)',
            'bytesInterests': '(Interests)',
            '#data': '(Data)',
            'bytesData': '(Data)',
            '#IPSyncPackets': '',
            'bytesIPSyncPackets': '',
            'received_chunk_responses' : 'Received Chunk Responses',
            'received_subtree_responses': 'Received Subtree Responses'
        }

    def setSettings(self, runNumber, serverNumbers, topologies, protocols, clientConcentrations):
        self.runNumber = runNumber
        self.serverNumbers = serverNumbers
        self.topologies = topologies
        self.protocols = protocols
        self.clientConcentrations = clientConcentrations

    def getTransformationFactor(self):
        if(self.data == "bytes" or self.data == "network" or self.data == "network-out"):
            return 1000*1000
        else:
            return 1000

    def fetchAllFiles(self):
        """
        fetch all csv-files which contain the data to analyze
        """
        for serverNumber in self.serverNumbers:
            for topology in self.topologies:
                for protocol in self.protocols:
                    for clientConcentration in self.clientConcentrations:
                        for i in range(self.runNumber):
                            if(self.data == "responses"):
                                for server in range(serverNumber):
                                    file = self.fileFetcher.getCSVFile(serverNumber, topology, protocol, i,
                                                                           clientConcentration, serverFolder = "s" + str(server))
                                    if(not(file.empty)):
                                        self.files.append(file)

                            else:
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
            elif self.data == "network-out":
                self.getValues(file.name, file[file['in/out'] == "out"], [protocol, barGroup, run] + filterCriteria, values)
            elif self.data == "responses":
                self.getValues(file.name, pandas.DataFrame(file[barGroup]), [protocol, run] + filterCriteria, values)
            elif self.data == "packets" or self.data == "bytes":
                # columnFilter[0] defines if we filter by 'in' or 'out'
                # columnFilter[1] defines the column-name
                frame = file[file['in/out'] == columnFilter[0]]
                #frame = {columnFilter[1]: file[columnFilter[1]]}
                self.getValues(file.name, frame, [protocol, barGroup, run] + filterCriteria, values, columnFilter[1])
            else:
                self.getValues(file.name, file, [protocol, barGroup, run] + filterCriteria, values)

        return numpy.mean(values)/self.transformationFactor

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



    def plotSimpleBarChart(self, axis, filterCriteria, barGroups, subplots = False,
                           alternativeLabel = None, makeSmaller = False):
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
        #legendlabels = []
        for barGroup in barGroups:
            labels.append(self.labelDictionary[barGroup])

        if(alternativeLabel == None):
            if(len(barGroups) <= 1 and not(self.data == 'responses' and subplots)):
                xlabel = self.buildLabel(filterCriteria + barGroups)
            elif(not(self.data == 'responses' and subplots)):
                xlabel = self.buildLabel(filterCriteria)
        else:
            xlabel = alternativeLabel

        # calculate the means + standard deviations per bar group
        # for each protocol ( #(means) = #(standard deviations) = #(barGroups) * #(protocols))
        for protocol in self.protocols:
            data = self.getProtocolData(protocol, filterCriteria, barGroups)
            means.append(data[0])
            stds.append(data[1])
            legendLabel = self.labelDictionary[protocol]
            if(not(legendLabel in self.legendLabels)):
                self.legendLabels.append(legendLabel)

        # define the starting position ( = position of first bar) for each bar group
        # as well as the width and color for the bars
        # if only one bar group is plotted, add a space of 0.1 between the bars
        x_pos = numpy.arange(len(barGroups))
        if(makeSmaller):
            width = 0.075
            axis.margins(0.3, None)
        else:
            width = 0.25

        space = 0
        if(len(barGroups) == 1):
            space = 0.1
        colors = [(1, 1, 1, 1), (0.6, 0.6, 0.6, 1), (0.2, 0.2, 0.2, 1)]


        # define the bars for each protocol we want to represent in the different bar groups
        bars = []
        #legend = []
        for i in range(len(self.protocols)):
            bar = self.getBar(axis, x_pos + i * (width+space), means[i], width, None, stds[i], "black", 10, colors[i], "black")
            bars.append(bar)
            legendHandle = bar[0]
            if(not(legendHandle in self.legendHandles)):
                self.legendHandles.append(legendHandle)

        # define the labels, legend and remove the ticks
        if(self.data == 'responses' and subplots):
            axis.set_xticks((x_pos + (space + width))/2)
        else:
            axis.set_xticks(x_pos + (space+width))
        axis.set_xticklabels(labels)

        if (len(barGroups) > 1 or (self.data == 'responses' and subplots)):
            self.removeTicks(axis, showLabel=True)
        else:
            self.removeTicks(axis, showLabel=False)

        # set the labels according to the data we analyzed
        if(self.data == 'latencies'):
            ylabel = "Sync Latencies"
        elif(self.data == "network"):
            ylabel = "Bytes of Sync Payload"
        elif (self.data == "network-out"):
            ylabel = "Outgoing Sync Payload"
        elif(self.data == "responses"):
            ylabel = "Received Responses"
        else:
            ylabel = "Lost Data"

        #axis.legend(legend, legendlabels)

        if(self.transformationFactor == 1000):
            ylabel += (" [k]")
        else:
            ylabel += (" [MB]")
        axis.set_ylabel(ylabel)
        axis.ticklabel_format(style='plain', axis='y', scilimits=(0, 0))
        if(not(self.data == 'responses' and subplots)):
            axis.set_xlabel(xlabel)

        # show a grid along the y-axis and put it behind the bars
        axis.set_axisbelow(True)
        axis.yaxis.grid(True)

        # get maximum y-value
        for i in range(len(means)):
            for j in range(len(means[i])):
                for i2 in range(len(means)):
                    self.y_limits.append(numpy.sum([means[i2][j], stds[i2][j]]))


    def plotStackedBarChart(self, axis, filterCriteria, barGroups,
                            alternativeLabel = None, makeSmaller = False):
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
            labels.append(self.labelDictionary[barGroup])

        if(alternativeLabel == None):
            if (len(barGroups) <= 1):
                xlabel = self.buildLabel(filterCriteria + barGroups)
            else:
                xlabel = self.buildLabel(filterCriteria)
        else:
            xlabel = alternativeLabel

        if self.data == "packets":
            columnFilters = {
                'QuadTree': [["out", "#data"], ["in", "#interests"]],
                'P2P': [["out", "#data"], ["in", "#interests"]],
                'StateVector': [["out", "#data"], ["in", "#interests"]],
                'ZMQ': [["out", "#IPSyncPackets"]]}
        else:
            columnFilters = {
                'QuadTree': [["out", "bytesData"], ["in", "bytesInterests"]],
                'P2P': [["out", "bytesData"], ["in", "bytesInterests"]],
                'StateVector': [["out", "bytesData"], ["in", "bytesInterests"]],
                'ZMQ': [["out", "bytesIPSyncPackets"]]}

        for protocol in self.protocols:
            columnmeans = []
            for columnFilter in columnFilters[protocol]:
                data = self.getProtocolData(protocol, filterCriteria, barGroups, columnFilter)
                columnmeans.append(data[0])
            means.append(columnmeans)


        # define the starting position ( = position of first bar) for each bar group
        # as well as the width and color for the bars
        # if only one bar group is plotted, add a space of 0.1 between the bars
        x_pos = numpy.arange(len(barGroups))
        if (makeSmaller):
            width = 0.075
            axis.margins(0.3, None)
        else:
            width = 0.25
        space = 0
        if (len(barGroups) == 1):
            space = 0.1
        colors = [(1, 1, 1, 1), (0.6, 0.6, 0.6, 1), (0.2, 0.2, 0.2, 1)]

        # define the bars for each protocol we want to represent in the different bar groups
        bars = []
        i = 0
        for protocol in self.protocols:
            for j in range(len(columnFilters[protocol])):
                if(j > 0):
                    bar = self.getBar(axis, x_pos + i*(width + space), means[i][j], width, means[i][j-1],
                                      None, None, 10, colors[i], "black", "//")
                else:
                    bar = self.getBar(axis, x_pos + i * (width + space), means[i][j], width, 0, None,
                                      None, 10, colors[i], "black", )
                bars.append(bar)
                legendHandle = bar[0]
                legendLable = "%s %s" % (self.labelDictionary[protocol],
                                         self.labelDictionary[columnFilters[protocol][j][1]])
                if(not(legendLable in self.legendLabels)):
                    self.legendLabels.append(legendLable)
                    self.legendHandles.append(legendHandle)
            i += 1

        # define the labels, legend and remove the ticks
        axis.set_xticks(x_pos + (space+width))
        axis.set_xticklabels(labels)

        if (len(barGroups) > 1):
            self.removeTicks(axis, showLabel=True)
        else:
            self.removeTicks(axis, showLabel=False)

        # set the labels according to the data we analyzed
        if self.data == "packets":
            ylabel = "Number of Sent Packets"
        else:
            ylabel = "Amount of Sent Bytes"

        if (self.transformationFactor == 1000):
            ylabel += (" [k]")
        else:
            ylabel += (" [MB]")
        axis.set_ylabel(ylabel)
        axis.ticklabel_format(style='plain', axis='y', scilimits=(0, 0))
        axis.set_xlabel(xlabel)

        # show a grid along the y-axis and put it behind the bars
        axis.set_axisbelow(True)
        axis.yaxis.grid(True)

        # get maximum y-value
        stacked_y_limits = []
        # for every protocol
        for i in range(len(means)):
            #for every data
            for j in range(len(means[i])):
                #for every barGroup
                for k in range(len(means[i][j])):
                    for j2 in range(len(means[i])):
                        stacked_y_limits.append(means[i][j2][k])

                    self.y_limits.append(numpy.sum(stacked_y_limits))
                    stacked_y_limits.clear()


    def getBar(self, axis, position, mean, width, bottom, error, errorcolor, capsize, color, edgecolor, hatch=None):
        """
        return a bar, defined by the given parameters
        """
        return axis.bar(position, mean, width, bottom=bottom, yerr=error, ecolor=errorcolor, capsize=capsize, color=color, edgecolor=edgecolor, hatch=hatch)

    def removeTicks(self, axis, showLabel):
        """
        remove the ticks along the x-axis, and show a label if necessary
        """
        axis.tick_params(
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
                concentrationLevel = self.labelDictionary[criterion]
                label += concentrationLevel

            # if the criterion is a topology do not put a space in front of
            # it, if it is the first criterion used in the label
            elif criterion in self.topologies:
                if i > 0:
                    label += " "
                label += "in a %s" %self.labelDictionary[criterion]

            # if the current criterion is not the last one --> add 'and' to label
            # do not add 'and' if the current criterion is the first one
            # and it is also a topology, use 'with' instead
            # example: "cluster with 16 servers.....", instead of "cluster and 16 servers...."
            if i < (len(filterCriteria)-1) and not(filterCriteria[i+1] in self.topologies)\
                    and not(criterion in self.topologies and i == 0):
                label += ", "
            elif i < (len(filterCriteria)-1) and not(filterCriteria[i+1] in self.topologies)\
                    and (criterion in self.topologies and i == 0):
                label += ", "

        return label

    def setMaxY(self, axes, rows, columns):
        axes = numpy.array(axes)
        y_limit = max(self.y_limits) * 1.1
        if(1 in [rows, columns] and rows!=columns):
            for index in range(columns):
                axes[index].set_ylim(top=y_limit, bottom=0)
        else:
            for i in range(rows):
                for j in range(columns):
                    axes[i][j].set_ylim(top=y_limit, bottom=0)

    def prependYAxisLabel(self, axis, prependLabel):
        newLabel = prependLabel + axis.get_ylabel()
        axis.set_ylabel(newLabel)

    def setLabelPerRow(self, axes, rows, columns):
        if (1 in [rows, columns] and rows != columns):
            for index in range(columns):
                if(columns > 1 and index > 0):
                    axes[index].set_ylabel("")
        else:
            for i in range(rows):
                for j in range(columns):
                    if (j > 0):
                        axes[i][j].set_ylabel("")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-r", "--result-dir", help="Directory containing the result dirs of the runs",
                        default="../result-csv-files_6runs")
    parser.add_argument("-o", "--output-dir", help="Directory for resulting figures",
                        default="../plot-results/")
    args = parser.parse_args()

    csvDirectory = args.result_dir
    outputDirectory = args.output_dir
    if not os.path.isdir(outputDirectory):
        os.makedirs(outputDirectory)

    #visualize bytes
    '''visualizer = Visualizer("bytes", csvDirectory)
    figure, axes = plotter.subplots(nrows=2, ncols=2)
    figure.set_size_inches(15, 10)
    visualizer.plotStackedBarChart(axes[0, 0], ["16", "very-distributed"], ["cluster", "continent"])
    visualizer.plotStackedBarChart(axes[0, 1], ["16", "concentrated"], ["cluster", "continent"])
    visualizer.plotStackedBarChart(axes[1, 0], ["4", "very-distributed"], ["cluster", "continent"])
    visualizer.plotStackedBarChart(axes[1, 1], ["4", "concentrated"], ["cluster", "continent"])
    visualizer.setMaxY(axes, 2, 2)
    visualizer.setLabelPerRow(axes, 2, 2)
    legend = figure.legend(bbox_to_anchor=(0.5, 0), loc='lower center', ncol=2,
                  labels=visualizer.legendLabels, handles=visualizer.legendHandles, frameon=False, fontsize='large')
    figure.tight_layout()
    figure.subplots_adjust(bottom=0.15)
    plotter.savefig("{}/allProtocols_bytes.pdf".format(outputDirectory))
    print("{}/allProtocols_bytes.pdf".format(outputDirectory))


    #visualize summary
    visualizer = Visualizer("summary", csvDirectory)
    figure, axes = plotter.subplots(nrows=2, ncols=3)
    figure.set_size_inches(15, 7)
    visualizer.plotSimpleBarChart(axes[0, 0], ["16", "very-distributed"], ["cluster", "continent"])
    visualizer.plotSimpleBarChart(axes[0, 1], ["16", "distributed"], ["cluster", "continent"])
    visualizer.plotSimpleBarChart(axes[0, 2], ["16", "concentrated"], ["cluster", "continent"])
    visualizer.plotSimpleBarChart(axes[1, 0], ["4", "very-distributed"], ["cluster", "continent"])
    visualizer.plotSimpleBarChart(axes[1, 1], ["4", "distributed"], ["cluster", "continent"])
    visualizer.plotSimpleBarChart(axes[1, 2], ["4", "concentrated"], ["cluster", "continent"])
    visualizer.setMaxY(axes, 2, 3)
    visualizer.setLabelPerRow(axes, 2, 3)
    figure.legend(bbox_to_anchor=(0.5, 0), loc='lower center', ncol=3,
                  labels=visualizer.legendLabels, handles=visualizer.legendHandles, frameon=False, fontsize='large')
    figure.tight_layout()
    figure.subplots_adjust(bottom=0.15)
    plotter.savefig("{}/allProtocols_loss.pdf".format(outputDirectory))
    print("{}/allProtocols_loss.pdf".format(outputDirectory))

    #visualize in/out network-traffic
    visualizer = Visualizer("network", csvDirectory)
    figure, axis = plotter.subplots()
    visualizer.plotSimpleBarChart(axis, ["16", "very-distributed", "cluster"], ["in", "out"])
    axis.set_ylim(bottom=0)
    figure.legend(bbox_to_anchor=(0.5, 0), loc='lower center', ncol=len(visualizer.legendLabels),
                  labels=visualizer.legendLabels, handles=visualizer.legendHandles, frameon=False, fontsize='large')
    figure.tight_layout()
    figure.subplots_adjust(bottom=0.2)
    plotter.savefig("{}/allProtocols_network_in_out.pdf".format(outputDirectory))
    print("{}/allProtocols_network_in_out.pdf".format(outputDirectory))

    #visualize sync latencies
    visualizer = Visualizer("latencies", csvDirectory)
    figure, axis = plotter.subplots()
    visualizer.plotSimpleBarChart(axis, ["16", "very-distributed"], ["continent", "cluster"])
    axis.set_ylim(bottom=0)
    figure.legend(bbox_to_anchor=(0.5, 0), loc='lower center', ncol=len(visualizer.legendLabels),
                  labels=visualizer.legendLabels, handles=visualizer.legendHandles, frameon=False, fontsize='large')
    figure.tight_layout()
    figure.subplots_adjust(bottom=0.2)
    plotter.savefig("{}/allProtocols_latencies.pdf".format(outputDirectory))
    print("{}/allProtocols_latencies.pdf".format(outputDirectory))

    # visualize summary: P2P vs. QuadTree
    visualizer = Visualizer("summary", csvDirectory, compareP2P=True)
    figure, axes = plotter.subplots(nrows=1, ncols=3)
    figure.set_size_inches(15,7)
    visualizer.plotSimpleBarChart(axes[0], ["16", "concentrated"], ["cluster"], makeSmaller=True)
    visualizer.plotSimpleBarChart(axes[1], ["16", "distributed"], ["cluster"], makeSmaller=True)
    visualizer.plotSimpleBarChart(axes[2], ["16", "very-distributed"], ["cluster"], makeSmaller=True)
    visualizer.setMaxY(axes, 1, 3)
    visualizer.setLabelPerRow(axes, 1, 3)
    figure.legend(bbox_to_anchor=(0.5, 0), loc='lower center', ncol=2,
                  labels=visualizer.legendLabels, handles=visualizer.legendHandles, frameon=False, fontsize='large')
    figure.tight_layout()
    figure.subplots_adjust(bottom=0.15)
    plotter.savefig("{}/p2p_loss.pdf".format(outputDirectory))
    print("{}/p2p_loss.pdf".format(outputDirectory))

    # visualize network traffic in/out: P2P vs. QuadTree
    visualizer = Visualizer("network", csvDirectory, compareP2P=True)
    figure, axes = plotter.subplots(nrows=1, ncols=3)
    figure.set_size_inches(15,7)
    visualizer.plotSimpleBarChart(axes[0], ["16", "concentrated", "cluster"], ["in", "out"])
    visualizer.plotSimpleBarChart(axes[1], ["16", "distributed", "cluster"], ["in", "out"])
    visualizer.plotSimpleBarChart(axes[2], ["16", "very-distributed", "cluster"], ["in", "out"])
    visualizer.setMaxY(axes, 1, 3)
    visualizer.setLabelPerRow(axes, 1, 3)
    figure.legend(bbox_to_anchor=(0.5, 0), loc='lower center', ncol=2,
                  labels=visualizer.legendLabels, handles=visualizer.legendHandles, frameon=False, fontsize='large')
    figure.tight_layout()
    figure.subplots_adjust(bottom=0.2)
    plotter.savefig("{}/p2p_network_in_out.pdf".format(outputDirectory))
    print("{}/p2p_network_in_out.pdf".format(outputDirectory))

    # visualize packets: P2P vs. QuadTree
    visualizer = Visualizer("packets", csvDirectory, compareP2P=True)
    figure, axes = plotter.subplots(nrows=1, ncols=3)
    figure.set_size_inches(15,7)
    visualizer.plotStackedBarChart(axes[0], ["16", "concentrated"], ["cluster"], makeSmaller=True)
    visualizer.plotStackedBarChart(axes[1], ["16", "distributed"], ["cluster"], makeSmaller=True)
    visualizer.plotStackedBarChart(axes[2], ["16", "very-distributed"], ["cluster"],makeSmaller=True)
    visualizer.setMaxY(axes, 1, 3)
    visualizer.setLabelPerRow(axes, 1, 3)
    figure.legend(bbox_to_anchor=(0.5, 0), loc='lower center', ncol=2,
                  labels=visualizer.legendLabels, handles=visualizer.legendHandles, frameon=False, fontsize='large')
    figure.tight_layout()
    figure.subplots_adjust(bottom=0.2)
    plotter.savefig("{}/p2p_packets.pdf".format(outputDirectory))
    print("{}/p2p_packets.pdf".format(outputDirectory))

    # visualize summary: P2P vs. QuadTree
    visualizer = Visualizer("bytes", csvDirectory, compareP2P=True)
    figure, axes = plotter.subplots(nrows=1, ncols=3)
    figure.set_size_inches(15,7)
    visualizer.plotStackedBarChart(axes[0], ["16", "concentrated"], ["cluster"], makeSmaller=True)
    visualizer.plotStackedBarChart(axes[1], ["16", "distributed"], ["cluster"], makeSmaller=True)
    visualizer.plotStackedBarChart(axes[2], ["16", "very-distributed"], ["cluster"], makeSmaller=True)
    visualizer.setMaxY(axes, 1, 3)
    visualizer.setLabelPerRow(axes, 1, 3)
    figure.legend(bbox_to_anchor=(0.5, 0), loc='lower center', ncol=2,
                  labels=visualizer.legendLabels, handles=visualizer.legendHandles, frameon=False, fontsize='large')
    figure.tight_layout()
    figure.subplots_adjust(bottom=0.2)
    plotter.savefig("{}/p2p_bytes.pdf".format(outputDirectory))
    print("{}/p2p_bytes.pdf".format(outputDirectory))

    # visualize responses in P2P vs. QuadTree in one plot
    visualizer = Visualizer("responses", csvDirectory)
    figure, axis = plotter.subplots()
    visualizer.plotSimpleBarChart(axis, ["16", "cluster", 'concentrated'],
                                  ["received_chunk_responses", "received_subtree_responses"])
    axis.set_ylim(bottom=0)
    figure.legend(bbox_to_anchor=(0.5, 0), loc='lower center', ncol=len(visualizer.legendLabels),
                  labels=visualizer.legendLabels, handles=visualizer.legendHandles, frameon=False, fontsize='large')
    figure.tight_layout()
    figure.subplots_adjust(bottom=0.2)
    plotter.savefig("{}/p2p_responses.pdf".format(outputDirectory))
    print("{}/p2p_responses.pdf".format(outputDirectory))

    # visualize responses in P2P vs. QuadTree with subplots
    visualizer = Visualizer("responses", csvDirectory)
    figure, axes = plotter.subplots(nrows=1, ncols=2)
    figure.set_size_inches(10, 7)
    visualizer.plotSimpleBarChart(axes[0], ["16", "cluster", "concentrated"], ["received_chunk_responses"], subplots = True, makeSmaller=True)
    visualizer.plotSimpleBarChart(axes[1], ["16", "cluster", "concentrated"], ["received_subtree_responses"], subplots = True, makeSmaller=True)
    visualizer.setLabelPerRow(axes, 1, 2)
    figure.legend(bbox_to_anchor=(0.5, 0), loc='lower center', ncol=len(visualizer.legendLabels),
                  labels=visualizer.legendLabels, handles=visualizer.legendHandles, frameon=False, fontsize='large')
    figure.suptitle(visualizer.buildLabel(["16", "cluster", "concentrated"]), y=0.1)
    figure.tight_layout()
    figure.subplots_adjust(bottom=0.15)
    plotter.savefig("{}/p2p_responses_subplots.pdf".format(outputDirectory))
    print("{}/p2p_responses_subplots.pdf".format(outputDirectory))

    # visualize network-out in P2P vs. QuadTree with subplots
    visualizer = Visualizer("network-out", csvDirectory, compareP2P=True)
    figure, axes = plotter.subplots(nrows=1, ncols=3)
    figure.set_size_inches(15, 7)
    visualizer.plotSimpleBarChart(axes[0], ["16","cluster"], ["concentrated"], makeSmaller=True)
    visualizer.plotSimpleBarChart(axes[1], ["16", "cluster"], ["distributed"], makeSmaller=True)
    visualizer.plotSimpleBarChart(axes[2], ["16", "cluster"], ["very-distributed"], makeSmaller=True)
    visualizer.setMaxY(axes, 1, 3)
    visualizer.setLabelPerRow(axes, 1, 3)
    figure.legend(bbox_to_anchor=(0.5, 0), loc='lower center', ncol=2,
                  labels=visualizer.legendLabels, handles=visualizer.legendHandles, frameon=False, fontsize='large')
    figure.tight_layout()
    figure.subplots_adjust(bottom=0.15)
    plotter.savefig("{}/p2p_network_out.pdf".format(outputDirectory))
    print("{}/p2p_network_out.pdf".format(outputDirectory))'''

    # visualize network-out in P2P vs. QuadTree with subplots
    visualizer = Visualizer("bytes", csvDirectory, compareP2P=True)
    figure, axes = plotter.subplots(nrows=2, ncols=3)
    figure.set_size_inches(15, 10)
    visualizer.plotStackedBarChart(axes[0][0], ["16", "cluster"], ["concentrated"], makeSmaller=True, alternativeLabel="concentrated scenario")
    visualizer.plotStackedBarChart(axes[0][1], ["16", "cluster"], ["distributed"], makeSmaller=True, alternativeLabel="widespread scenario")
    visualizer.plotStackedBarChart(axes[0][2], ["16", "cluster"], ["very-distributed"], makeSmaller=True, alternativeLabel="max-distance scenario")
    first_y_limits = visualizer.y_limits
    visualizer = Visualizer("packets", csvDirectory, compareP2P=True)
    visualizer.plotStackedBarChart(axes[1][0], ["16", "cluster"], ["concentrated"], makeSmaller=True, alternativeLabel="concentrated scenario")
    visualizer.plotStackedBarChart(axes[1][1], ["16", "cluster"], ["distributed"], makeSmaller=True, alternativeLabel="widespread scenario")
    visualizer.plotStackedBarChart(axes[1][2], ["16", "cluster"], ["very-distributed"], makeSmaller=True, alternativeLabel="max-distance scenario")
    visualizer.y_limits += first_y_limits
    visualizer.setMaxY(axes, 2, 3)
    axes[0, 0].set_ylim(top=7, bottom=0)
    axes[0, 1].set_ylim(top=7, bottom=0)
    axes[0, 2].set_ylim(top=7, bottom=0)
    figure.legend(bbox_to_anchor=(0.5, 0), loc='lower center', ncol=2,
                  labels=visualizer.legendLabels, handles=visualizer.legendHandles, frameon=False, fontsize='large')
    #visualizer.prependYAxisLabel(axes[0, 0], "Amount of Sent Bytes\n\n")
    #visualizer.prependYAxisLabel(axes[1, 0], "Number of Sent Packets\n\n")
    visualizer.setLabelPerRow(axes, 2, 3)
    figure.tight_layout(pad=3.0)
    figure.subplots_adjust(bottom=0.2)
    plotter.savefig("{}/p2p_bytes_vs_packets.pdf".format(outputDirectory))
    print("{}/p2p_bytes_vs_packets.pdf".format(outputDirectory))

    # visualize outgoing network traffic
    visualizer = Visualizer("network-out", csvDirectory)
    figure, axes = plotter.subplots(nrows=2, ncols=3)
    figure.set_size_inches(20, 10)
    visualizer.plotSimpleBarChart(axes[0][0], ["4", "concentrated"], ["cluster", "continent"], alternativeLabel="concentrated scenario")
    visualizer.plotSimpleBarChart(axes[0][1], ["4", "distributed"], ["cluster", "continent"], alternativeLabel="widespread scenario")
    visualizer.plotSimpleBarChart(axes[0][2], ["4", "very-distributed"], ["cluster", "continent"], alternativeLabel="max-distance scenario")
    visualizer.plotSimpleBarChart(axes[1][0], ["16", "concentrated"], ["cluster", "continent"], alternativeLabel="concentrated scenario")
    visualizer.plotSimpleBarChart(axes[1][1], ["16", "distributed"], ["cluster", "continent"], alternativeLabel="widespread scenario")
    visualizer.plotSimpleBarChart(axes[1][2], ["16", "very-distributed"], ["cluster", "continent"], alternativeLabel="max-distance scenario")
    visualizer.setMaxY(axes, 2, 3)
    visualizer.setLabelPerRow(axes, 2, 3)
    visualizer.prependYAxisLabel(axes[0, 0], "4 Servers\n\n")
    visualizer.prependYAxisLabel(axes[1, 0], "16 Servers\n\n")
    figure.legend(bbox_to_anchor=(0.5, 0), loc='lower center', ncol=3,
                  labels=visualizer.legendLabels, handles=visualizer.legendHandles, frameon=False, fontsize='large')
    figure.tight_layout(pad=3.0)
    figure.subplots_adjust(bottom=0.2)
    plotter.savefig("{}/allProtocols_network_out.pdf".format(outputDirectory))
    print("{}/allProtocols_network_out.pdf".format(outputDirectory))


    # visualize packets
    visualizer = Visualizer("packets", csvDirectory)
    figure, axes = plotter.subplots(nrows=2, ncols=3)
    figure.set_size_inches(15, 10)
    visualizer.plotStackedBarChart(axes[0, 0], ["4", "concentrated"], ["cluster", "continent"], alternativeLabel="concentrated scenario")
    visualizer.plotStackedBarChart(axes[0, 1], ["4", "distributed"], ["cluster", "continent"], alternativeLabel="widespread scenario")
    visualizer.plotStackedBarChart(axes[0, 2], ["4", "very-distributed"], ["cluster", "continent"], alternativeLabel="max-distance scenario")
    visualizer.plotStackedBarChart(axes[1, 0], ["16", "concentrated"], ["cluster", "continent"], alternativeLabel="concentrated scenario")
    visualizer.plotStackedBarChart(axes[1, 1], ["16", "distributed"], ["cluster", "continent"], alternativeLabel="widespread scenario")
    visualizer.plotStackedBarChart(axes[1, 2], ["16", "very-distributed"], ["cluster", "continent"], alternativeLabel="max-distance scenario")
    visualizer.setMaxY(axes, 2, 3)
    visualizer.prependYAxisLabel(axes[0, 0], "4 Servers\n\n")
    visualizer.prependYAxisLabel(axes[1, 0], "16 Servers\n\n")
    visualizer.setLabelPerRow(axes, 2, 3)
    legend = figure.legend(bbox_to_anchor=(0.5, 0), loc='lower center', ncol=3,
                  labels=visualizer.legendLabels, handles=visualizer.legendHandles, frameon=False, fontsize='large')
    figure.tight_layout(pad=3.0)
    figure.subplots_adjust(bottom=0.2)
    plotter.savefig("{}/allProtocols_packets.pdf".format(outputDirectory))
    print("{}/allProtocols_packets.pdf".format(outputDirectory))