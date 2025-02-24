import os
import asyncio
from typing import List, Tuple
import logging
from random import choice as random_choice

from .AsyncRPCEndpoint import AsyncRPCEndpoint
from .utils.RPC.RPCRequests import RPC_Error, RPCRequest

# Get the current working directory when the script is executed
current_directory = os.getcwd()

# Logger setup
failed_requests_logger = logging.getLogger("RPCRequestManagerFailedRequests")
failed_requests_logger.setLevel(logging.ERROR)
# Create file handler for failed requests
handler = logging.FileHandler(os.path.join(current_directory, "failed_requests.log"))
handler.setLevel(logging.ERROR)
# Create formatter and set it for the handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
failed_requests_logger.addHandler(handler)

class RPCRequestManager:
    def __init__(self, endpoints_file: str = None, endpoints_list: List[Tuple[str, int]] = None):
        """
        Initializes the RPCRequestManager with either a file containing endpoints or a list of (url, rps) tuples.
        
        :param endpoints_file: Path to a file containing endpoint URLs and RPS values.
        :param endpoints_list: List of tuples containing (url, rps) for endpoints.
        """
        if endpoints_file:
            self.endpoints = self._load_endpoints_from_file(endpoints_file)
        elif endpoints_list:
            self.endpoints = [AsyncRPCEndpoint(url, rps) for url, rps in endpoints_list]
        else:
            raise ValueError("Either endpoints_file or endpoints_list must be provided.")

    def _load_endpoints_from_file(self, file_path: str) -> List[AsyncRPCEndpoint]:
        """Loads endpoints from a file and initializes AsyncRPCEndpoint instances."""
        endpoints = []
        with open(file_path, 'r') as f:
            for line in f:
                url, rps_str = line.strip().split()
                rps = int(rps_str)
                endpoints.append(AsyncRPCEndpoint(url, rps))
        return endpoints

    async def close(self):
        """
        Closes all active RPC endpoints by closing their asynchronous sessions.
        """
        close_tasks = [endpoint.close() for endpoint in self.endpoints]
        await asyncio.gather(*close_tasks)

    async def _send_request(self, request: RPCRequest, endpoint: AsyncRPCEndpoint = None, max_retries: int=3, timeout: int=30):
        if endpoint is None:
            endpoint = random_choice(self.endpoints)  # Pick random endpoint to use
        try:
            return await endpoint.send_request(request, max_retries, timeout)
        except RPC_Error as e:
            failed_requests_logger.error(f"RPC_Error occurred for endpoint {endpoint.url}: {e}")
        except Exception as e:
            failed_requests_logger.error(f"UNKNOWN ERROR occurred for endpoint {endpoint.url}: {e}")
        
        return None
    
    async def _send_request_batch(self, endpoint: AsyncRPCEndpoint, requests: List[RPCRequest], max_retries: int = 3, timeout: int = 30):
        """Send a batch of requests to a single endpoint asynchronously."""
        
        # Create coroutines for each request
        request_tasks = [self._send_request(request, endpoint, max_retries, timeout) for request in requests]

        # Run all requests concurrently and wait for them to finish
        responses = await asyncio.gather(*request_tasks, return_exceptions=True)

        # Handle any exceptions that may have occurred during the requests
        for response in responses:
            if isinstance(response, Exception):
                failed_requests_logger.error(f"Request in batch failed with error: {response}")
        
        return responses

    async def distribute_and_send_requests(
        self, 
        requests: List[RPCRequest], 
        max_retries: int = 3, 
        timeout: int = 30, 
        excluded_endpoints: List[str] = None
    ):
        """
        Distributes requests across available endpoints and sends them concurrently,
        allowing the exclusion of specific endpoints.

        :param requests: List of RPCRequest objects to be sent.
        :param max_retries: Maximum number of retries for each request.
        :param timeout: Timeout for each request.
        :param excluded_endpoints: List of endpoint URLs to exclude from sending requests.
        :return: Combined results from all endpoints.
        """
        if excluded_endpoints is None:
            excluded_endpoints = []

        # Filter out the excluded endpoints
        available_endpoints = [endpoint for endpoint in self.endpoints if endpoint.url not in excluded_endpoints]

        if not available_endpoints:
            raise ValueError("No available endpoints to send requests after exclusions.")

        # Calculate how to distribute requests across remaining endpoints based on RPS limits
        rps_limits = [endpoint.rps for endpoint in available_endpoints]
        total_rps = sum(rps_limits)

        request_groups = []
        index = 0
        for limit in rps_limits:
            num_of_requests = int((limit / total_rps) * len(requests)) + 1
            request_groups.append(requests[index: index + num_of_requests])
            index += num_of_requests

        # Create coroutines for each remaining endpoint's request group
        endpoint_tasks = []
        for endpoint, request_group in zip(available_endpoints, request_groups):
            if request_group:
                print(f"Endpoint {endpoint.url} is handling {len(request_group)} requests")
                # Schedule each batch of requests as a task
                task = self._send_request_batch(endpoint, request_group, max_retries, timeout)
                endpoint_tasks.append(task)

        # Run all endpoint tasks concurrently and gather results
        all_responses = await asyncio.gather(*endpoint_tasks, return_exceptions=True)

        # Combine all responses into one result set
        combined_results = []
        for responses in all_responses:
            if isinstance(responses, list):
                combined_results.extend(responses)

        return combined_results








    '''async def _send_request_batch(self, endpoint: AsyncRPCEndpoint, requests: RPCRequest, max_retries: int=3, timeout: int=30):
        request_tasks = [self._send_request(request, endpoint, max_retries, timeout) for request in requests]

        responses = await asyncio.gather(*request_tasks, return_exceptions=True)

        # Log or handle any exceptions that occurred
        for response in responses:
            if isinstance(response, Exception):
                failed_requests_logger.error(f"Request in batch failed with error: {response}")
        
        return responses



    def distribute_and_send_requests(self, requests: List[RPCRequest], max_retries: int = 3, timeout: int = 30):
        """
        Distributes requests across available endpoints and sends them concurrently.

        :param requests: List of RPCRequest objects to be sent.
        :param max_retries: Maximum number of retries for each request.
        :param timeout: Timeout for each request.
        :return: Combined results from all endpoints.
        """
        def thread_requests(endpoint, requests, results_queue):
            """Handles requests in a separate thread per endpoint as one endpoint shouldn't affect another."""
            loop = asyncio.new_event_loop()

            asyncio.set_event_loop(loop)
            loop.run_until_complete(endpoint.open())
            try:
                result = loop.run_until_complete(self._send_request_batch(endpoint, requests))
                results_queue.put(result)
            finally:
                loop.run_until_complete(endpoint.close())
                loop.close()

        rps_limits = [endpoint.rps for endpoint in self.endpoints]
        total_rps = sum(rps_limits)

        request_groups = []
        index = 0
        for limit in rps_limits:
            num_of_requests = int((limit / total_rps) * len(requests)) + 1
            request_groups.append(requests[index: index + num_of_requests])
            index += num_of_requests

        threads = []
        results_queue = queue.Queue()
        for endpoint, request_group in zip(self.endpoints, request_groups):
            if len(request_group) > 0:
                print(f"Endpoint {endpoint.url} is handling {len(request_group)} requests")
                t = Thread(target=thread_requests, args=(endpoint, request_group, results_queue))
                t.start()
                threads.append(t)

        for t in threads:
            t.join()
        
        # Once all threads have finished, get all results from queue
        all_results = []
        while not results_queue.empty():
            results = results_queue.get()
            all_results.extend(results)

        return all_results
'''