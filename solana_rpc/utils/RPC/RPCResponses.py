from solana_rpc.utils.RPC import decoders

class RPCTransaction:
    def __init__(self, response):
        """
        Initializes the RPCTransaction object with the raw response from the Solana JSON-RPC getTransaction method.
        
        :param response: The response JSON from the getTransaction method
        """
        # Extract basic info from the response
        result = response.get('result')
        self.transaction = result.get('transaction', {})
        self.meta = result.get('meta', {})
        self.slot = result.get('slot', None)
        self.block_time = result.get('blockTime', None)
        self.transaction_status = self.meta.get('err', None)

        # Transaction level details
        self.signatures = self.transaction.get('signatures', [])
        self.signature = self.signatures[0]
        self.message = self.transaction.get('message', {})
        self.recent_blockhash = self.message.get('recentBlockhash', None)

        # Meta-level details
        self.fee = self.meta.get('fee', 0)
        self.pre_balances = self.meta.get('preBalances', [])
        self.post_balances = self.meta.get('postBalances', [])
        self.pre_token_balances = self.meta.get('preTokenBalances', [])
        self.post_token_balances = self.meta.get('postTokenBalances', [])
        self.log_messages = self.meta.get('logMessages', [])
        self.rewards = self.meta.get('rewards', [])

        # Transaction account details
        self.accounts = self.message.get('accountKeys', [])

        # Instruction details (parsed and raw)
        self.instructions = self.message.get('instructions', [])
        self.parsed_instructions = self.message.get('instructions', [])
    
    def __str__(self):
        return f"Transaction: {self.signature}"

    def __eq__(self, other):
        if self.signature == other.signature:
            return True
        return False

class RPCSignature:
    def __init__(self, signature_data):
        # Initialize with the data you expect from the signature response
        self.signature = signature_data['signature']
        self.slot = signature_data['slot']
        self.err = signature_data.get('err', None)
        self.memo = signature_data.get('memo', None)
        self.block_time = signature_data.get('blockTime', None)

class RPCBlock:
    def __init__(self, block_data):
        """
        Initializes the RPCBlock object with the raw response from the Solana JSON-RPC getBlock method.
        
        :param block_data: The response JSON from the getBlock method
        """
        self.block_height = block_data.get('blockHeight', None)
        self.block_time = block_data.get('blockTime', None)
        self.blockhash = block_data.get('blockhash', None)
        self.parent_slot = block_data.get('parentSlot', None)
        self.previous_blockhash = block_data.get('previousBlockhash', None)
        self.rewards = block_data.get('rewards', [])
        self.transactions = block_data.get('transactions', [])

        # Optional fields for full or partial transaction data
        self.transaction_count = len(self.transactions)
        if 'signatures' in block_data:
            self.signatures = block_data['signatures']
        else:
            self.signatures = [tx['transaction']['signatures'][0] for tx in self.transactions]

    def __str__(self):
        return f"Block: {self.blockhash}, Slot: {self.parent_slot}"

    def __eq__(self, other):
        return self.blockhash == other.blockhash


class RPCProgramAccount:
    def __init__(self, account_data, encoding):
        """
        Initializes the RPCProgramAccount object with the raw response from the Solana JSON-RPC getProgramAccounts method.
        
        :param account_data: A single account entry from the getProgramAccounts response
        :param encoding: Encoding used for request (Needed to decode data)
        """
        self.encoding = encoding
        self.pubkey = account_data.get('pubkey', None)
        self.account = account_data.get('account', {})
        self.lamports = self.account.get('lamports', None)
        self.owner = self.account.get('owner', None)
        self.executable = self.account.get('executable', False)
        self.rent_epoch = self.account.get('rentEpoch', None)
        self.data = self.account.get('data', None)
        self.decoded_data = None
    
    def decode_data(self, account_layout_struct):
        data = decoders.decode_on_type(self.data, self.encoding)
        self.decoded_data = account_layout_struct.parse(data)

    def __str__(self):
        return f"Program Account: {self.pubkey}"

    def __eq__(self, other):
        return self.pubkey == other.pubkey

class RPCSendTransactionResponse:
    def __init__(self, response):
        """
        Initialize the RPCSendTransactionResponse object with the raw response from the sendTransaction method.
        
        :param response: The response JSON from the sendTransaction method
        """
        result = response.get('result')
        self.signature = result  # The signature of the transaction if it was successfully submitted
        
        # Optional: If there is an error, you can capture it
        self.error = response.get('error', None)

    def __str__(self):
        if self.signature:
            return f"Transaction Signature: {self.signature}"
        else:
            return f"Transaction failed with error: {self.error}"

    def __eq__(self, other):
        if isinstance(other, RPCSendTransactionResponse):
            return self.signature == other.signature
        return False
