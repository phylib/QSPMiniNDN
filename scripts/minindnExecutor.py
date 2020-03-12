import os
import argparse


def execute(result_dir="/vagrant/results/"):
    num_servers = [
        4,
        16
    ]
    runs = [
        0,
        1,
        2,
        3,
        4,
        5
    ]
    protocols = [
        "QuadTree",
        # "StateVector",
        # "ZMQ"
    ]

    types = [
        "continent",
        "cluster"
    ]
    traceFiles = [
        "ChunkChanges-concentrated.csv",
        "ChunkChanges-distributed.csv",
        "ChunkChanges-very-distributed.csv",
    ]

    print("### Starting Experiments ###")
    emulation_no = 1
    for run in runs:
        for servers in num_servers:
            for protocol in protocols:
                for type in types:
                    for traceFile in traceFiles:

                        print("### Starting emulation {} ###".format(emulation_no))
                        results_folder = result_dir + "/RESULTS_" + str(
                            servers) + "_" + type + "_" + protocol + "_run" + str(run) + "_" + traceFile.replace('.',
                                                                                                                 '')

                        topology = "topologies/geant.conf"
                        serverClusterConfig = ""
                        if type == "cluster":
                            topology = "topologies/" + str(servers) + "-server-topo.conf"
                            serverClusterConfig = "--server-cluster True "

                        cmd = "sudo python examples/serversync_experiment.py {} --num-servers={} --protocol={} {} " \
                              "--result-dir {} --random-seed {} --trace-file {}/traceFiles/{}".format(
                            topology,
                            servers,
                            protocol,
                            serverClusterConfig,
                            results_folder,
                            run,
                            os.getcwd(),
                            traceFile
                        )
                        print(cmd)
                        os.system(cmd)

                        # do cleanup
                        cmd = "sudo rm -rf /tmp/minindn"
                        print(cmd)
                        os.system(cmd)

                        emulation_no += 1
                        print("")

    # os.system("sudo chown -R vagrant:vagrant " + result_dir)
    # os.system(
    #     "source ~/analysis/bin/activate && python3 ~/mc/mc-server-sync/statistics/trafficAnalysis/parsePCAP.py -i " + result_dir + " -o " + result_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Execute multiple MiniNDN Evaluations.')
    parser.add_argument('--result-dir', dest='resultDir', default="/tmp/")

    args = parser.parse_args()
    resultDir = args.resultDir

    execute(result_dir=resultDir)
