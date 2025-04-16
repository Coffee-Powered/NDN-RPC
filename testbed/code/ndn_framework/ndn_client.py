#from os import popen
#from sys import argv
# from time import sleep
#from pathlib import Path
from multiprocessing import Pipe
from random import randint

from ndn.appv2 import PktContext #, ReplyFunc

from .ndn_host import NDN_Host
# from .ndn_app import APP_TYPE, Sender, Receiver
from .ndn_utility import print_time_message #, get_datetime, get_time_diff, generate_random
# from .sprintlink_functions import get_function_names

class NDN_Client(NDN_Host):
    def __init__(self, task: str, par_dir: str, context: dict[str, str]) -> None:
        # NDN
        super().__init__("client", task, par_dir, context)
        
        if not hasattr(self, "order"):
            print_time_message("WARNING: Client is missing an order number.")

    # PARENT OVERRIDES

    def _setup_(self) -> None:
        # Try to detect the presence of named functions..
        self.func_prefix: str = "/FUNC/ndn_rpc"
        # sleep(60)
        func_check: bool = self.__search_prefix__(self.func_prefix)
        if func_check:
            print_time_message(f"Prefixes containing \"{self.func_prefix}\" detected.")
        else:
            print_time_message(f"No prefixes containing \"{self.func_prefix}\" detected. Exiting.")
            exit()

        self._setup_task_()  # OVERRIDE THIS

        # Establish a connection between RECV and SEND processes.
        self.recv_conn, self.send_conn = Pipe()
        
    def _run_(self) -> None:
        # Make an RPC request.
        if self.task == "sprintlink":
            max_rpcs: int = 5
            for _ in range(max_rpcs):
                funcs: list[str] = self.__get_full_prefix__(self.func_prefix, True)
                func_select = randint(0, len(funcs)-1)
                print_time_message(f"Requesting RPC: {funcs[func_select]}..")
                res_data: dict = self._make_rpc_(funcs[func_select])  # OVERRIDE THIS
                if "result" in res_data.keys():
                    print_time_message(f"Result acquired: {res_data['result']}.")
                elif "error" in res_data.keys():
                    print_time_message(f"Error message obtained: {res_data['error']}.")
                else:
                    print_time_message(f"Unexpected data: {res_data}.")
 
    def _shutdown_(self) -> None:
        self._shutdown_task_()
        
        # Clean up connection.
        self.send_conn.close()
        self.recv_conn.close()

    def _process_data_(self, name: str, content: dict, context: PktContext) -> None:
        try:
            self._process_data_task_(name, content, context)    # OVERRIDE THIS
        except Exception as e:
            print_time_message(f"Unable to decode content: {e}")

    # CHILD OVERRIDES

    def _setup_task_(self) -> None:
        '''
        Method for child classes of NTS_Client to define the class task logic 
        that is performed during the _setup_ function call.

        Returns:
            None.
        '''
        raise NotImplementedError("_setup_task_ not implemented.")
         
    def _make_rpc_(func_name: str) -> dict:
        '''
        Method for child classes of NTS_Client to define the class task logic 
        that is performed during the _run_ function call.

        Returns:
            dict of RPC result.
        '''
        raise NotImplementedError("_run_task_ not implemented.")
    
    def _shutdown_task_(self) -> None:
        '''
        Method for child classes of NTS_Client to define the class task logic 
        that is performed during the _shutdown_ function call.

        Returns:
            None.
        '''
        raise NotImplementedError("_shutdown_task_ not implemented.")
        
    def _process_data_task_(self, name: str, content: dict, context: PktContext) -> None:
        '''
        Method for child classes of NTS_Client to define the class task logic 
        that is performed during the _after_data_ function callback.

        Returns:
            None.
        '''
        raise NotImplementedError("_after_data_task_ not implemented.")
    