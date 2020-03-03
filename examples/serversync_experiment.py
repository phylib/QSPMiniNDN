# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2015-2019, The University of Memphis,
#                          Arizona Board of Regents,
#                          Regents of the University of California.
#
# This file is part of Mini-NDN.
# See AUTHORS.md for a complete list of Mini-NDN authors and contributors.
#
# Mini-NDN is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mini-NDN is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mini-NDN, e.g., in COPYING.md file.
# If not, see <http://www.gnu.org/licenses/>.

import argparse
import sys
import random
import time
from tqdm import tqdm

from mininet.log import setLogLevel, info
from mininet.topo import Topo

from minindn.minindn import Minindn
from minindn.util import MiniNDNCLI
from minindn.apps.app_manager import AppManager
from minindn.apps.nfd import Nfd
from minindn.apps.tshark import Tshark
from minindn.helpers.ndn_routing_helper import NdnRoutingHelper

from math import sqrt, log

from minindn.apps.gameServer import GameServer

if __name__ == '__main__':
    setLogLevel('info')

    Minindn.cleanUp()
    Minindn.verifyDependencies()

    ####### Define evaluation specific parameters #######
    parser = argparse.ArgumentParser()
    parser.add_argument('--num-servers', dest='numServers', type=int, default=4, choices=[4, 16])
    parser.add_argument('--log-dir', dest='logDir', default="log/")
    parser.add_argument('--tree-size', dest='treeSize', default=65536)
    parser.add_argument('--prefix', dest='prefix', default="/world")
    parser.add_argument('--random-seed', dest='randomSeed', default=0)
    parser.add_argument('--chunk-threshold', dest='chunkThreshold', type=int, default=200)
    parser.add_argument('--level-difference', dest='levelDifference', default=2)
    parser.add_argument('--console', dest='console', default=False, type=bool)

    ####### Start all the NDN Stuff #######
    ndn = Minindn(parser=parser)
    ndn.start()

    numServers = ndn.args.numServers
    logDir = ndn.args.logDir
    treeSize = ndn.args.treeSize
    prefix = ndn.args.prefix
    randomSeed = ndn.args.randomSeed
    random.seed(randomSeed)

    info('Start PCAP logging on nodes\n')
    AppManager(ndn, ndn.net.hosts, Tshark, logFolder=logDir, singleLogFile=True)

    info('Starting NFD on nodes\n')
    nfds = AppManager(ndn, ndn.net.hosts, Nfd)

    ####### Here, the real magic is starting #######

    # Calculate regions of the servers
    requestLevel = int(log(sqrt(numServers), 2))
    regionSize = treeSize / 2 ** requestLevel
    servers = []
    for i in range(0, numServers):
        host = ndn.net.hosts[random.randint(0, len(ndn.net.hosts) - 1)]
        x_index = int(i / sqrt(numServers))
        y_index = int(i % sqrt(numServers))
        x = x_index * regionSize
        y = y_index * regionSize
        responsibility = ",".join([str(y), str(x), str(y + regionSize), str(x + regionSize)])
        name = []
        for j in range(0, requestLevel):
            qIndex = 3
            if (x_index / 2 ** (requestLevel - 1 - j)) % 2 == 0 and (y_index / 2 ** (requestLevel - 1 - j)) % 2 == 0:
                qIndex = 0
            elif (x_index / 2 ** (requestLevel - 1 - j)) % 2 == 0 and (y_index / 2 ** (requestLevel - 1 - j)) % 2 == 1:
                qIndex = 1
            elif (x_index / 2 ** (requestLevel - 1 - j)) % 2 == 1 and (y_index / 2 ** (requestLevel - 1 - j)) % 2 == 0:
                qIndex = 2
            name.append(qIndex)
        str_name = prefix + "/" + "/".join(str(x) for x in name)
        print((host, x_index, y_index, x, y, str_name))
        servers.append((host, x_index, y_index, x, y, str_name, responsibility))

    info('Adding static routes to NFD\n')
    grh = NdnRoutingHelper(ndn.net)
    # For all host, pass ndn.net.hosts or a list, [ndn.net['a'], ..] or [ndn.net.hosts[0],.]
    for server in servers:
        grh.addOrigin([server[0]], [server[5]])
    grh.calculateNPossibleRoutes(nFaces=1)

    # Start all game server apps
    for server in servers:
        AppManager(ndn, [server[0]], GameServer, responsibility=server[6], logFolder=logDir, prefix=prefix,
                   requestLevel=requestLevel,
                   treeSize=treeSize,
                   chunkThreshold=ndn.args.chunkThreshold, levelDifference=ndn.args.levelDifference,
                   traceFile="/home/phmoll/Coding/SyncProtocols/QuadTreeRMAComparison/max_distance/ChunkChanges-very-distributed.csv")

    # Sleep until the end of the evaluation + a bit more
    info("Waiting for evaluation to end\n")
    if ndn.args.console:
        MiniNDNCLI(ndn.net)
    else:
        for i in tqdm(range(0, 66), desc="Evaluation Progress"):
            time.sleep(10)

    ndn.stop()
