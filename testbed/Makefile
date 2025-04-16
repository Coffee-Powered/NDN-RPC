TOPO = ""
LATY = ""
LOOP = ""
SIZE ?= 0 	# Size of AS1239 topology, n nodes.
CLI  = ""	# Number of clients.
SRV  = ""	# Number of servers.
TASK = ""	# Task to perform.

# PCAPS = $(wildcard data/pcap/***/**/*.pcap)
# N_LOGS = $(wildcard data/log_net/***/**/*.log)
# P_LOGS = $(wildcard data/log_proc/***/**/*.log)

# CSVS = $(patsubst data/pcap/%.pcap,data/csv/%.csv,$(PCAPS))
# CSVS = $(subst pcap,csv,$(PCAPS))

check_int_args:
	@if ! echo $(SIZE) | grep -qE '^[0-9]+$$'; then \
		echo "ERROR: SIZE arg is not an integer: $(SIZE)."; \
		exit 1; \
	fi
	@if ! echo $(CLI) | grep -qE '^[0-9]+$$'; then \
		echo "ERROR: CLI arg is not an integer: $(CLI)."; \
		exit 1; \
	fi
	@if ! echo $(SRV) | grep -qE '^[0-9]+$$'; then \
		echo "ERROR: SRV arg is not an integer: $(SRV)."; \
		exit 1; \
	fi

run: check_int_args
#	mkdir -p data/log_net/$(TOPO)/$(LATY) data/log_proc/$(TOPO)/$(LATY) data/pcap/$(TOPO)/$(LATY) 
	sudo python code/rpc2_minindn.py size=$(SIZE) cli=$(CLI) srv=$(SRV) $(TASK)

# analyse: $(CSVS)
# python src/python/data_analyser.py $(CSVS)

# clean: 
# 	rm -f $(PCAPS)
# 	rm -f $(N_LOGS)
# 	rm -f $(P_LOGS)
	
# data/csv/%.csv: data/pcap/%.pcap
# 	tshark -r $< -T fields -E separator=, -e _ws.col.No. -e _ws.col.Time -e ndn > $@
	
# pythonpath:
# 	export PYTHONPATH=$PYTHONPATH:/home/vagrant/.local/lib/python3.11/site-packages

# test: src/python/test.py
# 	python3 src/python/test.py
