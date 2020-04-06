from minindn.apps.application import Application
from mininet.log import info


class ZMQGameServer(Application):

    def __init__(self, node, responsibility, clientId, logLevel='NONE', logFolder="./logs/", otherPeers=[],
                 traceFile="trace.csv", srcDir="/home/phmoll/Coding/SyncProtocols/ZMQSyncPeer/"):
        Application.__init__(self, node)

        self.logLevel = node.params['params'].get('nfd-log-level', logLevel)
        self.logFolder = logFolder
        self.traceFile = traceFile
        self.srcDir = srcDir
        self.clientId = clientId
        self.otherPeers = otherPeers

        self.responsibility = responsibility

        # create logfolder folder
        node.cmd('mkdir -p {}'.format(self.logFolder))

    def start(self):
        others = ",".join([ip + ":" + str(port) for (ip, port) in self.otherPeers])

        rect_parts = self.responsibility.split(",")
        zmqRect = [rect_parts[0], rect_parts[3], rect_parts[2], rect_parts[1]]

        # Start capturing traffic with Tshark
        info("[{0}] Start ZMQGameServer\n".format(self.node.name))
        cmd = "sudo python3 {3}/peers_seperate/peer.py" \
              " --coordinates {0}" \
              " --serverPort 5000" \
              " --clients {4}" \
              " --logDir {1}" \
              " --tracefile {2} &> {1}/app-out.log &".format(','.join(zmqRect), self.logFolder,
                                                    self.traceFile, self.srcDir, others)
        print(cmd)
        self.node.cmd(cmd)
