from multiprocessing import Pipe #, Process
from sys import argv
from types import FunctionType

from ndn.appv2 import ReplyFunc, PktContext

from ndn_framework.ndn_utility import print_time_message
from ndn_framework.ndn_app import Sender, Receiver, APP_TYPE
from ndn_framework.ndn_client import NDN_Client
from ndn_framework.ndn_host import NDN_Host


class NDN_FM_Client(NDN_Client):
    def __init__(self, task: str, path_to_code: str, context: dict[str, str]) -> None:
        super().__init__(task, path_to_code, context)
        if "order" in context.keys():
            self.order = context["order"]

    # PARENT OVERRIDES
        
    def _setup_task_(self) -> None:
        # Add Results receiver.
        self.results_prefix = f"/RESULT/ndn_rpc/{self.task}"
        self.identifier = f"c{self.order}"
        self.results_dict: dict = {}    # Dict to store known results.
        self.receiver = self.__create_run_ndnapp__(APP_TYPE.RECV, 
            f"{self.results_prefix}/{self.identifier}", wait_to_finish=False)
        
        # Establish a connection between RECV and SEND processes.
        self.recv_conn, self.send_conn = Pipe()

    def _run_task_(self, func_num) -> dict:
        # FM: Client sends an Interest to acquire a function.
        #     RPC (FM) Name convention = "/FUNC/<func_name>"
        #     Func Name convention = "<func_prefix>/<func_suffix>"

        res_data: dict = {"result": None}   # Dict object for parent class..

        # Check if result has already been obtained.
        if f"dummy{func_num}" in self.results_dict.keys():
            print_time_message(f"dummy{func_num} has already been obtained: {self.results_dict[f'dummy{func_num}']}.")
            res_data["result"] = self.results_dict[f"dummy{func_num}"]
            return res_data

        # Gather prefixes of other client results servers.
        results_servers: list[str] = self.__get_full_prefix__(self.results_prefix, return_all=True)
        # Remove self.
        if f"{self.results_prefix}/{self.identifier}" in results_servers:
            results_servers.remove(f"{self.results_prefix}/{self.identifier}")
        
        # Check if result has already been calculated.
        res: int | float | str | None = None
        print_time_message(f"Checking other clients for result of dummy{func_num}..")
        for results_server in results_servers:
            self.__create_run_ndnapp__(APP_TYPE.SEND, results_server, func_num)
            res = self.recv_conn.recv()
            print_time_message(f"Res obtained from {results_server}: {res}.")
            if res is not None:
                self.results_dict[f"dummy{func_num}"] = res
                print_time_message("Result saved.")
                res_data["result"] = res
                return res_data
        
        # Calculate result if not obtained from other clients.
        rpc_prefix: str = f"{self.func_prefix}/{self.func_names[func_num-1]}"
        print_time_message("Acquiring function.")
        self.__create_run_ndnapp__(APP_TYPE.SEND, rpc_prefix)
        func: FunctionType = self.recv_conn.recv()
        print_time_message(f"Func obtained: {type(func)}.")

        print_time_message(f"Calculating dummy{func_num}..")
        if func_num == 1:
            res = func(10)
        if func_num == 2:
            res = func(10.0)
        if func_num == 3:
            res = func("Hello World!")
        
        print_time_message(f"Result: {res}. Saving.")
        self.results_dict[f"dummy{func_num}"] = res   
        res_data["result"] = res
        return res_data       

        # if self.task in ["average_pixel", "desaturate_image"]:
        #     self.__create_run_ndnapp__(APP_TYPE.SEND, results_server, "coffee-small.jpg")                
        # elif self.task == "color_image":
        #     self.__create_run_ndnapp__(APP_TYPE.SEND, results_server, (0,150,150))
                    
        # if res is not None:
        #     if self.task in ["average_pixel", "desaturate_image"]:
        #         self.results_dict["coffee-small.jpg"] = res     
        #     elif self.task == "color_image":
        #         self.results_dict[(0,150,150)] = res

            # return  # Don't need to continue.

        # if self.task in ["average_pixel", "desaturate_image"]:
        #     with open(f"{self.path_to_code}/images/coffee-small.jpg", "rb") as f_in:                
        #         if self.task == "average_pixel":
        #             res: tuple[int] = func(f_in.read())
        #             print_time_message(f"Result: {res}")
        #         else:
        #             res: bytes = func(f_in.read())
        #             out_path = f"{self.path_to_code}/images/fm-coffee-small-desat.jpg"
        #             with open(out_path, "wb") as f_out:
        #                 f_out.write(res)
        #             print_time_message(f"Data written out to: {out_path}.")
        #         self.results_dict["coffee-small.jpg"] = res # Store for res sharing.
        # elif self.task == "color_image":
        #     res: bytes = func((0,150,150))
        #     out_path = f"{self.path_to_code}/images/fm-color-image.jpg"
        #     with open(out_path, "wb") as f_out:
        #         f_out.write(res)
        #         print_time_message(f"Data written out to: {out_path}.")
        #     self.results_dict[(0,150,150)] = res

    def _shutdown_task_(self) -> None:
        # Clean up connection.
        self.send_conn.close()
        self.recv_conn.close()

    def _after_interest_task_(self, recv_app: Receiver, name: str, params: dict | None, reply: ReplyFunc, context: PktContext) -> dict:        
        if "RESULT" in name:
            suffix = NDN_Host.__get_suffix__(name, self.results_prefix)
            # if type(suffix) == str:
            #     suffix = suffix.split("/")[-1]
            # # print(f"suffix (before): {suffix}")
            # if "%28" in suffix:
            #     suffix = suffix.replace("%28", "(")
            #     if "%29" in suffix:
            #         suffix = suffix.replace("%29", ")")
            #     if "%2C" in suffix:
            #         suffix = suffix.replace("%2C", ",")
            # print(f"suffix (after): {suffix}")
            
            if f"dummy{suffix}" in self.results_dict.keys():
                return {"result": self.results_dict[suffix]}
            else:
                return {"error": "Result not found."}
        else:
            # print_time_message("Unexpected Interest name.")
            return {"error": "Unexpected Interest name."}

    def _after_data_task_(self, send_app: Sender, name: str, content: dict, context: PktContext) -> None:
        # FM: Client is waiting for function to arrive as a result of their RPC request.
        #      Result Name convention = "/FUNC/<rpc_name>"
        if "FUNC" in name:
            if "func" in content.keys():
                self.send_conn.send(content["func"])
            else:
                print("No func obtained.")
        elif "RESULT" in name:
            if "result" in content.keys():
                self.send_conn.send(content["result"])
            else: 
                self.send_conn.send(None)
        else:
            print_time_message(f"Unexpected Data name: {name}")

# MAIN SCRIPT

if __name__ == "__main__":
    print_time_message(f"Creating an NDN Function Client using FM protocol.")    
    #ndn_fwh_client = NDN_FWH_Client("__test_fwh_cli_ser__", "", {})
    ndn_fm_client = NDN_FM_Client(argv[1], argv[2], {"order": argv[3]})
    ndn_fm_client.run()
    print_time_message("End of script.")   
