from multiprocessing import Process #, Pipe
from sys import argv
# from random import randint
# from time import sleep

from ndn.appv2 import PktContext #, ReplyFunc

from ndn_framework.ndn_utility import print_time_message
from ndn_framework.ndn_app import APP_TYPE #, Sender, Receiver
from ndn_framework.ndn_client import NDN_Client
from ndn_framework.ndn_host import NDN_Host


class NDN_FWH_Client(NDN_Client):
    def __init__(self, task: str, par_dir: str, context: dict[str, str]) -> None:
            context["protocol"] = "fwh"
            super().__init__(task, par_dir, context)    
        
    @property
    def param_prefix(self) -> str:
        return self.__param_prefix__
    
    @param_prefix.setter
    def param_prefix(self, s: str) -> None:
        self.__param_prefix__ = s

    @property
    def recv_proc(self) -> Process:
        return self.__recv_proc__
    
    @recv_proc.setter
    def recv_proc(self, r: Process) -> None:
        self.__recv_proc__ = r

    # PARENT OVERRIDES
        
    def _setup_task_(self) -> None:
        # FWH: Client sets up a param server.
        #      Param Name convention = "/PARAM/<param_prefix>/<param_suffix>"
        self.param_prefix: str = f"/PARAM/ndn_rpc/cli_{self.order}/param"

        # Add Params receiver.
        self.recv_proc: Process = self.__create_run_ndnapp__(
            APP_TYPE.RECV, prefix=self.param_prefix, callback=self._param_callback_)
        
    def _make_rpc_(self, name: str) -> dict:
        # FWH: Client sends an Interest to initiate a function call.
        #      RPC (FWH) Name convention = "/FUNC/<func_name>/PARAM/<param_name>"
        #      Func Name convention = "<func_prefix>/<func_suffix>"
        #      Param Name convention = "<param_prefix>/<param_suffix>"
            
        # Make an RPC request.
        func_id: str = name.split("/")[-1]
        self.__create_run_ndnapp__(APP_TYPE.SEND, f"{name}{self.param_prefix}/{func_id}")
        res_data: dict = self.recv_conn.recv()
        return res_data

    def _shutdown_task_(self) -> None:
        self.recv_proc.join()
        self.recv_proc.close()

    def _param_callback_(self, name: str, params: dict) -> dict:
        # FWH: Client serves parameter data when a function server requests one.
        #      Param Name convention = "/PARAM/<param_prefix>/<param_suffix>"
        if "PARAM" not in name:
            return {"error": "Unexpected Interest name."}
        
        param_suffix = NDN_Host.__get_suffix__(name, f"{self.param_prefix}/")
        print_time_message(f"Param requested: {param_suffix}.")

        try:
            func_num = int(param_suffix[-1])
            if func_num == 1:
                return {"value": 10}
            if func_num == 2:
                return {"value": 10.0}
            if func_num == 3:
                return {"value": "Hello World!"}
        except:
            return {"error": f"Unexpected param name: {param_suffix}."}
            
    def _process_data_task_(self, name: str, content: dict, context: PktContext) -> None:
        # FWH: Client is waiting for data to arrive as a result of their RPC request.
        #      Result Name convention = "/FUNC/<rpc_name>"
        if "FUNC" in name:
            self.send_conn.send(content)    # Should be the result of RPC.
        else:
            print_time_message("Unexpected Data name.")


# MAIN SCRIPT


if __name__ == "__main__":
    print_time_message(f"Creating an NDN Function Client using FWH protocol.")    
    ndn_fwh_client = NDN_FWH_Client(argv[1], argv[2], {"order": argv[3], "pcap": argv[4], "role": argv[5]})
    ndn_fwh_client.run()
    print_time_message("End of script.")   
