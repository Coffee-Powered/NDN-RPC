# Common functionality for Consumer and Producer.


from datetime import datetime, timedelta
from os import popen
from time import sleep
from types import FunctionType, CoroutineType
import asyncio
#from multiprocessing import Process

from ndn.app import NDNApp
from ndn.encoding import Name
from ndn.types import InterestNack, InterestTimeout #, InterestCanceled, ValidationFailure


def time_print(message: str) -> None:
    time = datetime.now().time()
    print(f"[{time}] {message}")

def try_express_interest(prefix: str, suffix: str | None, on_data: FunctionType) -> None:
    '''
    Function that will attempt to send an Interest. 
    Will first check if specified prefix is found in the NDNApps FIB table, then will create 
    a full name by joining the prefix and suffix args (will add a / between them). 
    If prefix is not found within 30 seconds, will print a fail message and return.
    If a Data packet is received then will call on_data function, on_data must accept 4 args: 
    app, data_name, meta_data and content.
    If a Data packet is not received then it will retry up to 5 times before printing a fail 
    message and returning.
    '''

    time_print(f"Searching for prefix: {prefix}")
    prefix_found: bool = True

    # Wait for name to appear in FIB table..
    datetime_start = datetime.now()
    while prefix not in popen(f"nfdc fib").read():
        sleep(0.1)
        time_lapsed: timedelta = datetime.now() - datetime_start
        if time_lapsed.total_seconds() > 30:
            # Too long.
            prefix_found = False
            break
    time_diff: timedelta = datetime.now() - datetime_start

    if prefix_found:
        time_print(f"Prefix found, time taken: {time_diff.total_seconds()} seconds.")
        name_str: str = prefix if suffix is None else "/".join([prefix, suffix])  

        app: NDNApp = NDNApp()
        app.run_forever(my_express_interest(app, name_str, on_data))
        #app.run_forever(after_start=my_express_interest(app, name_str, on_data))
    else:
        time_print(f"Unable to find prefix..")
    
async def my_express_interest(app: NDNApp, name_str: str, on_data: FunctionType) -> None:
    retries: int = 0
    while retries < 5:
        try:
            time_print(f"Expressing interest for: {name_str}.")
            name_data, meta_info, content = await app.express_interest(
            Name.from_str(name_str), must_be_fresh=True, can_be_prefix=False,
            # Interest lifetime in ms
            lifetime=6000)
            # Print out Data Name, MetaInfo and its conetnt.
            on_data(app, name_data, meta_info, content)
            break
        except InterestNack as e:
            # A NACK is received
            time_print(f'Nacked with reason={e.reason}')
            sleep(0.5)
            retries += 1
        except InterestTimeout:
            # Interest times out
            time_print(f'Timeout.')
            retries += 1
        #except InterestCanceled:
        #    # Connection to NFD is broken
        #    time_print(f'Canceled')
        #except ValidationFailure:
        #    # Validation failure
        #    time_print(f'Data failed to validate')

def advertise_prefix(prefix: str, on_int: FunctionType | CoroutineType) -> None:
    time_print(f"Advertising the prefix: {prefix}")
    
    app = NDNApp()
    @app.route(prefix)
    def on_interest(name_int, interest_param, application_param):
        #if type(on_int) is CoroutineType:
        #    time_print("Coroutine callback.")
        #    asyncio.run(on_int(app, name_int, interest_param, application_param))
        #else:
        #    time_print("Function callback.")
        on_int(app, name_int, interest_param, application_param)
    
    #app.register(Name.from_str(prefix), on_interest)
    popen(f"nlsrc advertise {prefix}")  # Necessary to propagate prefix.
    
    time_print("Waiting..")      
    app.run_forever()