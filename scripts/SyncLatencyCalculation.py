import argparse
import pandas as pd
import glob
from tqdm import tqdm
import sys
import os
import numpy as np
import matplotlib.pyplot as plt


def do_calculation(resultDir):
    logfiles = glob.glob(resultDir + "/**/*_chunklog.csv", recursive=True)
    logs = [('Server_' + x.split('/')[-1].replace("__", "_").split('_')[-2].replace('.csv', ''), x) for x in logfiles]

    # Check if sync latencies csv already exists
    folderName = resultDir.split("/")[-1]
    if folderName == "":
        folderName = resultDir.split("/")[-2]
    csv_filename = resultDir + "/" + folderName + '.csv'
    syncLatencies = None

    if not os.path.isfile(csv_filename):

        ######## Calculate Sync Latencies of all updates ########
        #

        print("Calculate Sync Latencies for all updates")

        columns = ['chunk_x', 'chunk_y', 'version', 'producer', 'produced_at', 'update_size']

        chunk_produced_map = {}
        chunk_arrvied_at_server_map = {}
        for (server, file) in logs:
            columns.append("arrived_at_" + server)
            columns.append("sync_latency_" + server)
            chunk_arrvied_at_server_map[server] = {}
        syncLatencies = pd.DataFrame(columns=columns)

        for (server, file) in logs:
            log = pd.read_csv(file, sep='\t', header=None, names=["time", "type", "x", "y", "v", "update_size"])
            # log = log.dropna(subset=['time'])
            print("Processing CSV file of server " + server)

            for index, row in tqdm(log.iterrows(), total=len(log), desc=server):
                # The fields time,x,y,v most be integers, otherwise the entry is not valid
                try:
                    _ = (int(row['x']), int(row['y']), int(row['v']), int(row['time']))
                except ValueError:
                    print("Row not complete:\n" + str(row))
                    continue

                key = sys.intern(str(int(row['x'])) + '_' + str(int(row['y'])) + '_' + str(int(row['v'])))
                #if server == "Server_15":
                #    print((key, row))
                if row['type'] == 'OUT':
                    try:
                        chunk_produced_map[key] = (int(row['time']), server, int(row['update_size']))
                    except ValueError:
                        print("Row not complete:\n" + str(row))
                        continue
                elif row['type'] == 'IN':
                    chunk_arrvied_at_server_map[server][key] = int(row['time'])

        rows = []
        for chunk, (timestamp, server, update_size) in tqdm(chunk_produced_map.items(), total=len(chunk_produced_map),
                                                            desc="Calculating latencies"):
            cd = chunk.split('_')
            x = int(cd[0])
            y = int(cd[1])
            v = int(cd[2])
            entry = {'chunk_x': x,
                     'chunk_y': y,
                     'version': v,
                     'producer': server,
                     'produced_at': timestamp,
                     'update_size': update_size}
            for (r_server, file) in logs:
                if chunk in chunk_arrvied_at_server_map[r_server]:
                    arrived_time = chunk_arrvied_at_server_map[r_server][chunk]
                    sync_latency = arrived_time - timestamp
                    entry["arrived_at_" + r_server] = arrived_time
                    entry["sync_latency_" + r_server] = sync_latency
                elif server != r_server:
                    # Try to find the next higher version for the chunk
                    for version in range(v, v + 100):
                        id = str(x) + '_' + str(y) + '_' + str(version)
                        if id in chunk_arrvied_at_server_map[r_server]:
                            if version - v > 10:
                                print("Version found after skipping {} entries".format(version - v))
                            arrived_time = chunk_arrvied_at_server_map[r_server][id]
                            sync_latency = arrived_time - timestamp
                            entry["arrived_at_" + r_server] = arrived_time
                            entry["sync_latency_" + r_server] = sync_latency
                            break

            rows.append(entry)
            # syncLatencies = syncLatencies.append(entry, ignore_index=True)
        syncLatencies = pd.DataFrame(rows, columns=columns)

        def _max_sync_latency(row, servers):
            values = []
            for server in servers:
                val = float(row["sync_latency_" + server])
                if val > 0.0: # Skip NaN values
                    values.append(val)
            return max(values)

        servers = [log[0] for log in logs]
        syncLatencies["syncLatency"] = syncLatencies.apply(lambda x: _max_sync_latency(x, servers), axis=1)

        syncLatencies = syncLatencies.sort_values('produced_at')

        print("Saving syncLatencies to: " + csv_filename)
        syncLatencies.to_csv(csv_filename, sep="\t", index=False)

    else:
        print("CSV file with sync latencies already exists, skip this step")
        syncLatencies = pd.read_csv(csv_filename, sep="\t")

    ######## Calculate lost updates, convergence times ########
    #

    summary = None
    if not os.path.isfile(resultDir + '/summary.csv'):

        servers = [log[0] for log in logs]
        updates_received = {server: 0 for server in servers}
        updates_missing = {server: 0 for server in servers}
        updates_latencies = {server: 0 for server in servers}

        for index, row in tqdm(syncLatencies.iterrows(), total=len(syncLatencies), desc="Calculating sync latencies"):
            producer = row["producer"]
            for server in servers:
                if server == producer:
                    continue
                if float(row["sync_latency_" + server]) > 0:
                    updates_received[server] += 1
                    updates_latencies[server] += float(row["sync_latency_" + server])
                else:
                    updates_missing[server] += 1
        for server in updates_latencies:
            if updates_received[server] == 0:
                updates_latencies[server] = float("NaN")
            else:
                updates_latencies[server] = updates_latencies[server] / updates_received[server]
        summay_cols = ['server', 'received', 'lost', 'avg_latency']
        summary_rows = []
        for server in servers:
            row = {
                'server': server,
                'received': updates_received[server],
                'lost': updates_missing[server],
                'avg_latency': updates_latencies[server]
            }
            summary_rows.append(row)
        summary = pd.DataFrame(summary_rows, columns=summay_cols)
        summary.to_csv(resultDir + '/summary.csv', sep="\t", index=False)
    else:
        print("Summary.csv already exists, skip calculation")
        summary = pd.read_csv(resultDir + '/summary.csv', sep="\t")

    ############ Draw figures ############
    plt.figure()
    boxplot = syncLatencies.boxplot(column=['syncLatency'], showfliers=False)
    plt.savefig(resultDir + '/convergence-time.png')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--result-dir', dest='resultDir', default="/tmp/")

    args = parser.parse_args()
    resultDir = args.resultDir

    do_calculation(resultDir=resultDir)
