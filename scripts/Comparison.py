import argparse
import pandas as pd
import glob
from tqdm import tqdm
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from enum import Enum


class EvaluationAttribute(Enum):
    TOPOLOGY = 1
    PROTOCOL = 2
    TRACE = 3

    def __str__(self):
        return self.name

    @staticmethod
    def from_string(s):
        try:
            return EvaluationAttribute[s]
        except KeyError:
            raise ValueError()


class Setting:

    def __init__(self, folderName):
        self.folderName = folderName
        folderName = folderName.split("/")[-1]
        folderName = folderName.split("_")
        self.servers = int(folderName[1])
        self.topology = folderName[2]
        self.protocol = folderName[3]
        self.runNo = int(folderName[4].replace("run", ""))
        self.trace = folderName[5]

    def __str__(self):
        return "#Servers: {}, Topology: {}, Protocol: {}, RUN: {}, Trace: {}".format(self.servers, self.topology,
                                                                                     self.protocol, self.runNo,
                                                                                     self.trace)


def do_calculation(resultDir, facet, traceFilter, sizeFilter, protocolFilter, topoFilter):
    directories = glob.glob(resultDir + "/RESULTS*", recursive=True)

    data = pd.DataFrame()

    for foldername in directories:
        setting = Setting(foldername)
        if len(glob.glob(foldername + "/RESULTS*.csv")) == 0:
            continue
        csvFile = glob.glob(foldername + "/RESULTS*.csv")[0]
        print(setting)

        if topoFilter != None and setting.topology != topoFilter:
            continue
        if traceFilter != None and setting.trace != traceFilter:
            continue
        if sizeFilter != None and setting.servers != sizeFilter:
            continue
        if protocolFilter != None and setting.protocol != protocolFilter:
            continue
        if setting.runNo != 0:
            continue

        heading = ""
        if facet is EvaluationAttribute.TRACE:
            heading = setting.trace
        elif facet is EvaluationAttribute.PROTOCOL:
            heading = setting.protocol
        elif facet is EvaluationAttribute.TOPOLOGY:
            heading = setting.topology
        settingData = pd.read_csv(csvFile, sep='\t')
        data[heading] = settingData["syncLatency"]

    fig, ax = plt.subplots()
    ax.set_title(str(facet))

    boxplotData = []
    labels = []
    for col in data.columns:
        filtered = data[col].to_numpy()
        filtered = filtered[~np.isnan(filtered)]
        print(filtered)
        boxplotData.append(filtered)
        labels.append(col)
    ax.boxplot(boxplotData, showfliers=False)

    plt.xticks(range(1, len(boxplotData) + 1), labels)

    plt.savefig(resultDir + "/test.pdf")

    print(data)

## Possible commands to use
# python3 ~/Coding/SyncProtocols/mini-ndn/scripts/Comparison.py --result-dir=$(pwd) --facetingField=PROTOCOL --sizeFilter=4 --topoFilter=continent --traceFilter=ChunkChanges-concentratedcsv
# python3 ~/Coding/SyncProtocols/mini-ndn/scripts/Comparison.py --result-dir=$(pwd) --facetingField=TRACE --protocolFilter=QuadTree --sizeFilter=4 --topoFilter=cluster

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--result-dir', dest='resultDir', default="/tmp/")
    parser.add_argument('--facetingField', dest='facetingField', type=EvaluationAttribute.from_string,
                        choices=list(EvaluationAttribute), default=EvaluationAttribute.TRACE)
    parser.add_argument('--protocolFilter', dest='protocolFilter', default=None)
    parser.add_argument('--sizeFilter', dest='sizeFilter', default=None, type=int)
    parser.add_argument('--traceFilter', dest='traceFilter', default=None)
    parser.add_argument('--topoFilter', dest='topoFilter', default=None)

    args = parser.parse_args()
    resultDir = args.resultDir
    facetingField = args.facetingField
    traceFilter = args.traceFilter
    sizeFilter = args.sizeFilter
    protocolFilter = args.protocolFilter
    topoFilter = args.topoFilter

    do_calculation(resultDir, facetingField, traceFilter, sizeFilter, protocolFilter, topoFilter)
