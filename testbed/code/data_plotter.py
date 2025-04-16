# import os
from sys import argv
import matplotlib.pyplot as plt 
from json import load
from pathlib import Path


plots: list[str] = ["fwh", "nsc", "fm", "pnb", "host"]
par_dir = Path(__file__).resolve().parent.parent


def get_data(plot: str) -> dict[str, list[float]]:
    if plot == "host":
        data_paths = [str(file) for file in Path(f"{par_dir}/data").rglob("*") if file.is_file()]
    else:
        data_paths = [str(file) for file in Path(f"{par_dir}/data/{plot}").rglob("*")]

    # Obtain data from files..    
    data_dict: dict[str, dict[str, dict[str, list[float]]]] = {}
    for data_path in data_paths:
        with open(data_path, "r") as f:
            data_dict["/".join(data_path.split("/")[-2:]).replace(".data", "")] = load(f)
    data_dict = dict(sorted(data_dict.items()))

    # Collect all the delta times..
    delta_times: dict[str, list[float]] = {}
    for host, host_data in data_dict.items():
        delta_times[host] = []
        for _, name_data in host_data.items():
            delta_times[host].extend(name_data["delta_times"])
    return delta_times

# def make_histogram(plot: str, data: dict) -> None:
#     for host_name, x in data.items():
#         plt.hist(x, bins=50, edgecolor='black')  # Adjust bins as needed

#         # Add labels and title
#         plt.title(f"Histogram of Interest-Data response times for {host_name}")
#         plt.xlabel('Response Times (s)')
#         plt.ylabel('Frequency')

#         plt.savefig(f"{os.getcwd()}/plots/{protocol}/{host_name}.png")
#         plt.clf()
        

def make_boxplot(plot: str, data: dict[str, list[float]], plot_config: dict[str, str]) -> None:
    labels = list(map(lambda s: s.split("/")[-1], list(data.keys())))
    datasets = list(data.values())
        
    box = plt.boxplot(datasets, showfliers=False)

    # Customize box colors
    # colors = ["lightblue", "lightgreen", "lightred", "lightpurple", "lightorange"]
    # for patch, color in zip(box['boxes'], colors):
    #     patch.set_facecolor(color)

    # Config plot settings.
    if "title" in plot_config.keys():
        plt.title(plot_config["title"])
    if "xlabel" in plot_config.keys():
        plt.xlabel(plot_config["xlabel"])
    if "ylabel" in plot_config.keys():
        plt.ylabel(plot_config["ylabel"])
    plt.xticks(ticks=list(range(1, len(labels)+1)), labels=labels)

    # Save fig.
    plt.savefig(f"{par_dir}/plots/latency/{plot if 'host' in plot else f'{plot}_only'}.png")


if __name__ == "__main__":
    box_config = {}
    box_config["ylabel"] = "Response Time (s)"

    if len(argv) == 1:
        for plot in plots:
            deltas = get_data(plot)

            if plot != "host":
                box_config["title"] = f"Response times for {plot.upper()} Hosts."
                box_config["xlabel"] = "Host"
                make_boxplot(plot, deltas, box_config)
            else:
                box_config["title"] = f"Response times for __host__ across protocols."
                box_config["xlabel"] = "Protocol"
            
    else:
        plot = argv[1]
        if plot not in plots:
            print(f"Error: Plot setting not recognised: {plot}.")
            exit()

        deltas = get_data(plot)
        
        if plot != "host":
            box_config["title"] = f"Response times for {plot.upper()} Hosts."
            box_config["xlabel"] = "Host"
            make_boxplot(plot, deltas, box_config)
        else:
            deltas_sorted: dict[str, dict[str, list[float]]] = {}   # Mixed data dict, needs sorting.
            for prot_host, host_deltas in deltas.items():
                protocol, host = prot_host.split("/")
                if host not in deltas_sorted.keys():
                    deltas_sorted[host] = {protocol.upper(): host_deltas}
                else:
                    deltas_sorted[host][protocol.upper()] = host_deltas
            
            box_config["xlabel"] = "Protocol"
            for host, host_deltas in deltas_sorted.items():
                box_config["title"] = f"Response times for {host} across protocols."
                make_boxplot(f"{plot}_{host}", host_deltas, box_config)
                plt.clf()   # Clear fig before looping.
            
