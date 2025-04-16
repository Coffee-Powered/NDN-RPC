from sys import argv
# from multiprocessing import Pipe
# import asyncio

from ndn.appv2 import ReplyFunc, PktContext #, NDNApp, pass_all

from ndn_framework.ndn_utility import print_time_message
from ndn_framework.ndn_app import Sender, Receiver #, APP_TYPE
from ndn_framework.ndn_server import NDN_Server
from ndn_framework.ndn_host import NDN_Host


# NDN Function Server using FM protocol.
class NDN_FM_Server(NDN_Server):
    def __init__(self, task: str, path_to_data: str, context: dict[str, str]) -> None:
        super().__init__(task, path_to_data, context)
        
    # PARENT OVERRIDES
        
    def _setup_task_(self) -> None:
        pass

    def _run_task_(self) -> None:
        pass

    def _shutdown_task_(self) -> None:
        pass

    def _after_interest_task_(self, recv_app: Receiver, name: str, params: dict | None, reply: ReplyFunc, context: PktContext) -> dict:
        # FM:  Server sends the function specified in the RPC request.
        #      RPC (FM) Name convention = "/FUNC/<func_name>"
        #      Function Name convention = "<func_prefix>/<func_suffix>"
        
        if "FUNC" not in name:
            return {"error": "Unexpected Interest name."}
        
        func_suffix: str | None = NDN_Host.__get_suffix__(name, f"/FUNC/{self.func_prefix}/")
        print_time_message(f"Function requested: {func_suffix}.")

        if func_suffix not in self.func_dict.keys():
            return {"error": "Unrecognized function."}
        
        # Send function.
        print_time_message(f"Sending function: {func_suffix}.")
        return {"func": self.func_dict[func_suffix]}
    
    def _after_data_task_(self, send_app: Sender, name: str, content: dict, context: PktContext) -> None:
        pass


# MAIN SCRIPT


if __name__ == "__main__":
    print_time_message(f"Creating an NDN Function Server using FM protocol.")    
    ndn_fm_server = NDN_FM_Server("fm_srv", "", {"stay_open": argv[1], "clients": argv[2]})
    ndn_fm_server.run()
    print_time_message("End of script.")   

