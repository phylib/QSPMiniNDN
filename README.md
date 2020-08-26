# Mini-NDN QSP Evaluation

This repository contains software artifacts for the the paper: _Philipp Moll, Selina Isak, Hermann Hellwagner, Jeff Burke. A Quadtree-based Synchronization Protocol for Inter-Server Game State Synchronization. Submitted to Computer Networks, Elsevier._

This repository is a fork of the [MiniNDN repository](https://github.com/named-data/mini-ndn). The original README
content can be found below.

The script to perform the evaluation can bei found in `examples/serversync_experiment.py`. To start, execute
`sudo python3 examples/serversync_experiment.py -h`. The used topologies were the `4-server-topo`, the `16-server-topo`
and the `geant` topology. Please specify the parameters `--server-cluster` and `--num-servers` accordingly.

The trace files used in the paper's evalulations can be found in the `traceFiles` folder. However, other trace files
can be generated as explained in the [reproducibility repository of the paper](https://github.com/phylib/QSPArtifacts).

To install MiniNDN and all Dependencies, please use `sudo ./install.sh -a`

# Calculation of results

The results of a minindn evaluation run can be found in the folder specified by
the `--resultDir` option. In order to draw figures from the raw results, a
post processing step is necessary. The scripts can be found in the `scripts`
folder of this repository. To postprocess, use the script
`scripts/SyncLatencyCalculation.py`.

Once the results for all required settings are post-processed, the script
'scripts/visuals.py' can be used to create the required figures.

Mini-NDN
========

If you are new to the NDN community of software generally, read the
[Contributor's Guide](https://github.com/named-data/NFD/blob/master/CONTRIBUTING.md).

### What is Mini-NDN?

Mini-NDN is a lightweight networking emulation tool that enables testing, experimentation, and
research on the NDN platform based on [Mininet](https://github.com/mininet/mininet).
Mini-NDN uses the NDN libraries, NFD, NLSR, and tools released by the
[NDN project](http://named-data.net/codebase/platform/) to emulate an NDN network on a single system.

Mini-NDN is open and free software licensed under the GPL 3.0 license. Mini-NDN is free to all
users and developers. For more information about licensing details and limitations,
please refer to [COPYING.md](COPYING.md).

The first release of Mini-NDN is developed by members of the NSF-sponsored NDN project team.
Mini-NDN is open to contribution from the public.
For more details, please refer to [AUTHORS.md](AUTHORS.md).
Bug reports and feedback are highly appreciated and can be made through our
[Redmine site](http://redmine.named-data.net/projects/mini-ndn) and the
[mini-ndn mailing list](http://www.lists.cs.ucla.edu/mailman/listinfo/mini-ndn).

### Documentation

Please refer to http://minindn.memphis.edu/ or [docs/index.rst](docs/index.rst) for installation, usage, and other documentation.
The documentation can be built using:

    ./install.sh -d

and is available under `docs/_build/html`.
