import json
from pathlib import Path

curr_dir: Path = Path(__file__).resolve().parent
par_dir: Path = Path(curr_dir).resolve().parent
num_nodes: int = 20

with open(f'{par_dir}/data/1239.topo') as f:
    graph = json.load(f)
    connections: dict[int, list[int]] = {}
    
    # Populate connections dict with first n nodes.
    for node in graph['hosts']:
        if len(connections.keys()) < num_nodes:
            connections[node['id']] = []
        else:
            break

    # Gather lists of links for each node in set.
    for link in graph['links']:
        if link['src'] in connections.keys() and link['dest'] in connections.keys():
            connections[link['src']].append(link['dest'])
    
    # Search for nodes with a single link.
    single_link_nodes: list[str] = []
    for node, neighbours in connections.items():
        if len(neighbours) == 0:
            print(f"Node {node} has 0 neighbours: {neighbours[0]}.")
        elif len(neighbours) == 1:
            print(f"Node {node} has 1 neighbour: {neighbours[0]} (Their neighbours: {connections[neighbours[0]]}).")
            single_link_nodes.append(node)
    print(f"Single-link nodes: {single_link_nodes}.")