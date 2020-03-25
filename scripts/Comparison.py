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


def do_calculation(resultDir, facet):
    directories = glob.glob(resultDir + "RESULTS*", recursive=True)

    data = pd.DataFrame()

    for foldername in directories:
        setting = Setting(foldername)
        settingData = pd.read_csv(foldername + "/testvalues.csv", sep='\t')
        heading = ""
        if facet is EvaluationAttribute.TRACE:
            heading = setting.trace
        elif facet is EvaluationAttribute.PROTOCOL:
            heading = setting.protocol
        elif facet is EvaluationAttribute.TOPOLOGY:
            heading = setting.topology
        data[heading] = settingData["syncLatencies"]

    fig, ax = plt.subplots()
    ax.set_title(str(facet))

    boxplotData = []
    labels = []
    for col in data.columns:
        boxplotData.append(data[col])
        labels.append(col)
    ax.boxplot(boxplotData, showfliers=False)

    plt.xticks(range(1, len(boxplotData) + 1), labels)

    plt.savefig("test.pdf")

    print(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--result-dir', dest='resultDir', default="/tmp/")
    parser.add_argument('--facetingField', dest='facetingField', type=EvaluationAttribute.from_string,
                        choices=list(EvaluationAttribute), default=EvaluationAttribute.TRACE)

    args = parser.parse_args()
    resultDir = args.resultDir
    facetingField = args.facetingField

    do_calculation(resultDir, facetingField)
