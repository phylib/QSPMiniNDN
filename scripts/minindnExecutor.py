import os
import argparse


def execute(result_dir="/vagrant/results/", srcDir="./QuadTreeSyncEvaluation/", workDir="/tmp/minindn/",
            calcPcap=False):
    num_servers = [
        # 4,
        # 16,
        64
    ]
    runs = [
        0,
        1,
        2,
        # 3,
        # 4,
        # 5
    ]
    protocols = [
        # "QuadTree",
        # "StateVector",
        # "ZMQ",
        "P2P"
    ]

    types = [
        # "continent",
        "cluster"
    ]
    traceFiles = [
        # "ChunkChanges-concentrated.csv",
        # "ChunkChanges-distributed.csv",
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

                        # Check if the results_folder already exists and do not do evaluation in this case
                        if os.path.isdir(results_folder):
                            print("### Skipping evaluation run, result folder {} already exists ###".format(
                                results_folder))
                            continue

                        topology = "topologies/geant.conf"
                        serverClusterConfig = ""
                        if type == "cluster":
                            topology = "topologies/" + str(servers) + "-server-topo.conf"
                            serverClusterConfig = "--server-cluster True "

                        cmd = "sudo python examples/serversync_experiment.py {} --num-servers={} --protocol={} {} " \
                              "--result-dir {} --random-seed {} --trace-file {}/traceFiles/{} --src-dir {} --work-dir {}".format(
                            topology,
                            servers,
                            protocol,
                            serverClusterConfig,
                            results_folder,
                            run,
                            os.getcwd(),
                            traceFile,
                            srcDir,
                            workDir
                        )
                        print(cmd)
                        os.system(cmd)

                        # do cleanup
                        cmd = "sudo rm -rf {}".format(workDir)
                        print(cmd)
                        os.system(cmd)

                        cmd = "sudo chown -R ubuntu:ubuntu {}".format(results_folder)
                        print(cmd)
                        os.system(cmd)

                        # Start calculation of results as background process
                        cmd = "python3 scripts/SyncLatencyCalculation.py --result-dir {} &".format(results_folder)
                        print(cmd)
                        os.system(cmd)

                        emulation_no += 1
                        print("")

    os.system("sudo chown -R ubuntu:ubuntu " + result_dir)
    if calcPcap:
        os.system("python3 scripts/parsePcap.py --result-dir {}".format(results_folder))
    # os.system(
    #     "source ~/analysis/bin/activate && python3 ~/mc/mc-server-sync/statistics/trafficAnalysis/parsePCAP.py -i " + result_dir + " -o " + result_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Execute multiple MiniNDN Evaluations.')
    parser.add_argument('--result-dir', dest='resultDir', default="/tmp/")
    parser.add_argument('--src-dir', dest='srcDir', default=None)
    parser.add_argument('--work-dir', dest='workDir', default="/tmp/minindn/")
    parser.add_argument('--calc-pcap', action='store_true',
                        help="Recalculate all pcap stats after the evaluation finished")

    args = parser.parse_args()
    resultDir = args.resultDir
    srcDir = args.srcDir
    workDir = args.workDir
    calcPcap = args.calcPcap
    if srcDir is None:
        srcDir = os.getcwd() + "/QuadTreeSyncEvaluation/"

    execute(result_dir=resultDir, srcDir=srcDir, workDir=workDir, calcPcap=calcPcap)
