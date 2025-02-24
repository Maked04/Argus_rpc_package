from .RPCResponses import *

class RPC_Error(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class RPCRequest:
    def __init__(self, method, params):
        self.method = method
        self.params = params

    def parse_response(self, response):
        return response


class getTransactionRequest(RPCRequest):
    def __init__(self, tx_sig, encoding = "jsonParsed", commitment= 'finalized', max_supported_transaction_version=0):
        params = [
                tx_sig,
                {
                    "encoding": encoding,
                    "commitment": commitment,
                    "maxSupportedTransactionVersion": max_supported_transaction_version
                }
            ]
        super().__init__("getTransaction", params)

    def parse_response(self, response):
        if 'result' in response and response['result']:
            return RPCTransaction(response)
        else:
            return None

class getSignaturesForAddressRequest(RPCRequest):
    def __init__(self, address, limit=None, before=None, until=None, encoding="jsonParsed", commitment='finalized', max_supported_transaction_version=0):
        params = [
            address,
            {
                "limit": limit,
                "before": before,
                "until": until,
                "encoding": encoding,
                "commitment": commitment,
                "maxSupportedTransactionVersion": max_supported_transaction_version
            }
        ]
        super().__init__("getSignaturesForAddress", params)

    def parse_response(self, response):
        if 'result' in response and response['result'] is not None:  # Checking if not none as if it's empty list boolean check won't work
            return [RPCSignature(signature) for signature in response['result']]
        else:
            return None

class getBlockRequest(RPCRequest):
    def __init__(self, block, encoding="json", commitment="finalized", transaction_details="full", rewards=False):
        params = [
            block,
            {
                "encoding": encoding,
                "commitment": commitment,
                "transactionDetails": transaction_details,
                "rewards": rewards
            }
        ]
        super().__init__("getBlock", params)

    def parse_response(self, response):
        if 'result' in response and response['result']:
            return RPCBlock(response['result'])
        else:
            return None


class getBlockHeightRequest(RPCRequest):
    def __init__(self, commitment="finalized"):
        params = [
            {"commitment": commitment}
        ]
        super().__init__("getBlockHeight", params)

    def parse_response(self, response):
        if 'result' in response and response['result']:
            return response['result']  # Returns int
        else:
            return None


class getProgramAccountsRequest(RPCRequest):
    def __init__(self, program_id, filters=None, data_slice=None, encoding="base64", commitment="finalized"):
        self.encoding = encoding
        params = [
            program_id,
            {
                "encoding": encoding,
                "commitment": commitment,
                "filters": filters or []
            }
        ]
        if data_slice:
            if encoding in ["base58", "base64", "base64+zstd"]:  # Data slice only available for these encodings
                params[1]["dataSlice"] = data_slice
            else:
                print(f"To use dataSlice please use a valid encoding, instead creating request without dataSlice")

        super().__init__("getProgramAccounts", params)

    def parse_response(self, response):
        if 'result' in response and response['result'] is not None:  # Checking if not none as if it's empty list boolean check won't work
            return [RPCProgramAccount(account, self.encoding) for account in response['result']]
        else:
            return None


class sendTransactionRequest(RPCRequest):
    def __init__(self, tx, encoding="base64", skip_preflight=False, preflight_commitment="finalized"):
        """
        Initialize the sendTransactionRequest object with the transaction to send.
        
        :param tx: The serialized transaction to be sent (in base64 or another supported encoding)
        :param encoding: The encoding for the transaction (default is "base64")
        :param skip_preflight: If True, skip the preflight transaction checks
        :param preflight_commitment: The commitment level for preflight (default is "finalized")
        """
        params = [
            tx,
            {
                "encoding": encoding,
                "skipPreflight": skip_preflight,
                "preflightCommitment": preflight_commitment
            }
        ]
        super().__init__("sendTransaction", params)

    def parse_response(self, response):
        """
        Parse the response of the sendTransaction request.
        
        :param response: The raw JSON response from the Solana RPC
        :return: RPCSendTransactionResponse object or None if the response doesn't contain a result
        """
        if 'result' in response and response['result']:
            return RPCSendTransactionResponse(response)
        else:
            return None

