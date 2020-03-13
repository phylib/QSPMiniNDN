from minindn.apps.application import Application
from mininet.log import info


class QuadTreeGameServer(Application):

    def __init__(self, node, responsibility, logLevel='NONE', logFolder="./logs/", treeSize=65536,
                 traceFile="trace.csv", requestLevel=1, prefix="/world", chunkThreshold=200, levelDifference=2,
                 srcDir="/home/phmoll/Coding/SyncProtocols/QuadTreeSyncEvaluation/"):
        Application.__init__(self, node)

        self.logLevel = node.params['params'].get('nfd-log-level', logLevel)
        self.logFolder = logFolder
        self.traceFile = traceFile
        self.treeSize = treeSize
        self.requestLevel = requestLevel
        self.prefix = prefix
        self.chunkThreshold = chunkThreshold
        self.levelDifference = levelDifference
        self.srcDir = srcDir

        self.responsibility = responsibility

        # create logfolder folder
        node.cmd('mkdir -p {}'.format(self.logFolder))

    def start(self):
        # Start capturing traffic with Tshark
        info("[{0}] Start QuadTreeGameServer\n".format(self.node.name))
        self.node.cmd("{8}/EvaluationSyncClient"
                      " --responsiblityArea {0}"
                      " --logDir {1}"
                      " --treeSize {2}"
                      " --traceFile {3}"
                      " --requestLevel {4}"
                      " --prefix {5}"
                      " --chunkThreshold {6}"
                      " --levelDifference {7}"
                      " &> {1}/gameserver_{0}.out &".format(self.responsibility, self.logFolder, self.treeSize,
                                                            self.traceFile, self.requestLevel, self.prefix,
                                                            self.chunkThreshold, self.levelDifference, self.srcDir))
