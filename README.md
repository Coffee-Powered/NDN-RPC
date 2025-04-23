# Steps to run

vagrant up 

vagrant ssh

git clone https://github.com/Coffee-Powered/NDN-RPC.git

cd NDN-RPC/testbed

make run TASK="sprintlink fwh" CLI=1 SRV=1 SIZE=10

## Change CLI, SRV and SIZE to whatever you want (max nodes: 315)
## Delete the SIZE variable and the network will default to using the full network.
