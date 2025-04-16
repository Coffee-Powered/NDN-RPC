# Example code from:
# https://github.com/named-data/mini-ndn/blob/master/examples/mnndn.py


# import datetime
from os import popen
from sys import argv
# from io import TextIOWrapper
from time import sleep 
from pathlib import Path
from json import load
from random import choice, seed
seed(0)

from mininet.log import setLogLevel, info
from minindn.minindn import Minindn, Topo
from minindn.util import MiniNDNCLI, getPopen
from minindn.apps.app_manager import AppManager
from minindn.apps.nfd import Nfd
from minindn.apps.nlsr import Nlsr

# from ndn_framework.ndn_utility import get_datetime, get_time_diff


if __name__ == '__main__':
    # Process CMD args for convenienve and to prevent them from conflicting with MiniNDN startup..
    ndn_config: dict[str, str | list | None] = {"protocol": None, "other": []}
    while len(argv) > 1:
        arg = argv.pop(1)
        if arg in ["fwh", "fm", "nsc", "pnb"]:
            ndn_config["protocol"] = arg
        # elif arg in ["average_pixel", "desaturate_image", "fibonacci", "color_image"]:
        #     ndn_config["function"] = arg
        # elif arg in ["multi_adv"]:
        #     ndn_config["test"] = arg
        elif "cli=" in arg or "srv=" in arg:
            host, count = arg.split("=")
            ndn_config["clients" if host == "cli" else "servers"] = int(count)
        elif "size=" in arg:
            # if len(arg) > 5:
            try:
                ndn_config["topo_size"] = int(arg.split("=")[-1])
            except:
                print(f"Unable to parse size arg: {arg}.")
                exit()
        elif arg in ["sprintlink"]:
            ndn_config["benchmark"] = arg
        else:
            print(f"Other arg detected: {arg}")
            ndn_config["other"].append(arg)

    # Begin test.
    protocol_defined: bool = ndn_config["protocol"] is not None
    task_defined: bool = "test" in ndn_config.keys() or "benchmark" in ndn_config.keys()
    if not protocol_defined or not task_defined:
        print((f"Unable to run MiniNDN, "
               f"{'protocol' if ndn_config['protocol'] is None else 'function'}"
               f" is not undefined."))
        exit()

    if "clients" in ndn_config.keys() and "servers" in ndn_config.keys():
        print((f"Setting up MiniNDN with {ndn_config['clients']} clients, "
               f"and {ndn_config['servers']} servers."))
    else:
        print((f"Unable to run MiniNDN,"
               f"{' clients not specified' if 'clients' not in ndn_config.keys() else ''}"
               f"{' servers not specified' if 'servers' not in ndn_config.keys() else ''}."))
        exit()

    setLogLevel('debug')

    Minindn.cleanUp()
    Minindn.verifyDependencies()

    curr_dir: Path = Path(__file__).resolve().parent
    par_dir: Path = Path(curr_dir).resolve().parent
    
    # Build topology.
    topo_dict: dict[str, list[dict[str, str | dict[str, str]]]]
    with open(f"{curr_dir}/data/1239.topo") as f:
        topo_dict = load(f)

    topo: Topo = Topo()

    if ndn_config["topo_size"] == 0:
        for host in topo_dict["hosts"]:
            topo.addHost(host["id"])
    else:
        for host in topo_dict["hosts"][:ndn_config['topo_size']]:
            topo.addHost(host["id"])

    for link in topo_dict["links"]:
        if link["src"] not in topo.hosts() or link["dest"] not in topo.hosts():
            continue    # Skip hosts not within test topo.
        duplicate: bool = False
        for src, dest in topo.links():
            if link["dest"] == src and link["src"] == dest:
                duplicate = True    # Skip links already established.
                break
        if not duplicate:
            topo.addLink(link["src"], link["dest"], **link["attrs"])

    print(f"Number of topo hosts: {len(topo.hosts())}")
    print(f"Number of topo links: {len(topo.links())}")

    # Find single-linked nodes..
    connections: dict[int, list[int]] = {}
    for host in topo.hosts():
        connections[host] = []

    for link in topo_dict["links"]:
        if link["src"] not in topo.hosts() or link["dest"] not in topo.hosts():
            continue    # Skip hosts if using a sub-set of the network topo.
        connections[link["src"]].append(link["dest"])

    no_link_nodes: list[str] = []
    single_link_nodes: list[str] = []
    multi_link_nodes: list[str] = []
    for node, neighbours in connections.items():
        if len(neighbours) == 0:
            print(f"Node {node} has 0 neighbours: {connections[node]}.")
            no_link_nodes.append(node)
        elif len(neighbours) == 1:
            # print(f"Node {node} has 1 neighbour: {connections[node]}.")
            single_link_nodes.append(node)
        else:
            multi_link_nodes.append(node)
    
    print(f"Number of no-linked nodes: {len(no_link_nodes)}.")
    print(f"Number of single-linked nodes: {len(single_link_nodes)}.")
    print(f"Number of multi-linked nodes: {len(multi_link_nodes)}.")

    if len(single_link_nodes) < 1:
        print("No single linked nodes, aborting.")
        exit()
    
    ndn = Minindn(topo=topo)
    
    # Set up host management dict.
    # cmd_dict: dict[str, dict[str, str]] = {"s": {}, "c": {}}
    # out: str = f"{par_dir}/logs/__host__.out"
    #
    # Define application commands and output paths.
    # if "s" in cmd_dict.keys():
    # cmd_dict["s"]["cmd"] = (f"python {curr_dir}/ndn_{ndn_config['protocol']}_server.py "
    #                          f"{True if ndn_config['function'] == 'fibonacci' else False} 4")
    # cmd_dict["s"]["stdout"] = "open(out.replace('__host__', 's__node__'), 'w')"
    # cmd_dict["s"]["stderr"] = "open(out.replace('__host__', 's__node__').replace('.out', '.err'), 'w')"
    # cmd_dict["s"]["tcpdump"] = (f"tcpdump -n -i __node__-eth0 -w "
    #                              f"{par_dir}/pcaps/{ndn_config['protocol']}/s__node__-eth0.pcap &")
    #
    # for i in range(4):
    #     if f"c{i}" in cmd_dict:
    # cmd_dict[f"c"]["cmd"] = (f"python {curr_dir}/ndn_{ndn_config['protocol']}_client.py "
    #                           f"{ndn_config['function']} {par_dir} __num__")
    # cmd_dict[f"c"]["stdout"] = "open(out.replace('__host__', 'c__node__'), 'w')"
    # cmd_dict[f"c"]["stderr"] = "open(out.replace('__host__', 'c__node__').replace('.out', '.err'), 'w')"
    # cmd_dict[f"c"]["tcpdump"] = (f"tcpdump -n -i __node__-eth0 -w "
    #                               f"{par_dir}/pcaps/{ndn_config['protocol']}/c__node__-eth0.pcap &")
        
    # Start application.
    
    # Begin Test.
    info("Starting up NDN..\n")
    # ndn_bootup_time_start: datetime = get_datetime()
    ndn.start()

    info('Starting NFD on nodes\n')
    nfds = AppManager(ndn, ndn.net.hosts, Nfd)
    info('Starting NLSR on nodes\n')
    nlsrs = AppManager(ndn, ndn.net.hosts, Nlsr)

    # ndn_bootup_time_diff: float = get_time_diff(ndn_bootup_time_start, get_datetime())
    # with open(f"{curr_dir}/data/minindn_times.txt", "a") as f:
    #     f.write(f"Time to boot up NDN with 1 CPU: {ndn_bootup_time_diff} seconds.\n")

    # Track log and err files in test for later.
    log_files: list[str] = []
    err_files: list[str] = []
    nodes_in_test: list[tuple[str, str]] = []

    # Create servers
    for i in range(ndn_config["servers"]):
        node: str = choice(multi_link_nodes) # Choose random multi-link node.
        multi_link_nodes.remove(node)
        nodes_in_test.append((node, "s"))

        log_file: str = f"{par_dir}/logs/s{node}.out"
        log_files.append(log_file)
        err_file: str = f"{par_dir}/logs/s{node}.err"
        err_files.append(err_file)

        getPopen(ndn.net[node], 
            (f"python {curr_dir}/ndn_{ndn_config['protocol']}_server.py "
            f"{ndn_config['benchmark'] if 'benchmark' in ndn_config.keys() else ndn_config['function']} "
            f"{par_dir} {i} {True if 'pcap' in ndn_config['other'] else False} server"), 
            stdout=open(log_file, "w"), stderr=open(err_file, "w"))
        
        # if "pcap" in ndn_config["other"]:
        #     ifconfig: list[str] = popen(f"ifconfig").read().split("\n")
        #     for line in ifconfig:
        #         print(f"line: {line}")
        #         if line[:3] == "eth":
        #             intf: str = line.split(":")[0]
        #             print(f"interface: {intf}.")
        #             print(f"path: {par_dir}/pcaps/{ndn_config['protocol']}/s{node}-{intf}.pcap")
        #             getPopen(ndn.net[node], 
        #     ndn.net[node].cmd(
        #         (f"tcpdump -n -i s{node}-eth{0} -w "
        #             f"{par_dir}/pcaps/{ndn_config['protocol']}/s{node}-{intf}.pcap &"))
                    
        print(f"Server {i} node:\t{node}.")
    
    # Create clients
    for i in range(ndn_config["clients"]):
    # for i, node in enumerate(single_link_nodes):
        node: int = choice(single_link_nodes)   # Choose random single-link node.
        single_link_nodes.remove(node)
        nodes_in_test.append((node, "c"))

        log_file: str = f"{par_dir}/logs/c{node}.out"
        log_files.append(log_file)
        err_file: str = f"{par_dir}/logs/c{node}.err"
        err_files.append(err_file)

        getPopen(ndn.net[node], 
            (f"python {curr_dir}/ndn_{ndn_config['protocol']}_client.py "
            f"{ndn_config['benchmark'] if 'benchmark' in ndn_config.keys() else ndn_config['function']} "
            f"{par_dir} {i} {True if 'pcap' in ndn_config['other'] else False} client"), 
            stdout=open(log_file, "w"), stderr=open(err_file, "w"))
        
        # if "pcap" in ndn_config["other"]:
        #     ifconfig = popen(f"ifconfig").read()
        #     for intf in ifconfig:
        #         if "eth" in intf:
        #             ndn.net[node].cmd(
        #                 (f"tcpdump -n -i {intf} -w "
        #                  f"{par_dir}/pcaps/{ndn_config['protocol']}/c{intf}.pcap &"))
        
        print(f"Client {i} node:\t{node}.")
    
    # Wait.
    timer = 300
    print(f"Timer set: {timer} seconds")  
    sleep(timer)
    # MiniNDNCLI(ndn.net)
    
    # for node, role in nodes_in_test:
    #     getPopen(ndn.net[node],
    #              "nfdc fib", stdout=open(f'{par_dir}/logs/{role}{node}.fib', "w"))
    
    # Terminate Test.
    ndn.stop()

    # Post-test checks for completeness.
    not_complete: list[str] = []    # Hosts that didn't reach the end of their scriprs.
    had_errors: list[str] = []      # Hosts that ran into errors.
    
    # log_files: list[str] = [str(file) for file in Path(f"{par_dir}/logs").rglob("*.log") if file.is_file()]
    # err_files: list[str] = [str(file) for file in Path(f"{par_dir}/logs").rglob("*.err") if file.is_file()]
    
    for log_file in log_files:
        with open(log_file, "r") as f:
            if "End of script." not in f.read():
                not_complete.append(log_file.split("/")[-1].split(".")[0])
    
    for err_file in err_files:
        with open(err_file, "r") as f:
            if len(f.readlines()) > 0:
                had_errors.append(err_file.split("/")[-1].split(".")[0])
    
    print("Test completed fully." if len(not_complete) == 0 else 
            f"Hosts that failed to complete: {', '.join(not_complete)}.")
    print("Test had no errors." if len(had_errors) == 0 else 
            f"Hosts that had errors: {', '.join(had_errors)}.")
