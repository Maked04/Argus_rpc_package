"""
Client class for interacting with the Solana Yellowstone gRPC.
"""

import asyncio
import grpc
import logging
from typing import Iterator, AsyncGenerator, Dict, List

from .generated import geyser_pb2
from .generated import geyser_pb2_grpc

logger = logging.getLogger(__name__)

class gRPCCLient:
    """
    Attributes:
        endpoint (str): The gRPC endpoint URL
        token (str): Authentication token for the gRPC service
        channel (grpc.Channel): Secure gRPC channel
        stub (geyser_pb2_grpc.GeyserStub): gRPC stub for communication
    """
    def __init__(self, endpoint: str, token: str) -> None:
        """
        Args:
            endpoint: gRPC service endpoint URL (your RPC endpoint with port 10000)
            token: Authentication token for the service
        """
        self.endpoint = endpoint.replace('http://', '').replace('https://', '')
        self.token = token
        self.channel = self._create_secure_channel()
        self.stub = geyser_pb2_grpc.GeyserStub(self.channel)

    def _create_secure_channel(self) -> grpc.Channel:
        """Create a secure gRPC channel with authentication credentials."""
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

    async def start_monitoring(self, from_slot=None)  -> AsyncGenerator[geyser_pb2.SubscribeUpdate, None]:
        """
        Start monitoring for the specified request_iterator

        Yields updates received on stub

        Raises:
            grpc.RpcError: If gRPC communication fails
        """
        try:
            responses = self.stub.Subscribe(self.request_iterator(from_slot))
            for response in responses:
                if self.valid_response(response):
                    yield response
                
        except grpc.RpcError as e:
            logger.error(f"gRPC error occurred: {e}")
            raise
        finally:
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
