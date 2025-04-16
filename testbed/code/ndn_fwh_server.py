# from multiprocessing import Pipe
from sys import argv
from pathlib import Path
# from types import FunctionType
# import asyncio
# from inspect import signature

from ndn.appv2 import PktContext #, ReplyFunc, NDNApp, pass_all

from ndn_framework.ndn_utility import print_time_message
from ndn_framework.ndn_app import APP_TYPE #, Sender, Receiver
from ndn_framework.ndn_server import NDN_Server
# from ndn_framework.ndn_host import NDN_Host


# NDN Function Server using FWH protocol.
class NDN_FWH_Server(NDN_Server):
    def __init__(self, task: str, par_dir: str, context: dict[str, str]) -> None:
        context["protocol"] = "fwh"
        super().__init__(task, par_dir, context)
        
    @property
    def param_data(self) -> dict:
        return self.__param_data__
    
    @param_data.setter
    def param_data(self, d: dict) -> None:
        self.__param_data__ = d

    # PARENT OVERRIDES
        
    def _setup_task_(self) -> None:
        pass

    def _run_task_(self) -> None:
        pass

    def _shutdown_task_(self) -> None:
        pass

    def _obtain_params_(self, name: str) -> dict:
        # FWH: Server sends an Interest to acquire parameter data for a function call.
        #      RPC (FWH) Name convention = "/FUNC/<func_name>/PARAM/<param_name>"
        #      Function Name convention = "<func_prefix>/<func_suffix>"

        # Identify function.
        if "PARAM" not in name:
            return {"error": "Missing PARAM component."}
        
        # Obtain params.
        param_dict: dict = {}   # Set up dict for ordered param passing..
        for param_name in name.split('/PARAM/')[1:]:
            print_time_message(f"Acquiring param: {param_name}..")
            self.__create_run_ndnapp__(APP_TYPE.SEND, f"/PARAM/{param_name}")
            
            # ------ This block of code does not work. ------
            # async def test(app: NDNApp):
            #     name, content, context = await app.express(
            #         name="/test/", validator=pass_all, lifetime=10000)

            # self.future = self.loop.create_task(
            #     recv_app.app.express(param_name, recv_app.validator))
            # asyncio.wait_for(self.future, None)
            # _, content, _ = self.future.result()
        
            # future = asyncio.ensure_future(recv_app.app.express(param_name, recv_app.validator), self.loop)
            # _, content, _ = future

            # if type(content) is memoryview:
            #     param_data = content.tobytes().decode()
            # elif type(content) is bytes:
            #     param_data = content.decode()
            # else:
            #     param_data = content
            # -----------------------------------------------

            params: dict = self.recv_conn.recv()
            for k,v in params.items():
                param_dict[k] = v
                print_time_message(f"Param \"{k}\" for {param_name} acquired.")
        
        return param_dict
            
    def _process_data_task_(self, name: str, content: dict, context: PktContext) -> None:
        # FWH: Server is waiting for parameter data to arrive for a function call.
        #      Param Name convention: "/PARAM/<param_name>"
        if "PARAM" in name:
            self.send_conn.send(content)
        else:
            print_time_message("Unexpected Data name.")


# MAIN SCRIPT


if __name__ == "__main__":
    print_time_message(f"Creating an NDN Function Server using FWH protocol.")
    ndn_fwh_server = NDN_FWH_Server(argv[1], argv[2], {"order": argv[3], "pcap": argv[4], "role": argv[5]})
    ndn_fwh_server.run()
    print_time_message("End of script.")   

