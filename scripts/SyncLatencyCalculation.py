import argparse
import pandas as pd
import glob
from tqdm.notebook import tqdm
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
    for chunk, (timestamp, server) in tqdm(chunk_produced_map.items(), total=len(chunk_produced_map)):
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

    syncLatencies.tail(50)
    # syncLatencies.to_csv('../logs/syncLatencies.csv', sep='\t')

    syncLatencies.to_csv(resultDir + '.csv')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--result-dir', dest='resultDir', default="/tmp/")

    args = parser.parse_args()
    resultDir = args.resultDir

    do_calculation(resultDir=resultDir)
