from multiprocessing import Pipe #, Process 
from sys import argv

from ndn.appv2 import ReplyFunc, PktContext

from ndn_framework.ndn_utility import print_time_message
from ndn_framework.ndn_app import Sender, Receiver, APP_TYPE
from ndn_framework.ndn_client import NDN_Client
#from ndn_framework.ndn_host import NDN_Host


class NDN_PNB_Client(NDN_Client):
    def __init__(self, task: str, path_to_code: str, context: dict[str, str]) -> None:
        super().__init__(task, path_to_code, context)

    # PARENT OVERRIDES
        
    def _setup_task_(self) -> None:
        # Establish a connection between RECV and SEND processes.
        self.recv_conn, self.send_conn = Pipe()

    def _run_task_(self, func_num) -> dict:
        # PNB: Client sends an Interest to initiate a function call.
        #      RPC (PNB) Name convention = "/FUNC/<func_name>/PARAM/<param_data>"
        #      Func Name convention = "<func_prefix>/<func_suffix>"
        #      Param Data convention = "<param_key>/<param_value>"
        
        # Make an RPC request.
        rpc_prefix: str = f"{self.func_prefix}/{self.func_names[func_num-1]}"
        
        if func_num == 1:
            rpc_suffix: str = f"PARAM/value/10"
        if func_num == 2:
            rpc_suffix: str = f"PARAM/value/10.0"
        if func_num == 3:
            rpc_suffix: str = f"PARAM/value/Hello World"
        
        self.__create_run_ndnapp__(APP_TYPE.SEND, rpc_prefix, rpc_suffix)
        res_data: dict = self.recv_conn.recv()
        return res_data

    def _shutdown_task_(self) -> None:
        # Clean up connection.
        self.send_conn.close()
        self.recv_conn.close()

    def _after_interest_task_(self, recv_app: Receiver, name: str, params: dict | None, reply: ReplyFunc, context: PktContext) -> tuple[dict | None, bool]:        
        pass

    def _after_data_task_(self, send_app: Sender, name: str, content: dict, context: PktContext) -> None:
        # PNB: Client is waiting for result to arrive as a result of their RPC request.
        #      Result Name convention = "/FUNC/<rpc_name>"
        if "FUNC" in name:
            self.send_conn.send(content)
        else:
            print_time_message("Unexpected Data name.")

# MAIN SCRIPT

if __name__ == "__main__":
    print_time_message(f"Creating an NDN Function Client using PNB protocol.")    
    ndn_pnb_client = NDN_PNB_Client(argv[1], argv[2], {})
    ndn_pnb_client.run()
    print_time_message("End of script.")   
