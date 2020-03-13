from minindn.apps.application import Application
from mininet.log import info


class SVSGameServer(Application):

    def __init__(self, node, responsibility, clientId, logLevel='NONE', logFolder="./logs/", treeSize=65536,
                 traceFile="trace.csv", srcDir="/home/phmoll/Coding/SyncProtocols/QuadTreeSyncEvaluation/"):
        Application.__init__(self, node)

        self.logLevel = node.params['params'].get('nfd-log-level', logLevel)
        self.logFolder = logFolder
        self.traceFile = traceFile
        self.treeSize = treeSize
        self.srcDir = srcDir
        self.clientId = clientId

        self.responsibility = responsibility

        # create logfolder folder
        node.cmd('mkdir -p {}'.format(self.logFolder))

    def start(self):
        # Start capturing traffic with Tshark
        info("[{0}] Start StateVectorGameServer\n".format(self.node.name))
        self.node.cmd("{5}/StateVectorSyncClient"
                      " --responsiblityArea {0}"
                      " --logDir {1}"
                      " --treeSize {2}"
                      " --traceFile {3}"
                      " --clientId {4}"
                      " &> {1}/gameserver_{0}.out &".format(self.responsibility, self.logFolder, self.treeSize,
                                                            self.traceFile, self.clientId, self.srcDir))
