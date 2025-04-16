# from sys import argv
# from pathlib import Path
from multiprocessing import Process, Pipe
# from types import FunctionType
from time import sleep 
from random import random, randint, choice
#import asyncio
from types import FunctionType

from ndn.appv2 import PktContext #, ReplyFunc

from .ndn_host import NDN_Host #, NDN_Logger
from .ndn_app import APP_TYPE #, Sender, Receiver
from .ndn_utility import print_time_message #, get_datetime, get_time_diff
# from . import functions
# from .sprintlink_functions import get_function_names

class NDN_Server(NDN_Host):
    def __init__(self, task: str, par_dir: str, context: dict[str, str]) -> None:
        # NDN
        super().__init__("server", task, par_dir, context)

        if not hasattr(self, "order"):
            print_time_message("WARNING: Server is missing an order number.")
        
    @property
    def recv_proc(self) -> Process:
        return self.__recv_proc__
    
    @recv_proc.setter
    def recv_proc(self, r: Process) -> None:
        self.__recv_proc__ = r

    # PARENT OVERRIDES

    def _setup_(self) -> None:
        self.func_prefix: str  = f"/FUNC/ndn_rpc/srv_{self.order}"
        self._setup_task_()  # OVERRIDE THIS

        # Establish a connection between RECV and SEND processes.
        self.recv_conn, self.send_conn = Pipe()
                
        # Create function receivers to serve Clients. (!!! This HAS to done last !!!)
        print_time_message("Creating receiver apps.")
        self.recv_procs: list[Process] = []

        # Advertise named functions to the network.
        callbacks: list[str] = [c for c in dir(self) if "callback" in c]
        min_procs: int = 1

        for i, callback in enumerate(callbacks):
            # Remaining callbacks: len(callbacks) - i
            # Accumulated Procs + Min: min_procs + len(self.recv_procs)
            # if random() > 0.5 or len(callbacks) - i <= min_procs + len(self.recv_procs):
            func_name: str = f"{self.func_prefix}/{callback[1:-1].split('_')[0]}"
            func: FunctionType = getattr(self, callback)
            recv_proc: Process = self.__create_run_ndnapp__(
                APP_TYPE.RECV, prefix=func_name, callback=func)
            self.recv_procs.append(recv_proc)
            # else:
            #     print_time_message(f"Not advertising {callback}.")

    def _run_(self) -> None:
        # Perform run-time routines.
        self._run_task_()       # OVERRIDE THIS
        
    def _shutdown_(self) -> None:
        self._shutdown_task_()  # OVERRIDE THIS
        
        # Clean up connection.
        self.send_conn.close()
        self.recv_conn.close()

        # Clean up Receiver proc.
        for recv_proc in self.recv_procs:
            recv_proc.join()
            recv_proc.close()
        
    def _dummy1_callback_(self, name: str, params: dict | None) -> dict:
        print_time_message("Function called: dummy1.")
        if params is None:
            params: dict = self._obtain_params_(name)
        print(f"Params: {params}")
        if "value" in params.keys():
            sleep(5)
            value = params['value']
            if value == 0:
                return {"result": 0}
            else:
                return {"result": randint(-value if value > 0 else value, value if value > 0 else -value)}
        else:
            return {"error": "Unable to obtain a \"value\" to pass to function."}
        
    def _dummy2_callback_(self, name: str, params: dict | None) -> dict:
        print_time_message("Function called: dummy2.")
        if params is None:
            params: dict = self._obtain_params_(name)
        print(f"Params: {params}")
        if "value" in params.keys():
            sleep(5)
            value = params['value']
            parity = (randint(0, 1)*2)-1    # +/- 1
            return {"result": random()*value*parity}
        else:
            return {"error": "Unable to obtain a \"value\" to pass to function."}

    def _dummy3_callback_(self, name: str, params: dict | None) -> dict:
        print_time_message("Function called: dummy3.")
        if params is None:
            params: dict = self._obtain_params_(name)
        print(f"Params: {params}")
        if "value" in params.keys():
            sleep(5)
            value = params['value']
            # if type(value) != str:
            #     return f"dummy3 needs a string input, received: {type(value)}."
            chars = [c for c in value]
            return {"result": "".join(choice(chars) for _ in range(10))}
        else:
            return {"error": "Unable to obtain a \"value\" to pass to function."}
        
    def _process_data_(self, name: str, content: dict, context: PktContext) -> None:
        # Obtain response message from Producer.
        if "message" in content.keys():
            print_time_message(content['message'])
        self._process_data_task_(name, content, context)

    # CHILD OVERRIDES

    def _setup_task_(self) -> None:
        raise NotImplementedError("_setup_task_ not implemented.")

    def _run_task_(self) -> None:
        raise NotImplementedError("_run_task_ not implemented.")

    def _shutdown_task_(self) -> None:
        raise NotImplementedError("_shutdown_task_ not implemented.")

    def _process_data_task_(self, name: str, content: dict, context: PktContext) -> None:
        raise NotImplementedError("_after_interest_task_ not implemented.")

    def _obtain_params_(name: str) -> dict:
        raise NotImplementedError("_obtain_params_ not implemented.")
