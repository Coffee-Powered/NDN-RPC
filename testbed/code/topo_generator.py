from json import dump
from pathlib import Path

curr_dir: Path = Path(__file__).resolve().parent

# from fnss import parse_rocketfuel_isp_latency

# # Parse topology data from source files.
# topo = parse_rocketfuel_isp_latency(f"{curr_dir}/data/1239_latencies.intra",
#                                     f"{curr_dir}/data/1239_weights.intra")

# print(dir(topo))
# print(topo.nodes)               # list[int]
# print(topo.edges)               # list[tuple[int]]
# print(topo.edges.data(True))    # list[int | dict[str, int | float]]
# print(topo.graph)               # dict[str, str]    
# print(topo.get_edge_data(0, 10381))

# # Generate nodes and links dict.
# topo_dict: dict[str, list[dict]] = {"hosts": [], "links": []}

# for node in topo.nodes:
#     topo_dict["hosts"].append({"id": str(node)})

# for src, dest, attrs in topo.edges(data=True):
#     for k, v in attrs.items():
#         attrs[k] = str(v)
#     link = {"src": str(src), "dest": str(dest), "attrs": attrs}
#     topo_dict["links"].append(link)

# # Save as JSON.
# with open(f"{curr_dir}/data/1239.topo", "w") as f:
#     dump(topo_dict, f)

with open(f"{curr_dir}/data/1239_latencies.intra") as f:
    lines = f.readlines()
    hosts: list[str] = []
    connections: dict[str, list[tuple[str, int]]] = {}
    for line in lines:
        try:
            src, dst, lat = line.split(" ")
            src = src.split(",")[-1]
            if src[0] == "+":
                src = src[1:]
            dst = dst.split(",")[-1]
            if dst[0] == "+":
                dst = dst[1:]
            lat = int(lat)
            
            if src not in hosts:
                hosts.append(src)
            if dst not in hosts:
                hosts.append(dst)
            if src not in connections.keys():
                connections["src"] = []
            if dst not in connections.keys():
                connections["dst"] = []
            
            connections["src"].append((dst, lat))
        except Exception as e:
            print(f"Error: {e}.")
            exit()

    print(hosts)
    print(connections)