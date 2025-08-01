"""
Client class for interacting with the Solana Yellowstone gRPC.
"""

import os
import asyncio
import grpc
import logging
import time
from typing import Iterator, AsyncGenerator, Dict, List

from .generated import geyser_pb2
from .generated import geyser_pb2_grpc

# Get the current working directory when the script is executed
current_directory = os.getcwd()

# Create logs directory if it doesn't exist
logs_directory = os.path.join(current_directory, 'logs')
os.makedirs(logs_directory, exist_ok=True)

# Set up logger for gRPC client
logger = logging.getLogger("gRPCClient")
logger.setLevel(logging.INFO)

# Create file handler for gRPC errors
handler = logging.FileHandler(os.path.join(logs_directory, 'grpc_endpoint.log'))
handler.setLevel(logging.INFO)

# Create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

class ConnectionTimeoutError(Exception):
    """Raised when connection appears dead due to no data flow"""
    pass


class ConnectionMonitor:
    """Monitor connection health and track timeouts"""
    def __init__(self, timeout_seconds: int = 30):
        self.last_response_time = time.time()
        self.timeout_seconds = timeout_seconds
        self.is_healthy = True
        
    def update(self):
        """Update last response time"""
        self.last_response_time = time.time()
        self.is_healthy = True
        
    def check_timeout(self) -> bool:
        """Check if connection has timed out"""
        if time.time() - self.last_response_time > self.timeout_seconds:
            self.is_healthy = False
            return True
        return False


class gRPCCLient:
    """
    Enhanced gRPC client with connection monitoring that bubbles up errors
    
    Attributes:
        endpoint (str): The gRPC endpoint URL
        token (str): Authentication token for the gRPC service
        channel (grpc.Channel): Secure gRPC channel
        stub (geyser_pb2_grpc.GeyserStub): gRPC stub for communication
        connection_timeout (int): Timeout for considering connection dead
    """
    def __init__(self, endpoint: str, token: str, connection_timeout: int = 60) -> None:
        """
        Args:
            endpoint: gRPC service endpoint URL (your RPC endpoint with port 10000)
            token: Authentication token for the service
            connection_timeout: Seconds before considering connection dead
        """
        self.endpoint = endpoint.replace('http://', '').replace('https://', '')
        self.token = token
        self.connection_timeout = connection_timeout
        self.channel = None
        self.stub = None
        self._connect()

    def _connect(self):
        """Establish connection to gRPC server"""
        if self.channel:
            try:
                self.channel.close()
            except Exception as e:
                logger.warning(f"Error closing previous channel: {e}")
                
        self.channel = self._create_secure_channel()
        self.stub = geyser_pb2_grpc.GeyserStub(self.channel)
        logger.info(f"Connected to gRPC endpoint: {self.endpoint}")

    def _create_secure_channel(self) -> grpc.Channel:
        """Create a secure gRPC channel with authentication credentials and options."""
        auth = grpc.metadata_call_credentials(
            lambda context, callback: callback((("x-token", self.token),), None)
        )
        ssl_creds = grpc.ssl_channel_credentials()
        combined_creds = grpc.composite_channel_credentials(ssl_creds, auth)
        
        return grpc.secure_channel(self.endpoint, credentials=combined_creds)

    def request_iterator(self, from_slot=None) -> Iterator[geyser_pb2.SubscribeRequest]:
        """
        Generate subscription requests for monitoring.
        """
        request = geyser_pb2.SubscribeRequest()
        
        # Create and configure slot filter
        slots_entry = request.slots.get_or_create("slots")
        slots_entry.filter_by_commitment = True

        if from_slot is not None and isinstance(from_slot, int):
            request.from_slot = from_slot
        
        # Set commitment level
        request.commitment = geyser_pb2.CommitmentLevel.FINALIZED
        
        yield request
    
    def valid_response(self, response) -> bool:
        if hasattr(response, 'slot') and response.slot:
            return True
        return False

    async def start_monitoring(self, from_slot=None) -> AsyncGenerator[geyser_pb2.SubscribeUpdate, None]:
        """
        Start monitoring - raises all errors to caller for handling
        
        Yields updates received on stub
        
        Raises:
            grpc.RpcError: If gRPC communication fails
            ConnectionTimeoutError: If no data received within timeout period
        """
        monitor = ConnectionMonitor(self.connection_timeout)
        health_task = None
        
        try:
            # Create monitoring task
            async def check_connection_health():
                while True:
                    await asyncio.sleep(5)  # Check every 5 seconds
                    if monitor.check_timeout():
                        logger.warning(f"Connection timeout detected - no data for {self.connection_timeout} seconds")
                        raise ConnectionTimeoutError(f"No data received for {self.connection_timeout} seconds")
            
            # Start health check in background
            health_task = asyncio.create_task(check_connection_health())
            
            responses = self.stub.Subscribe(self.request_iterator(from_slot))
            
            for response in responses:
                monitor.update()  # Update last response time
                if self.valid_response(response):
                    yield response
                    
        except asyncio.CancelledError:
            # Re-raise cancelled errors
            raise
        except Exception as e:
            # Log the error before re-raising
            if isinstance(e, grpc.RpcError):
                logger.error(f"gRPC error occurred: {e.code()} - {e.details()}")
            elif isinstance(e, ConnectionTimeoutError):
                logger.error(f"Connection timeout: {e}")
            else:
                logger.error(f"Unexpected error in start_monitoring: {type(e).__name__} - {e}")
            raise
        finally:
            # Clean up health check task
            if health_task and not health_task.done():
                health_task.cancel()
                try:
                    await health_task
                except asyncio.CancelledError:
                    pass
            
            # Close channel
            if self.channel:
                self.channel.close()

    def close(self):
        """Close the gRPC channel"""
        if self.channel:
            self.channel.close()


async def main():
    logging.basicConfig(level=logging.INFO)
    monitor = gRPCCLient(
        "add grpc endpoint url here",
        "add grpc token here"
    )

    try:
        async for response in monitor.start_monitoring():
            print(response)

    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == "__main__":
    asyncio.run(main())