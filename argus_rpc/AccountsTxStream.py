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
        if not hasattr(update, 'transaction'):
            print("Invalid: update has no 'transaction' attribute")
            return False

        if not update.transaction:
            print("Invalid: update.transaction is falsy")
            return False

        if not hasattr(update, 'filters'):
            print("Invalid: update has no 'filters' attribute")
            return False

        if not any(item in self.accounts.keys() for item in update.filters):
            print("Invalid: no overlap between update.filters and self.accounts")
            return False

        tx = update.transaction.transaction
        if not tx:
            print("Invalid: update.transaction.transaction is falsy")
            return False

        if not tx.transaction:
            print("Invalid: update.transaction.transaction.transaction is falsy")
            return False

        if not tx.transaction.message:
            print("Invalid: transaction.message is missing or falsy")
            return False

        if tx.meta and tx.meta.err and len(tx.meta.err.err) > 0:
            print("Invalid: transaction has an error")
            return False

        return True


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
            # Explicitly exclude vote transactions
            request.transactions[filter_name].vote = False
            # Explicitly exclude failed transactions
            request.transactions[filter_name].failed = False
        
        if from_slot is not None and isinstance(from_slot, int):
            request.from_slot = from_slot

        request.commitment = self.COMMITMENT_LEVEL
        yield request


async def main():
    logging.basicConfig(level=logging.INFO)
    accounts = {"raydium": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8", "pumpfun": "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"}
    monitor = AccountsTxStream(
        "add grpc endpoint url here",
        "add grpc token here",
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