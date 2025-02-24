import os
import asyncio
import aiohttp
import time
import json
import logging
from .utils.RPC.RPCRequests import RPCRequest, RPC_Error

# Get the current working directory when the script is executed
current_directory = os.getcwd()

# Configure the root logger
logging.basicConfig(
    filename=os.path.join(current_directory, 'rpc_endpoint.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AsyncRPCEndpoint:
    def __init__(self, url, rps):
        self.url = url
        self.next_rate_limit_reset = time.time() + 1  # Set next credit reset to a second from initialization
        self.last_send_time = time.time() - 5  # At start, do time in the past
        self.rps = rps  # Requests per second
        self.delay_time = 1/rps  # Spread requests over each second
        self.check_limit_lock = asyncio.Lock()
        self.session = None
        self.request_id = 1
        self.logger = logging.getLogger(f"AsyncRPCEndpoint-{url}")
        self.uptime_request = {"jsonrpc":"2.0","id":1, "method":"getHealth"}

    async def open(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    def get_request_time_slot(self):
        wait_time = 0
        time_since_last_send = time.time() - self.last_send_time
        if time_since_last_send < self.delay_time:
            wait_time = self.delay_time - time_since_last_send

        self.last_send_time = time.time() + wait_time

        return wait_time

    def generate_request_id(self):
        if self.request_id > 1000000:  # Reset every million requests so number doesn't get too large
            self.request_id = 0
        
        self.request_id += 1
        return self.request_id

    async def poll_until_available(self, timeout):
        backoff_time = 15  # Start with 30 seconds between polls
        max_polling_time = 300  # Max 5 minutes between polls
        
        while True:
            try:
                # Use a simple getHealth request to check server availability
                async with self.session.post(self.url, json=self.uptime_request, timeout=timeout) as response:
                    if response.status == 200:  # Server is available
                        self.logger.info("Endpoint is back online and ready.")
                        return
                    else:
                        self.logger.warning(f"Received unexpected status code: {response.status}. Trying again in {backoff_time} seconds.")
            except aiohttp.ClientError as e:
                self.logger.warning(f"Polling failed: {e}. Trying again in {backoff_time} seconds.")
            
            # Wait before retrying, with exponential backoff
            await asyncio.sleep(backoff_time)
            backoff_time = min(backoff_time * 2, 300)  # Exponential backoff
    
    async def send_request(self, request: RPCRequest, max_retries=0, timeout=20):
        if max_retries < 0:
            self.logger.warning(f"Max retries must be greater than or equal to zero, using no retries instead")
            max_retries = 0
        
        for attempt in range(max_retries + 1):  # Plus one as we want to send the initial request, which isn't a 'retry'
            async with self.check_limit_lock:
                wait_time = self.get_request_time_slot()

            await asyncio.sleep(wait_time)
            await self.open()  # Make sure session is open
            request_id = self.generate_request_id()
            rpc_json = {"jsonrpc": "2.0", "id": request_id, "method": request.method, "params": request.params}
            try:
                async with self.session.post(self.url, json=rpc_json, timeout=timeout) as response:
                    if response.status == 200:
                        try:
                            response_json = await response.json()
                            response_obj = request.parse_response(response_json)
                            if response_obj is not None:
                                return response_obj
                            self.logger.error(f"[{self.url}] Response unable to be parsed, response: {response_json}")
                        except aiohttp.ContentTypeError as e:
                            self.logger.error(f"[{self.url}] ContentTypeError: {e}")
                        except json.JSONDecodeError as e:
                            self.logger.error(f"[{self.url}] JSONDecodeError: {e}")
                    elif response.status == 429:  # Rate limit hit
                        self.logger.warning(f"[{self.url}] 429 Rate limited")
                    elif response.status == 504:  # Rate limit hit
                        self.logger.warning(f"[{self.url}] 504 Gateway Timeout")
                    elif response.status == 503:  # Server closed
                        self.logger.warning(f"[{self.url}] 503 Service Unavailable")
                        s_t = time.time()
                        await self.poll_until_available(timeout)
                        self.logger.info(f"Waited {time.time() - s_t} seconds for endpoint to come back up!")

                    else:
                        self.logger.warning(f"[{self.url}] Unexpected status code: {response.status}")

            except aiohttp.ClientResponseError as e:
                self.logger.error(f"[{self.url}] ClientResponseError : {e}")
            except asyncio.TimeoutError as e:
                self.logger.error(f"[{self.url}] TimeoutError: {e}")
            except aiohttp.ClientError as e:
                self.logger.error(f"[{self.url}] ClientError: {e}")
        
        raise RPC_Error(rpc_json)
