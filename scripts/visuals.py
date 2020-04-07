import numpy
import matplotlib.pyplot as plotter
import csv
from scripts.filefetcher import FileFetcher
if __name__ == "__main__":
    sync_latencies = []
    time = []
    fileFetcher = FileFetcher("../result-csv-files")
    csvfile = fileFetcher.getCSVFile(4, "cluster", "QuadTree", 0, "concentrated")

    rows = csv.reader(csvfile, delimiter='\t')
    i = 0;
    for row in rows:
        sync_latencies.append(row[len(row)-1])
        time.append(i)
        i += 1
    plotter.plot(time,sync_latencies, label="Sync Latencies")
    plotter.xlabel("Time")
    plotter.ylabel("Sync Latency")
    plotter.title("Sync Latencies")
    plotter.legend()
    plotter.show()
    csvfile.close()


