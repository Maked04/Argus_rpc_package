from .gRPCClient import *

class AccountsTxStream(gRPCCLient):
    COMMITMENT_LEVEL = geyser_pb2.CommitmentLevel.CONFIRMED
    def __init__(self, endpoint: str, token: str, accounts: Dict[str, List[str]]) -> None:
        self.accounts = accounts  # Name of account filter: [list of accounts]
        super().__init__(endpoint, token)

    def valid_response(self, update: geyser_pb2.SubscribeUpdate) -> bool:
        """
        Validate if the update contains a valid transaction and overlaps with the accounts.
        """
        return (
            hasattr(update, 'transaction')
            and update.transaction
            and hasattr(update, 'filters')  # Ensure filters exist
            and any(item in self.accounts.keys() for item in update.filters)  # Check overlap with accounts
            and update.transaction.transaction
            and update.transaction.transaction.transaction
            and update.transaction.transaction.transaction.message
            and len(update.transaction.transaction.meta.err.err) == 0
        )

    def request_iterator(self, from_slot=None) -> Iterator[geyser_pb2.SubscribeRequest]:
        """
        Generate subscription request for monitoring the given accounts.

        accounts: mapping from account name to account address

        Yields:
            geyser_pb2.SubscribeRequest: Configured subscription request
        """
        request = geyser_pb2.SubscribeRequest()

        for filter_name, addresses in self.accounts.items():
            request.transactions[filter_name].account_include.extend(addresses)
        
        if from_slot is not None and isinstance(from_slot, int):
            request.from_slot = from_slot

        request.commitment = self.COMMITMENT_LEVEL
        yield request


async def main():
    logging.basicConfig(level=logging.INFO)
    #accounts = {"raydium": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"}
    accounts = {"raydium": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8", "pumpfun": "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"}
    monitor = AccountsTxStream(
        "https://sol-yellowstone-avl.rpcfast.net:443",
        "XpDCDCxOx30xZ80C6lM6yvtiRftO8tgsJ6w8KG7eJlPZem36c0A3GMTcCSdJUecg",
        accounts
    )

    try:
        count = 0
        async for response in monitor.start_monitoring():
            count += 1
            if count > 15:
                break
            
            if "pumpfun" in response.filters:
                print(response)

    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == "__main__":
    asyncio.run(main())