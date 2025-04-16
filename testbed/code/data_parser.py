# import os
from sys import argv
import pyshark
from json import dump
from pathlib import Path
    

par_dir = Path(__file__).resolve().parent.parent


def collect_data(host: str, name: str, packet) -> None:
    if name not in packet_data[host].keys():
        packet_data[host][name] = {"interest_times": [], "data_times": []}
    packet_data[host][name][
        "data_times" if packet.ndn.type == "Data" else "interest_times"].append(
            float(packet.sniff_timestamp))


def parse(protocol: str | None = None) -> None:
    # Collect relevent pcap files for parsing.
    if protocol is None:
        pcap_paths = [str(file) for file in Path(f"{par_dir}/pcaps").rglob("*") if file.is_file()]
    else:
        pcap_paths = [str(file) for file in Path(f"{par_dir}/pcaps/{protocol}").rglob("*")]
    
    # Obtain pcap data.
    pcap_data_dict: dict[str, dict] = {}
    
    for pcap_path in pcap_paths:
        # data_dict keys = "<protocol>/<host>.pcap"
        pcap_data_dict["/".join(pcap_path.split("/")[-2:]).split("-eth")[0]] = pyshark.FileCapture(pcap_path)
    
    # print(dir(pcap_file_dict["c0"][0]))
    # print(f"frame_info: {pcap_file_dict['c0'][0].frame_info}")
    # print(f"ip: {pcap_file_dict['c0'][0].ip}")
    # print(f"dir(ndn): {dir(pcap_file_dict['c0'][0].ndn)}")
    # print(f"ndn.name: {pcap_file_dict['c0'][0].ndn.name}")
    # print(f"ndn.type: {pcap_file_dict['c0'][0].ndn.type}")
    # print(f"number: {pcap_file_dict['c0'][0].number}")
    # print(f"sniff_time: {pcap_file_dict['c0'][0].sniff_time}")
    # print(f"sniff_timestamp: {pcap_file_dict['c0'][0].sniff_timestamp}")

    # Get raw data from packets.
    for host, host_data in pcap_data_dict.items():
        # if host in packet_data.keys():
        #     print("WARNING: Packet dict entry is being overwritten.")
        protocol = host.split("/")[0]
        host_id = host.split("/")[-1]
        packet_data[host] = {}

        for packet in host_data:
            # Skip non-NDN packets.
            if not hasattr(packet, "ndn"):
                continue    
        
            # RPC names may contain "FUNC", "PARAM" and "RESULT" components.
            name = packet.ndn.name

            if protocol == "fwh":
                if host_id[0] == "s":
                    # FWH Server outgoing Interests: PARAM only
                    if "PARAM" in name and "FUNC" not in name:
                        collect_data(host, name, packet)
                else:
                    # FWH Client outgoing Interests: FUNC only
                    if "FUNC" in name:
                        collect_data(host, name, packet)

            elif protocol == "nsc":
                # NSC Server outgoing Interests: None
                if host_id[0] == "s":
                    continue
                else:
                    # NSC Client outgoing Interests: FUNC only
                    if "FUNC" in name:
                        collect_data(host, name, packet)

            elif protocol == "fm":
                # FM Server outgoing Interests: None
                if host_id[0] == "s":
                    continue
                else:
                    # FM Client outgoing Interests: FUNC and RESULT
                    if "FUNC" in name or "RESULT" in name:
                        collect_data(host, name, packet)

            elif protocol == "pnb":
                # PNB Server outgoing Interests: None
                if host_id[0] == "s":
                    continue
                else:
                    # PNB Client outgoing Interests: FUNC only
                    if "FUNC" in name:
                        collect_data(host, name, packet)
            
            else:
                print(f"Unable to identify protocol: {protocol}.")
            

def calc_deltas():
    # Get response times.
    for host, host_data in packet_data.items():
        for name, name_data in host_data.items():
            # Set up delta times list at the start.
            name_data["delta_times"] = []
            
            if len(name_data["interest_times"]) == 0:
                print(f"No interest times collected for: ({host}) {name}.")
                # if len(name_data["data_times"]) == 0:
                #     print(f"No data times collected for: ({host}) {name}.")
                continue
            if len(name_data["data_times"]) == 0:
                print(f"No data times collected for: ({host}) {name}.")
                continue
        
            # Check for timeouts..
            if len(name_data["interest_times"]) > len(name_data["data_times"]):
                print(f"Timeout detected for ({host}) {name}: ")
                print(f"Interests: {name_data['interest_times']}")
                print(f"Datas: {name_data['data_times']}")

                keep = []       # Interest times to keep.
                for data_time in name_data["data_times"]:

                    cull = []   # Interest times to cull.
                    for interest_time in name_data["interest_times"]:
                        if interest_time < data_time:
                            cull.append(interest_time)
                        else: 
                            break

                    # Keep last cull time later data_time iterations..
                    keep.append(cull.pop())  

                    # Remove cull times from data (assumed to be timed out interests)..
                    for time in cull:
                        name_data["interest_times"].remove(time)                    

                print(f"Interests (culled): {name_data['interest_times']}")
        
            # Calculate delta times.
            for i in range(len(name_data["data_times"])):
                name_data["delta_times"].append(
                    name_data["data_times"][i] - name_data["interest_times"][i])


if __name__ == "__main__":
    # Dict of parsed packet data.
    packet_data: dict[str, dict[str, dict[str, list[float]]]] = {}
    if len(argv) == 1:
        parse()
    else:
        parse(argv[1])

    calc_deltas()

    # Save data.
    for host, host_data in packet_data.items():
        with open(f"{par_dir}/data/{host}.data", "w") as f:
            dump(host_data, f)