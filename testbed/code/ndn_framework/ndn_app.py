from json import loads as j_loads, dumps as j_dumps 
from pickle import loads as p_loads, dumps as p_dumps
from types import FunctionType
from enum import Enum 
import base64
import os
import asyncio

from ndn.encoding import Signer, Name, NonStrictName, BinaryStr
from ndn.types import Validator
from ndn.appv2 import NDNApp, PktContext, ReplyFunc

# Own library
from .ndn_utility import print_time_message


class APP_TYPE(Enum):
    '''
    Enum flag to simplify NDNApp behavioral properties by simply  declaring them as either a SEND 
    app or a RECV app.
    
    SEND: NDNApp behaves as a Consumer, will express an Interest and will typically wait for a 
    Data packet response.
    RECV: NDNApp behales as a Producer, will advertise a prefix to the network and wait for 
    Interests to be delivered to it.
    '''
    SEND = 0
    RECV = 1

    def __eq__(self, __value: object) -> bool:
        if type(__value) is not APP_TYPE:
            return False
        else:
            return self.name == __value.name
            
    def __ne__(self, __value: object) -> bool:
        return not self == __value

    def __str__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"
        
    def __repr__(self) -> str:
        return self.__str__() 
    

class Named_App:
    '''
    Class to encapsulate a single NDNApp instance with its properties, which an NDN_Host needs to 
    at least two instances of to simultaneously perform Interest packet requesting and Interest 
    packet serving.

    Attributes:
    app (NDNApp): Handle to the object which accesses the NDN.
    prefix (str): Name of the data to be accessed or served.

    Additional attributes:
    validator (Validator): Object to parse ingress packets and validate against specific criteria.
    signer (Signer): Object to add a signature to egress packets and add specific information to 
    pass validation.
    '''
    def __init__(self, app: NDNApp, prefix: str) -> None:
        print_time_message(f"Creating NDNApp..")
        self.app = app
        self.prefix = prefix

    @property
    def app(self) -> NDNApp:
        return self.__app__
    
    @app.setter
    def app(self, a: NDNApp) -> None:
        self.__app__ = a

    @property
    def prefix(self) -> str:
        return self.__prefix__
    
    @prefix.setter
    def prefix(self, p: str) -> None:
        self.__prefix__ = p

    @property
    def validator(self) -> Validator:
        return self.__validator__
    
    @validator.setter
    def validator(self, v: Validator) -> None:
        self.__validator__ = v

    @property
    def signer(self) -> Signer:
        return self.__signer__
    
    @signer.setter
    def signer(self, s: Signer) -> None:
        self.__signer__ = s

    def __run__(self, func: FunctionType = None) -> None:
        print_time_message(f"..Running NDNApp..")
        if func is None:
            self.__app__.run_forever()
        else:
            self.__app__.run_forever(after_start=func(self))
        
    def __shutdown__(self) -> None:
        print_time_message(f"..Shutting down NDNApp.")
        self.__app__.shutdown()


class Sender(Named_App):
    '''
    Attributes:
    add (NDNApp): App instance to be wrapped.
    prefix (str): Name of network object/service to be acquired/accessed.
    must_be_fresh (bool): Flag to specify that Interest must reach the source (if True).
    freshness (int): How long (ms) an Interest packet can stay pending.

    Additional attributes:
    suffix (str): Name to append to the end of the prefix, to add specifics to the Name being formed.
    params (dict): An object to be delivered to the Producer containing parameter information, 
    data should be represented by a dict object that can be stringified by the json module.
    '''
    def __init__(self, app: NDNApp, prefix: str, must_be_fresh: bool = False, 
                 freshness: int = 0) -> None:
        super().__init__(app, prefix)
        if must_be_fresh:
            #print("must be fresh")
            self.must_be_fresh = must_be_fresh
            self.freshness = freshness

    @property
    def must_be_fresh(self) -> bool:
        return self.__must_be_fresh__
    
    @must_be_fresh.setter
    def must_be_fresh(self, m: bool) -> None:
        self.__must_be_fresh__ = m

    @property
    def freshness(self) -> int:
        return self.__freshness__
    
    @freshness.setter
    def freshness(self, f: int) -> None:
        self.__freshness__ = f

    @property
    def suffix(self) -> str:
        return self.__suffix__
    
    @suffix.setter
    def suffix(self, s: str) -> None:
        self.__suffix__ = s
        
    @property
    def params(self) -> dict:
        return self.__params__
     
    @params.setter
    def params(self, p: dict) -> None:
        self.__params__ = p

    def params_as_str(self) -> str:
        if "data" in self.params.keys():
            #print(f"Before encoding: {self.__data__['data']}")
            self.params["data"] = base64.b64encode(self.params["data"]).decode()
            #print(f"After encoding: {self.__data__['data']}")
        
        return j_dumps(self.params)
    

class Receiver(Named_App):
    '''
    Attributes:
    add (NDNApp): App instance to be wrapped.
    prefix (str): Name of network object/service to be acquired/accessed.

    Additional attributes:
    data (dict): An object to be delivered to the Consumer that requested it, data should be 
    represented by a dict object that can be stringified by the json module.
    '''
    def __init__(self, app: NDNApp, prefix: str) -> None:
        super().__init__(app, prefix)
        
    @property
    def data(self) -> dict:
        return self.__data__
    
    @data.setter
    def data(self, d: dict) -> None:
        self.__data__ = d

    def data_as_str(self) -> str:
        if "data" in self.data.keys():
            #print(f"Before encoding: {self.__data__['data']}")
            self.data["data"] = base64.b64encode(self.data["data"]).decode()
            #print(f"After encoding: {self.__data__['data']}")
        if "func" in self.data.keys():
            return p_dumps(self.data)
        
        return j_dumps(self.data)
    
    def advertise_prefix(self, prefix: str, callback: FunctionType):
        # Explicitly tell NLSR to advertise name to the network..
        # TODO: Handle potential errors here.
        print_time_message(f"Advertising the prefix: {prefix}")
#        self.logger_proc.record("ADV1", f"Advertising prefix: {receiver.prefix}")
        os.popen(f"nlsrc advertise {prefix}")

        # New way to register a prefix and bind a callback (doesn't work).
        # self.app.register(prefix)
        # self.app.attach_handler(prefix, callback)

        # Callback
        @self.app.route(prefix, self.validator if hasattr(self, "validator") else None)
        def on_interest(name: NonStrictName, params: BinaryStr | None, reply: ReplyFunc, context: PktContext):
            callback(name, params, reply, context)
        
    def send_data(self, name: str, reply: ReplyFunc):
        # Send Data packet if content was returned.
        if self.data is not None:
#                self.logger_proc.record("ENC1", f"Encoding content for name: {name_str}")
#                self.logger_proc.record("ENC2", f"Encoding finished for name: {name_str}")
            #print_time_message(f"About to send: {recv_app.data_as_str()}")
            reply(self.app.make_data(name=name, content=self.data_as_str(), signer=self.__signer__))
            print_time_message("Data packet sent.")
        else:
            # Response will be handled elsewhere by application..
            print_time_message("Delaying response..")  

def decode_data(data: bytes | memoryview) -> dict | None:
    # No clean way to determine whether data was encoded with json or pickle..
    # Just have to try json first and then try again with pickle.
    try:
        return j_loads(data.tobytes() if type(data) == memoryview else data)
    except:
        try:
            return p_loads(data.tobytes() if type(data) == memoryview else data)
        except Exception as e:
            print(f"Error: {e}")
            return None