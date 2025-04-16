# Example code from:
# https://python-ndn.readthedocs.io/en/latest/src/examples/basic_app.html#connect-to-nfd


#from datetime import datetime, timedelta
#from time import sleep
#from os import popen
import asyncio 

from ndn.app import NDNApp
from ndn.encoding import Name
#from ndn.types import InterestNack, InterestTimeout #, InterestCanceled, ValidationFailure

from img_common import time_print, try_express_interest, advertise_prefix


#app = NDNApp()

param_name: str | None = None
res_name: str | None = None

def on_data(app_con: NDNApp, name_data: Name, meta_data, content: memoryview):
    time_print(f'Data received.')
    name_str: str = Name.to_str(name_data)
    time_print(f' - Name: {Name.to_str(name_str)}')
    #print(meta_info)
    time_print(f' - Content: {content.tobytes().decode()}')
    
    if "FUNC" in name_str:
        for word in content.tobytes().decode().split():
            if "PARAM" in word:
                time_print(f"Obtained param name: {word}")
                global param_name   # Needed for modifying variable outside function..
                param_name = word
            if "RES" in word:
                time_print(f"Obtained results name: {word}")
                global res_name     # Needed for modifying variable outside function..
                res_name = word
    elif "RES" in name_str:
        pass
    else:
        time_print(f"Unable to process name: {name_str}.")

    app_con.shutdown()

def on_int(app_pro: NDNApp, name_int: Name, interest_param, application_param):
    name_str: str = Name.to_str(name_int)
    time_print(f"Interest received, Name: {name_str}.")
    msg: str

    if "PARAM" in name_str:
        param_name: list[str] = name_str.split("PARAM/")[-1]
        time_print(f"PARAM: {param_name}")
        if "coffee" in param_name:
            app_pro.put_data(name_int, content=bytes("This is a coffee message."), freshness_period=10000)
    else:
        msg = "Unable to process name."
        time_print(msg)
        app_pro.put_data(name_int, content=bytes(msg), freshness_period=10000)
    
    app_pro.shutdown()

### Main ###


# Make an RPC request.
#asyncio.run(try_express_interest('FUNC/average_pixel', 'ARG/caller/coffee', on_data))
try_express_interest('FUNC/average_pixel', 'ARG/caller/coffee', on_data)

if param_name is not None:
    # FWH: Make Param server.
    advertise_prefix(param_name, on_int)
else:
    time_print("Param name is not defined.")

# FWH: Retrieve RPC result.
#if res_name is not None:
#    try_express_interest(res_name, None, on_data)
#else:
#    time_print("Result name is not defined.")

time_print("End of script.")