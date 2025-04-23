# Steps to run

vagrant up 

vagrant ssh

git clone https://github.com/Coffee-Powered/NDN-RPC.git

cd NDN-RPC/testbed

make run TASK="sprintlink fwh" CLI=1 SRV=1 SIZE=10
