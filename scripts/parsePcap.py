import argparse as argparse
import pyshark
import os
import argparse
import time
import copy
import multiprocessing
from multiprocessing import Pool
import glob
import tqdm

IP_SERVER_SYNC_PORT = "5555"
MC_SERVER_PORT = "25565"
PYSHARK_DEBUG = True

proc_pool_args = []


# needs python3-packet pyshark (& installed tshark/wireshark)

# NDN packet dissector:
# git clone https://github.com/named-data/ndn-tools.git
# cd ndn-tools/tools/dissect-wireshark
# sudo cp -v ndn.lua /usr/local/share/ndn-dissect-wireshark/
# sudo vim /usr/share/wireshark/init.lua (append the following two lines to the end of the file)
# --dofile("/full/path/to/ndn.lua")
# dofile("/usr/local/share/ndn-dissect-wireshark/ndn.lua")

# https://stackoverflow.com/questions/800197/how-to-get-all-of-the-immediate-subdirectories-in-python
def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


def append_stat_dict_to_file(stat_dict, output_file_path):
    with open(output_file_path, "a") as output_file:
        output_file.write(
            "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(stat_dict["node"],
                                                                  stat_dict["in/out"],
                                                                  stat_dict["#interests"],
                                                                  stat_dict["bytesInterests"],
                                                                  stat_dict["#data"],
                                                                  stat_dict["bytesData"],
                                                                  stat_dict["#Nack"],
                                                                  stat_dict["bytesNack"],
                                                                  stat_dict["#IPSyncPackets"],
                                                                  stat_dict["bytesIPSyncPackets"],
                                                                  stat_dict["bytesSyncPayload"]))


def get_parent_dir(directory):
    return os.path.dirname(directory)


def parse_pcap(tuple):
    pcap_file = tuple[0]
    output_csv = tuple[1]
    # unpack tuple and call function
    parse_pcap_file(pcap_file, output_csv)


def parse_ip_addresses(ip_address_file):
    with open(ip_address_file) as file:
        addresses = file.readlines()[0].strip()
        return addresses.split(",")
    raise Exception("IP not found for " + ip_address_file)


def parse_pcap_file(pcap_file, output_csv):
    start = time.time()
    print(pcap_file + ": started processing")

    ip_address_list_file = "/".join(pcap_file.split("/")[:-1]) + "/ip-adresses.txt"
    own_ips = parse_ip_addresses(ip_address_list_file)
    # The location of the pcap file looks like .../[hostname]/log/filename.pcap.
    host = pcap_file.split("/")[-3]

    stat_in = {"node": host, "in/out": "in", "#interests": 0, "bytesInterests": 0, "#data": 0, "bytesData": 0,
               "#Nack": 0, "bytesNack": 0,
               "#IPSyncPackets": 0,
               "bytesIPSyncPackets": 0, "bytesSyncPayload": 0}

    stat_out = copy.deepcopy(stat_in)
    stat_out["in/out"] = "out"

    cap = pyshark.FileCapture(pcap_file, only_summaries=False)
    #cap.set_debug(PYSHARK_DEBUG)
    # cap.set_debug()

    try:
        for packet in cap:
            # Skip packets that are neighter TCP nor UDP
            if not hasattr(packet, "udp") and not hasattr(packet, "tcp"):  # skip certain packets (ARP, ICMP)
                continue

            # determine if incoming/outgoing
            stat = stat_in  # incoming data by default
            if packet.ip.src in own_ips:  # outgoing if src is own_ip
                stat = stat_out
            elif (packet.ip.dst not in own_ips):
                continue  # happens when packet was forwarded only

            # get packet infos
            if hasattr(packet, "ndn"):
                ndn_packet_type = packet.ndn._ws_lua_text.split(',')[0]
                if ndn_packet_type == "Interest":
                    stat["#interests"] += 1
                    stat["bytesInterests"] += int(packet.length)
                elif ndn_packet_type == "Data":
                    stat["#data"] += 1
                    stat["bytesData"] += int(packet.length)

                    # just take binary length of content as upper estimation of transported data (usually just two bytes above the actual size [TYPE, LENGTH])
                    # parsing the TLV is too error prone / to much work
                    # correctness hinges on correctness of Wireshark NDN dissector (ndn.lua, https://github.com/named-data/ndn-tools/tree/master/tools/dissect-wireshark )
                    # https://named-data.net/doc/NDN-packet-spec/current/tlv.html#variable-size-encoding-for-type-t-and-length-l
                    # https://named-data.net/doc/NDN-packet-spec/current/data.html
                    read_len = len(packet.ndn.content.binary_value)
                    stat["bytesSyncPayload"] += read_len
                elif ndn_packet_type == "Nack" or ndn_packet_type == "LpPacket":
                    stat["#Nack"] += 1
                    stat["bytesNack"] += int(packet.length)
                else:
                    print(pcap_file + ": unhandled NDN packet type: " + ndn_packet_type)
            elif hasattr(packet, "tcp"):
                ports = [packet.tcp.srcport, packet.tcp.dstport]

                # Segmentation-independent TCP payload. payload_bytes == 67 corresponds to the "Len:" in wireshark line:
                # Transmission Control Protocol, Src Port: 25565, Dst Port: 55782, Seq: 4488, Ack: 27, Len: 67
                # payload_bytes == 0 e.g. in case of "ACK"-only
                payload_bytes = int(packet.tcp.payload.size) if hasattr(packet.tcp, "payload") else 0

                stat["#IPSyncPackets"] += 1
                stat["bytesIPSyncPackets"] += int(packet.length)
                stat["bytesSyncPayload"] += payload_bytes
            else:
                print(pcap_file + ": dissector detected no 'ndn' or 'tcp', packet layers: " + str(packet.layers))

        cap.close()
    except:
        print("Could not fully parse PCAP file")

    end = time.time()
    print(pcap_file + ": finished in {} seconds".format(end - start))
    # write results to log file
    append_stat_dict_to_file(stat_in, output_csv)
    append_stat_dict_to_file(stat_out, output_csv)


def parse_directory(directory, fullPath):
    # write header to output file (overwrite existing)
    output_file_path = os.path.join(fullPath, "network-stats.csv")
    with open(output_file_path, "w") as output_file:
        output_file.write(
            "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format("node", "in/out", "#interests",
                                                                  "bytesInterests", "#data",
                                                                  "bytesData", "#Nack", "bytesNack",
                                                                  "#IPSyncPackets",
                                                                  "bytesIPSyncPackets", "bytesSyncPayload"))
    print("Parsing folder: " + fullPath)
    logfiles = glob.glob(fullPath + "/**/*_chunklog.csv", recursive=True)
    # Logfile syntax is [setting-directory]/[hostname]/log/[logfilename]
    hostnames = list(set([logfile.split("/")[-3] for logfile in logfiles]))
    print(hostnames)

    # todo: Search for servers instead of processing all folders
    for host in hostnames:
        pcap_dir = os.path.join(fullPath, host, "log")

        for file in os.listdir(pcap_dir):
            if file.endswith(".pcap"):
                proc_pool_args.append((os.path.join(pcap_dir, file), output_file_path))


if __name__ == "__main__":
    # entry point of script
    num_cpus = multiprocessing.cpu_count()
    used_cpus = max(1,
                    int(num_cpus / 2))  # leave room for one tshark-process for every concurrently processed pcap-file

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-r", "--result-dir", help="Directory containing the result dirs of the runs",
                        default="./")
    parser.add_argument("-p", "--processes", help="Size of process pool", type=int,
                        default=used_cpus)
    args = parser.parse_args()

    input = args.result_dir
    used_cpus = args.processes
    print("detected " + str(num_cpus) + " cpu(s), using " + str(used_cpus) + " cpu(s)")

    p = Pool(args.processes)

    # find pcap files that have to be processed, create output/log files for runs in output dir
    for subfolder in get_immediate_subdirectories(input):
        if "_QuadTree_run" in subfolder or "_StateVector_run" in subfolder or "_ZMQ_run" in subfolder:
            parse_directory(subfolder, os.path.join(input, subfolder))
        else:
            print("skipping directory: " + os.path.join(input, subfolder))

    # concurrently process as many pcap files as possible
    # p.map(parse_pcap, proc_pool_args)
    for _ in tqdm.tqdm(p.imap_unordered(parse_pcap, proc_pool_args), total=len(proc_pool_args)):
        pass
