import argparse
import pandas as pd
import glob
from tqdm import tqdm
import sys


def do_calculation(resultDir):
    logfiles = glob.glob(resultDir + "/**/*_chunklog.csv", recursive=True)

    logs = [('Server_' + x.split('/')[-1].split('_')[-2].replace('.csv', ''), x) for x in logfiles]
    columns = ['chunk_x', 'chunk_y', 'version', 'producer', 'produced_at']

    chunk_produced_map = {}
    chunk_arrvied_at_server_map = {}
    for (server, file) in logs:
        columns.append("arrived_at_" + server)
        columns.append("sync_latency_" + server)
        chunk_arrvied_at_server_map[server] = {}
    syncLatencies = pd.DataFrame(columns=columns)

    for (server, file) in logs:
        log = pd.read_csv(file, sep='\t', header=None, names=["time", "type", "x", "y", "v"])
        # log = log.dropna(subset=['time'])
        print("Processing CSV file of server " + server)

        for index, row in tqdm(log.iterrows(), total=len(log), desc=server):
            key = sys.intern(str(row['x']) + '_' + str(row['y']) + '_' + str(row['v']))
            if row['type'] == 'OUT':
                chunk_produced_map[key] = (int(row['time']), server)
            elif row['type'] == 'IN':
                chunk_arrvied_at_server_map[server][key] = int(row['time'])

    rows = []
    for chunk, (timestamp, server) in tqdm(chunk_produced_map.items(), total=len(chunk_produced_map),
                                           desc="Calculating latencies"):
        cd = chunk.split('_')
        x = cd[0]
        y = cd[1]
        v = cd[2]
        entry = {'chunk_x': x,
                 'chunk_y': y,
                 'version': v,
                 'producer': server,
                 'produced_at': timestamp}
        for (r_server, file) in logs:
            if chunk in chunk_arrvied_at_server_map[r_server]:
                arrived_time = chunk_arrvied_at_server_map[r_server][chunk]
                sync_latency = arrived_time - timestamp
                entry["arrived_at_" + r_server] = arrived_time
                entry["sync_latency_" + r_server] = sync_latency
            elif server != r_server:
                # Try to find the next higher version for the chunk
                for version in range(int(v), int(v) + 10):
                    id = x + '_' + y + '_' + str(version)
                    if id in chunk_arrvied_at_server_map[r_server]:
                        arrived_time = chunk_arrvied_at_server_map[r_server][id]
                        sync_latency = arrived_time - timestamp
                        entry["arrived_at_" + r_server] = arrived_time
                        entry["sync_latency_" + r_server] = sync_latency
                        break

        rows.append(entry)
        # syncLatencies = syncLatencies.append(entry, ignore_index=True)
    syncLatencies = pd.DataFrame(rows, columns=columns)
    syncLatencies = syncLatencies.sort_values('produced_at')

    folderName = resultDir.split("/")[-1]
    if folderName == "":
        folderName = resultDir.split("/")[-2]
    syncLatencies.to_csv(resultDir + "/" + folderName + '.csv', sep="\t", index=False)

    # Calculate average latency for transferring chunk changes
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--result-dir', dest='resultDir', default="/tmp/")

    args = parser.parse_args()
    resultDir = args.resultDir

    do_calculation(resultDir=resultDir)
