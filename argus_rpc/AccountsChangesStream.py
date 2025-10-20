from .gRPCClient import *
import base58

# SPL Token Program ID
TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"

class AccountsChangesStream(gRPCCLient):
    """AccountsChangesStream which listens for token account changes for given wallet addresses"""
    COMMITMENT_LEVEL = geyser_pb2.CommitmentLevel.CONFIRMED
   
    def __init__(self, endpoint: str, token: str, wallet_addresses: List[str], connection_timeout: int = 30) -> None:
        self.wallet_addresses = wallet_addresses  # List of wallet addresses to monitor
        super().__init__(endpoint, token, connection_timeout)
       
    def valid_response(self, update: geyser_pb2.SubscribeUpdate) -> bool:
        """
        Validate if the update contains a valid token account change.
        """
        if not (hasattr(update, 'account') and update.account and update.account.account):
            return False
        
        # Parse the token account data to check if it belongs to one of our wallets
        try:
            account_data = update.account.account.data
            if len(account_data) >= 64:  # Token account data should be 165 bytes
                # The owner is stored at bytes 32-64 in a token account
                owner_pubkey = base58.b58encode(bytes(account_data[32:64])).decode('utf-8')
                return owner_pubkey in self.wallet_addresses
        except Exception as e:
            print(f"Error parsing account data: {e}")
            return False
        
        return False
       
    def request_iterator(self, from_slot=None) -> Iterator[geyser_pb2.SubscribeRequest]:
        """
        Generate subscription request for monitoring token accounts.
        Subscribes to all accounts owned by the SPL Token Program, 
        filtered by wallet owner using memcmp.
       
        Yields:
            geyser_pb2.SubscribeRequest: Configured subscription request
        """
        try:
            request = geyser_pb2.SubscribeRequest()
           
            # Create the filter for token accounts
            filter_name = "token_accounts"
            
            # Subscribe to all accounts owned by the Token Program
            request.accounts[filter_name].owner.append(TOKEN_PROGRAM_ID)
            
            # Add memcmp filters for each wallet address
            # This filters for token accounts where the owner field (offset 32) matches our wallet
            for wallet_address in self.wallet_addresses:
                # Create memcmp filter
                memcmp_filter = geyser_pb2.SubscribeRequestFilterAccountsFilterMemcmp()
                memcmp_filter.offset = 32  # Owner field is at offset 32 in token account
                memcmp_filter.bytes = base58.b58decode(wallet_address)
                
                # Wrap in SubscribeRequestFilterAccountsFilter
                accounts_filter = geyser_pb2.SubscribeRequestFilterAccountsFilter()
                accounts_filter.memcmp.CopyFrom(memcmp_filter)
                
                # Add to the filters list
                request.accounts[filter_name].filters.append(accounts_filter)
           
            if from_slot is not None and isinstance(from_slot, int):
                request.from_slot = from_slot
               
            request.commitment = self.COMMITMENT_LEVEL
            
            yield request
            
        except Exception as e:
            print(f"Error creating request: {e}")
            raise