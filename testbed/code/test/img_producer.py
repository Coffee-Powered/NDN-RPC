# Example code from:
# https://python-ndn.readthedocs.io/en/latest/src/examples/basic_app.html#connect-to-nfd


#from os import popen
#from datetime import datetime
from dataclasses import dataclass
from types import FunctionType
from typing import Any 
#import asyncio
from asyncio import Task

from ndn.app import NDNApp
from ndn.encoding import Name

from img_common import time_print, advertise_prefix, try_express_interest
from functions import average_pixel


@dataclass
class Job:
    function: FunctionType
    arg_names: list[str] | None         # List match params to jobs.
    result_name: str
    args: dict[str, Any] | None = None  # Dict to match param names to values (might arrive out of order).
    result: Any = None
jobs: list[Job] = []


async def on_int(app_pro: NDNApp, name_int: Name, interest_param, application_param) -> None:
    msg: str
    name_str: str = Name.to_str(name_int)
    time_print(f"Interest received, Name: {name_str}.")
    
    # RPC name format: "FUNC/<func_name>/ARG/<arg1_name>/ARG/<arg2_name>/..."
    if "FUNC" in name_str:
        try:
            name_split: list[str] = name_str.split("/ARG/")
            func_name: str = name_split[0][6:]
            time_print(f"FUNC: {func_name}")

            # Function: average_pixel(<image_data>)
            if func_name == "average_pixel":
                if len(name_split) == 2:
                    # Add new RPC job to dict.
                    job = Job(average_pixel, [f"PARAM/{name_split[-1]}"], f"RES/{func_name}/{name_split[-1]}")
                    jobs.append(job)

                    # Close RPC request Interest.
                    msg = f"RPC request successful. Param required: {job.arg_names[0]}. Results name: {job.result_name}."
                    time_print(msg)
                    app_pro.put_data(name_int, content=msg, freshness_period=10000)
                    
                    # Obtain param for function, invoke func in on_data.
                    await try_express_interest(job.arg_names[0], None, on_data)
                    
                    time_print(f"Current args: {job.args}.")
                else:
                    raise Exception(f"Average_pixel requires exactly 1 arg, received: {len(name_split)-1}.")
        
            else:
                raise Exception(f"Function name is not recognised: {func_name}.")
            
        except Exception as e:
            time_print(f"Exception: {e.args[0]}")
            app_pro.put_data(name_int, content=e.args, freshness_period=10000)

    else:
        msg = "Unable to process name."
        time_print(msg)
        app_pro.put_data(name_int, content=msg, freshness_period=10000)
    
    app_pro.shutdown()

def on_data(app_con: NDNApp, name_data: Name, meta_data, content) -> None:
    time_print(f'Data received.')
    name_str: str = Name.to_str(name_data)
    time_print(f' - Name: {Name.to_str(name_str)}')
    #print(meta_info)
    #time_print(f' - Content: {bytes(content) if content else None}')
    
    if "PARAM" in name_str:
        arg_name: str = name_str.split("PARAM/")[-1]
        arg_found: bool = False
        for job in jobs:
            if arg_name in job.arg_names:
                time_print(f"Adding {arg_name} to job data.")
                job.args[arg_name] = content
                arg_found = True
        if not arg_found:
            time_print(f"Unable to find {arg_name} in current job list.")
    else:
        time_print(f"Unable to process name: {name_str}.")

    app_con.shutdown()

### Main ###
    
# Offer RPC services.
advertise_prefix('/FUNC/average_pixel', on_int)

time_print("End of script.")