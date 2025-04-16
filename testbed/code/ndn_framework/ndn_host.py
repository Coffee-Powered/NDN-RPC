from os import popen

from time import sleep
from multiprocessing import Process
# from multiprocessing.managers import BaseManager
# from pathlib import Path
import base64
from types import FunctionType

from ndn.appv2 import PktContext, NDNApp, ReplyFunc, pass_all
from ndn.encoding import Name, NonStrictName, BinaryStr
from ndn.types import InterestNack, InterestTimeout, InterestCanceled, ValidationFailure

# Own library
from .ndn_app import APP_TYPE, Sender, Receiver, decode_data
from .ndn_utility import print_time_message #, get_datetime


class NDN_Host:
    '''
    Class to define and execute the TS application over NDN.

    Attributes:
    name (str): Name which to associate with the wrapped NDNApp instance.
    task (str): Name of task to be performed by this class instance (for debugging).
    '''
    def __init__(self, name: str, task: str, par_dir: str, context: dict[str, str]) -> None:
        self.name = name
        self.task = task
        self.par_dir = par_dir
        
        if "order" in context.keys():
            self.order = context["order"]
        if "pcap" in context.keys():
            self.do_pcap = context["pcap"]
        if "protocol" in context.keys():
            self.protocol = context["protocol"]
        if "role" in context.keys():
            self.role = context["role"]
    
    @property
    def name(self) -> str:
        return self.__name__
    
    @name.setter
    def name(self, n: str) -> None:
        self.__name__ = n

    @property
    def task(self) -> str:
        return self.__task__
    
    @task.setter
    def task(self, t: str) -> None:
        self.__task__ = t

    # CHILD OVERRIDES

    def _setup_(self) -> None:
        raise NotImplementedError("_setup_ not implemented.")
        
    def _run_(self) -> None:
        raise NotImplementedError("_run_ not implemented.")
    
    def _shutdown_(self) -> None:
        raise NotImplementedError("_shutdown_ not implemented.")
    
    def _process_data_(self, name: str, content: dict, context: PktContext) -> None:
        '''
        Method to be overridden by inheriting classes. Is called in the on_data callback when a 
        sender NDNApp receives a Data packet that responds to the Interest packet initially 
        expressed by the sender.

        Parameters:
            name (NonStrictName): Name of the Interest packet.
            content (BinaryStr | None): The content of the named data, encoded in binary.
        
        Returns:
            None.
        '''
        raise NotImplementedError("_after_data_ not implemented.")

    # MANAGEMENT

    def __setup__(self, time: float, max: int) -> None:
        # Setup tcpdump, if applicable.
        if self.do_pcap:
            print_time_message("Setting up packet capture.")
            ifconfig: list[str] = popen(f"ifconfig").read().split("\n")
            for line in ifconfig:
                print(f"line: {line}")
                if "-eth" in line:
                    intf: str = line.split(":")[0]
                    path: str = f"{self.par_dir}/pcaps/{self.protocol}/{'s' if self.role == 'server' else 'c'}{intf}.pcap"
                    print(f"interface: {intf}.")
                    print(f"path: {path}")
                    popen(f"tcpdump -n -i {intf} -w {path} &")
                  
        # Retry counters
        # self.wait_time = time   # How much time should the app take
        # self.retry_max = max    # How many times should the app retry
        # self.retry_delay = self.wait_time/self.retry_max
        self.retry_delay = 10

        # TODO: Define task setup routines here.
        
        if self.task != "__test_host__":
            print_time_message(f"Setting up task: {self.task}.")
            self._setup_()  # OVERRIDE THIS.
        else:
            # Create a receiver process..
            print_time_message("Setting up test Receiver.")
            self.__receiver__: Process = self.__create_run_ndnapp__(
                APP_TYPE.RECV, "__test_host__", wait_to_finish=False)
        
        print_time_message("Setup completed.")
        
    # Main function to begin execution of NDN_Host task.
    def run(self) -> None:
        self.__setup__(60.0, 12)

        # TODO: Define task run routines here.

        if self.task != "__test_host__":
            print_time_message(f"Running task: {self.task}.")
            self._run_()    # OVERRIDE THIS.
        else:
            # Send an Interest to obtain a response from other host..
            print_time_message(f"Creating test sender and sending test packet.")
            self.__create_run_ndnapp__(APP_TYPE.SEND, "__test_host__", params={"k_test": "v_test"})
        
        print_time_message("Task completed.")
        self.__shutdown__()

    def __shutdown__(self) -> None:
        if self.task != "__test_host__":
            self._shutdown_()
        else:
            print_time_message("Tearing down test Receiver.")
            self.__receiver__.join()
            self.__receiver__.close()

    # def _setup_tcpdump_(self):
        # getPopen(ndn.net[node], 
                # ndn.net[node].cmd(
                #     (f"tcpdump -n -i s{node}-eth{0} -w "
                #         f"{par_dir}/pcaps/{ndn_config['protocol']}/s{node}-{intf}.pcap &"))
    
    
    def __create_run_ndnapp__(self, app_type: APP_TYPE, prefix: str, suffix: str = None, 
                              params: dict = None, callback: FunctionType = None, 
                              must_be_fresh: bool = False, freshness: int = 0) -> Process | None:
        '''
        Create a new NDNApp instance with the function of sending Interests. 
        
        This function adds a new Process object to the self.procs dictionary, which maps a string 
        name to the Process itself. After using this function to create a Process, it can be 
        started with self.procs[<proc_name>].start() and wait for join with 
        self.procs[<proc_name>].join().
        
        Parameters:
            app_type (APP_TYPE): Type of app to create, using the APP_TYPE enum.
            prefix (str): Name of the data to be accessed or served.
            suffix (str) (optional): Additional application information to send.
            params (dict) (optional): Application params to send with Interest. (Forces use of 
            signed Interests.)
            wait_to_finish (bool): Flag to specify if tear down of app should occur after calling 
            this function or if a handle for the app should be returned from this function.
            must_be_fresh (bool): Flag to specify that Interest must reach the source (if True).
            freshness (int): How long (ms) an Interest packet can stay pending.

        Returns: 
            A handle to the newly created Process if wait_to_finish is set to False so that caller 
            can manuall close the thread elsewhere, otherwise None.
        '''

        if app_type == APP_TYPE.SEND:
            if must_be_fresh:
                app = Sender(NDNApp(), prefix, must_be_fresh, freshness)
            else:
                app = Sender(NDNApp(), prefix)
            
            app.validator = pass_all
            
            if suffix is not None:
                app.suffix = suffix
            
            if params is not None:  # Forces NSC protocol (Embedded Interests).
                app.params = params
                app.signer = app.app.default_keychain().get_signer({})
            
            app_proc = Process(target=app.__run__, args=[self.__express_interest__])
            app_proc.start()    # Start proc
            app_proc.join()     # Wait for proc to finish.
            app_proc.close()    # Free resources.
    
        elif app_type == APP_TYPE.RECV:
            try:
                assert callback is not None, "Error: Callback is None."

                func_name = prefix.split("/")[-1]
                callback_name = callback.__name__[1:-1].split('_')[0]
                assert func_name == callback_name, f"Error: Callback mismatch. {func_name} doesn't match {callback_name}."

                # Prefix advertisement boilerplate code, requires prefix and callback.
                def advertise_prefix(recv_app: Receiver):
                    print_time_message(f"Advertising the prefix: {prefix}")
                    popen(f"nlsrc advertise {prefix}")
                    # Add an assert.
                    @recv_app.app.route(prefix, recv_app.validator if hasattr(self, "validator") else None)
                    def on_interest(name: NonStrictName, params: BinaryStr | None, reply: ReplyFunc, context: PktContext):
                        name_str = Name.to_str(name)
                        params_decoded: dict = NDN_Host._print_interest_(name_str, params, context)
                        recv_app.data = callback(name_str, params_decoded)
                        reply(recv_app.app.make_data(name=name_str, content=recv_app.data_as_str(),
                                                    signer=recv_app.__signer__))
                        print_time_message("Data packet sent.")

                # Set up Receiver.
                app = Receiver(NDNApp(), prefix)
                app.signer = app.app.default_keychain().get_signer({})
                app.validator = pass_all
                app_proc = Process(target=app.__run__, args=[advertise_prefix])
                app_proc.start()

                return app_proc 
            except AssertionError as e:
                print_time_message(e)
                return   
        else:
            print_time_message("Error: Unable to create an app. Returning.")
            return

    # SENDER

    async def __express_interest__(self, send_app: Sender) -> None:
        '''
        Expresses an Interest for a name to the network and attempts to send an Interest packet. 
        
        Args:
            sender (Named_App): The NDNApp sender instance.
        
        Returns:
            None.
        '''

        # Search for prefix before attempting to send..
        #if self.__search_prefix__(send_app.prefix):
        print_time_message("Attempting to express an Interest..")
        
        # Try sending an Interest..
        # retry_count = 0
        # while retry_count <= self.retry_max:
        while True: 
            try:
                name: NonStrictName         # Data packet name
                content: BinaryStr | None   # Data packet content
                context: PktContext         # Data packet context information
                
                # Construct Interest name..
                if hasattr(send_app, "suffix"):
                    full_name = f"{send_app.prefix}/{send_app.suffix}"
                else:
                    full_name = send_app.prefix
                
                # Express Interest..
                
                print_time_message(f"Expressing an Interest for name: {full_name}..")
                
                if not hasattr(send_app, "must_be_fresh"):
                    if not hasattr(send_app, "params"):
                        name, content, context = await send_app.app.express(
                            name=full_name, validator=send_app.validator, lifetime=10000)
                    else:
                        name, content, context = await send_app.app.express(
                            name=full_name, validator=send_app.validator, lifetime=10000,
                            app_param=send_app.params_as_str(), signer=send_app.signer)
                        
                else:
                    if not hasattr(send_app, "params"):
                        name, content, context = await send_app.app.express(
                            name=full_name, validator=send_app.validator, lifetime=10000,
                            must_be_fresh=send_app.must_be_fresh, freshness=send_app.freshness)
                    else:
                        name, content, context = await send_app.app.express(
                            name=full_name, validator=send_app.validator, lifetime=10000,
                            app_param=send_app.params_as_str(), signer=send_app.signer, 
                            must_be_fresh=send_app.must_be_fresh, freshness=send_app.freshness)

                # Collect Interest packet information.
                name_str = Name.to_str(name)
                content_decoded: dict = decode_data(content)
                    
                info_list = ["Data packet received!", "", f"Name:\t\t{name_str}",
                            f"Content:\t{content_decoded if len(content_decoded) < 100 else '<Too large to display.>'}"]
                for k,v in context.items():
                    info_list.append(f"Context:\t{k}: {v}")
                info_list.append("")
            
                # Print Interest packet information.
                print_time_message(f"+---{'D---'*20}")
                for i, info in enumerate(info_list):
                    print_time_message(f"{'|' if i%2 == 0 else 'D'}\t{info}")
                print_time_message(f"+---{'D---'*20}")
        
                # TODO: Define post-Data packet routines.
                if "data" in content_decoded.keys():
                    content_decoded["data"] = base64.b64decode(content_decoded["data"])
                self._process_data_(name_str, content_decoded, context)    # OVERRIDE THIS.
                
                print_time_message("Sender shutdown called.")
                send_app.__shutdown__()   # Shut down NDNApp, no longer needed.
                return
                
            except InterestNack as e:
                # A NACK is received
                print_time_message(f'Nacked with reason={e.reason}')            
            except InterestTimeout:
                # Interest times out
                print_time_message(f'Timeout')
            except ValidationFailure:
                # Validation failure
                print_time_message(f'Data failed to validate')
                return
            except InterestCanceled:
                # Connection to NFD is broken
                print_time_message(f'NFD Connection broken.')
                return
            
            # If unsuccessful, begin resend step
            # retry_count += 1
            sleep(self.retry_delay)
            print_time_message("Trying again..")
    
    def __search_prefix__(self, prefix: str) -> bool:
        '''
        NDN Interest sender method, searches local FIB table for an entry that 
        matches specified prefix.
        
        Args:
            prefix (str): The prefix to search for.
        
        Returns:
            True, if prefix exists in FIB table. Otherwise, false.
        '''

        # retry_count = 0
        print_time_message(f"Searching for prefix: {prefix}..")
        # while retry_count <= self.retry_max:
        while True:
            fib = popen(f"nfdc fib").read()
            
            # print(f"---\n{fib}\n---")
            
            if prefix in fib:
                print_time_message(f"{prefix} found.")
                return True
            else:
                # If unsuccessful, begin recheck step
                # retry_count += 1
                sleep(self.retry_delay)
                print_time_message("Trying again..")
        
        # Unsuccessful
        return False
    
    def __get_full_prefix__(self, prefix: str, return_all: bool = False) -> str | list[str] | None:
        '''
        NDN Interest sender method, searches local FIB table for an entry that 
        matches specified partial prefix and returns a prefix that complete it.
    
        Args:
            prefix (str): Partial prefix to search for.
            return_all (bool): Flag to return all FIB entries that contain prefix
    
        Returns:
            str: Prefix that contain specified partial prefix.
            list[str]: List of prefixes that contain specified partial prefix.
            None: No prefixes were found.
        '''
    
        print_time_message(f"Searching for a prefix that contains: {prefix}..")
    
        if self.__search_prefix__(prefix):
            fib = popen(f"nfdc fib").read()
            if not return_all:
                for entry in fib.split():
                    if prefix in entry:           
                        return entry
            else:
                return [entry for entry in fib.split() if prefix in entry]
    
        # Unable to find prefix
        else: 
            print_time_message(f"Unable to find a prefix containing: {prefix}.")
    
        return None            
    
    # RECEIVER
        
    def _print_interest_(name: str, params: BinaryStr | None, context: PktContext) -> dict:
        info_list = ["Interest packet received!", "", f"Name:\t\t{name}"]
        
        if params is not None:  # Signed Interest
            params_decoded: dict = decode_data(params)
            
            info_list.append(f"Params:\t\t{params_decoded}")
        
        else:                   # Unsigned Interest
            params_decoded = None
            info_list.append(f"Params:\t\tNone.")

            for k,v in context.items():
                info_list.append(f"Context:\t{k}: {v}")
            info_list.append("")
            
            # Print Interest packet information.
            print_time_message(f"+---{'I---'*20}")
            for i, info in enumerate(info_list):
                print_time_message(f"{'|' if i%2 == 0 else 'I'}\t{info}")
            print_time_message(f"+---{'I---'*20}")
            
        return params_decoded

    # NDN

    def __get_suffix__(name: str, prefix: str) -> str | None:
        if len(name) > len(prefix) and name.startswith(prefix):
            suffix = name[len(prefix):]
        else:
            suffix = None
        return suffix
    