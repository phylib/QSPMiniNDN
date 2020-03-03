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
import time
import os
import configparser
from subprocess import call, check_output
import shutil
import glob

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import Switch
from mininet.util import ipStr, ipParse
from mininet.log import info, error


class Minindn(object):
    """ This class provides the following features to the user:
        1) Wrapper around Mininet object with option to pass topology directly
           1.1) Users can pass custom argument parser to extend the default on here
        2) Parses the topology file given via command line if user does not pass a topology object
        3) Provides way to stop Mini-NDN via stop
           3.1) Applications register their clean up function with this class
        4) Sets IPs on neighbors for connectivity required in a switch-less topology
        5) Some other utility functions
    """
    ndnSecurityDisabled = False

    def __init__(self, parser=argparse.ArgumentParser(), topo=None, topoFile=None, **mininetParams):
        """Create MiniNDN object
        parser: Parent parser of Mini-NDN parser
        topo: Mininet topo object (optional)
        topoFile: Mininet topology file location (optional)
        mininetParams: Any params to pass to Mininet
        """
        self.parser = Minindn.parseArgs(parser)
        self.args = self.parser.parse_args()

        self.workDir = self.args.workDir
        self.resultDir = self.args.resultDir

        if not topoFile:
            # Args has default topology if none specified
            self.topoFile = self.args.topoFile
        else:
            self.topoFile = topoFile

        if topo is None:
            try:
                info('Using topology file {}\n'.format(self.topoFile))
                self.topo = self.processTopo(self.topoFile)
            except configparser.NoSectionError as e:
                info('Error reading config file: {}\n'.format(e))
                sys.exit(1)
        else:
            self.topo = topo

        self.net = Mininet(topo=self.topo, link=TCLink, **mininetParams)

        for host in self.net.hosts:
            if 'params' not in host.params:
                host.params['params'] = {}

            homeDir = '{}/{}'.format(self.workDir, host.name)
            host.params['params']['homeDir'] = homeDir
            host.cmd('mkdir -p {}'.format(homeDir))
            host.cmd('export HOME={} && cd ~'.format(homeDir))

        self.cleanups = []

        if not self.net.switches:
            self.ethernetPairConnectivity()

        try:
            Minindn.ndnSecurityDisabled = '/dummy/KEY/-%9C%28r%B8%AA%3B%60' in \
                                          check_output('ndnsec-get-default -k'.split()). \
                                              decode('utf-8').split('\n')
            info('Dummy key chain patch is installed in ndn-cxx. Security will be disabled.\n')
        except:
            pass

    @staticmethod
    def parseArgs(parent):
        parser = argparse.ArgumentParser(prog='minindn', parents=[parent], add_help=False)

        # nargs='?' required here since optional argument
        parser.add_argument('topoFile', nargs='?', default='/usr/local/etc/mini-ndn/default-topology.conf',
                            help='If no template_file is given, topologies/default-topology.conf will be used.')

        parser.add_argument('--work-dir', action='store', dest='workDir', default='/tmp/minindn',
                            help='Specify the working directory; default is /tmp/minindn')

        parser.add_argument('--result-dir', action='store', dest='resultDir', default=None,
                            help='Specify the full path destination folder where experiment results will be moved')

        return parser

    def ethernetPairConnectivity(self):
        ndnNetBase = '10.0.0.0'
        interfaces = []
        for host in self.net.hosts:
            for intf in host.intfList():
                link = intf.link
                node1, node2 = link.intf1.node, link.intf2.node

                if isinstance(node1, Switch) or isinstance(node2, Switch):
                    continue

                if link.intf1 not in interfaces and link.intf2 not in interfaces:
                    interfaces.append(link.intf1)
                    interfaces.append(link.intf2)
                    node1.setIP(ipStr(ipParse(ndnNetBase) + 1) + '/30', intf=link.intf1)
                    node2.setIP(ipStr(ipParse(ndnNetBase) + 2) + '/30', intf=link.intf2)
                    ndnNetBase = ipStr(ipParse(ndnNetBase) + 4)

    @staticmethod
    def processTopo(topoFile):
        config = configparser.ConfigParser(delimiters=' ')
        config.read(topoFile)
        topo = Topo()

        items = config.items('nodes')
        for item in items:
            name = item[0].split(':')[0]

            params = {}
            for param in item[1].split(' '):
                if param == '_':
                    continue
                params[param.split('=')[0]] = param.split('=')[1]

            topo.addHost(name, params=params)

        try:
            items = config.items('switches')
            for item in items:
                name = item[0].split(':')[0]
                topo.addSwitch(name)
        except configparser.NoSectionError:
            # Switches are optional
            pass

        items = config.items('links')
        for item in items:
            link = item[0].split(':')

            params = {}
            for param in item[1].split(' '):
                key = param.split('=')[0]
                value = param.split('=')[1]
                if key in ['bw', 'jitter', 'max_queue_size']:
                    value = int(value)
                if key == 'loss':
                    value = float(value)
                params[key] = value

            topo.addLink(link[0], link[1], **params)

        return topo

    def start(self):
        self.net.start()
        time.sleep(3)

    def stop(self):
        for cleanup in self.cleanups:
            cleanup()
        self.net.stop()
        if self.resultDir is not None:
            info("Moving results to {}\n".format(self.resultDir))
            os.system("mkdir -p {}".format(self.resultDir))
            for file in glob.glob('{}/*'.format(self.workDir)):
                shutil.move(file, self.resultDir)

    @staticmethod
    def cleanUp():
        devnull = open(os.devnull, 'w')
        call('nfd-stop', stdout=devnull, stderr=devnull)
        call('mn --clean'.split(), stdout=devnull, stderr=devnull)

    @staticmethod
    def verifyDependencies():
        """Prevent MiniNDN from running without necessary dependencies"""
        dependencies = ['nfd', 'nlsr', 'infoedit', 'ndnping', 'ndnpingserver']
        devnull = open(os.devnull, 'w')
        # Checks that each program is in the system path
        for program in dependencies:
            if call(['which', program], stdout=devnull):
                error('{} is missing from the system path! Exiting...\n'.format(program))
                sys.exit(1)
        devnull.close()

    @staticmethod
    def sleep(seconds):
        # sleep is not required if ndn-cxx is using in-memory keychain
        if not Minindn.ndnSecurityDisabled:
            time.sleep(seconds)
