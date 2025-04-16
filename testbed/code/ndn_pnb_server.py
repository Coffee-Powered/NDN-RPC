from sys import argv
# from multiprocessing import Pipe
# import asyncio
from inspect import signature

from ndn.appv2 import ReplyFunc, PktContext #, NDNApp, pass_all

from ndn_framework.ndn_utility import print_time_message
from ndn_framework.ndn_app import Sender, Receiver #, APP_TYPE
from ndn_framework.ndn_server import NDN_Server
from ndn_framework.ndn_host import NDN_Host


# NDN Function Server using FM protocol.
class NDN_PNB_Server(NDN_Server):
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
        # PNB: Server acquires parameter data from Interest packet name.
        #      RPC (PNB) Name convention = "/FUNC/<func_name>/PARAM/<param_data>"
        #      Function Name convention = "<func_prefix>/<func_suffix>"
        #      Param Data convention = "<param_key>/<param_value>"

        # Identify function.
        if "FUNC" not in name or "PARAM" not in name:
            return {"error": "Unexpected Interest name."}
    
        #Identify function.
        name_split_param = name.split("/PARAM/")
        func_suffix: str | None = NDN_Host.__get_suffix__(
            name_split_param[0], f"/FUNC/{self.func_prefix}/")
        if func_suffix not in self.func_dict.keys():
            return {"error": "Unexpected function name."}

        # Acquire params from name.
        param_dict: dict = {}   # Set up dict for ordered param passing..
        func_params = signature(self.func_dict[func_suffix]).parameters # Obtain func sig for param types..
        for param in name_split_param[1:]:
            k, v = param.split("/")
            if k in func_params.keys():
                # Obtain param type as specified by the function signature..
                param_type = str(func_params[k]).split(": ")[-1]
                try:
                    print(f"Before: {v}")
                    if "%20" in v:
                        v = v.replace("%20", " ")
                    if "%28" in v:
                        v = v.replace("%28", "(")
                    if "%29" in v:
                        v = v.replace("%29", ")")
                    if "%2C" in v:
                        v = v.replace("%2C", ",")
                    print(f"After: {v}")
                    
                    if v[0] == "(" and v[-1] == ")":
                        param_dict[k] = eval(v)
                    else:
                        # Dynamically convert param value from str to specified type..
                        param_dict[k] = getattr(__builtins__, param_type)(v)
                except:
                    return {"error": f"Failed to process param: {k}"}
            else:
                return {"error": f"Unexpected param: {k}"}
                
        # Invoke function.
        try:
            print_time_message(f"Invoking function: {func_suffix}.")
            result = self.func_dict[func_suffix](**param_dict)
            return {"data" if type(result) is bytes else "result": result}
        except Exception as e:
            return {"error": f"RPC runtime error: {e}"}
        
        # else:
        #     # Identify function. (No params.)
        #     func_suffix: str | None = NDN_Host.__get_suffix__(
        #         name, f"/FUNC/{self.func_prefix}/")
        #     if func_suffix not in self.func_dict.keys():
        #         return {"error": "Unrecognized function name."}
    
        #     # Invoke function. (No params.)
        #     print_time_message(f"Function requested: {func_suffix}.")
        #     try:
        #         return {"result": self.func_dict[func_suffix]()}
        #     except Exception as e:
        #         return {"error": f"RPC runtime error: {e}"}
        
    def _after_data_task_(self, send_app: Sender, name: str, content: dict, context: PktContext) -> None:
        pass


# MAIN SCRIPT


if __name__ == "__main__":
    print_time_message(f"Creating an NDN Function Server using PNB protocol.")    
    ndn_pnb_server = NDN_PNB_Server("pnb_srv", "", {"stay_open": argv[1], "clients": argv[2]})
    ndn_pnb_server.run()
    print_time_message("End of script.")   

