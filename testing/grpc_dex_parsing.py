import asyncio
from dotenv import load_dotenv
import os
import time

from pathlib import Path
import base58
from google.protobuf.json_format import MessageToDict, ParseDict
from argus_rpc.generated import geyser_pb2

import json
from datetime import datetime
from typing import List
from grpc import RpcError, StatusCode

# GRPC STUFF
from argus_rpc.gRPCClient import ConnectionTimeoutError, gRPCCLient
from argus_rpc.AccountsTxStream import AccountsTxStream
from argus_rpc.utils.gRPC.TransactionParser import TransactionParser

RAYDIUM_V4_PROGRAM = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
PUMP_FUN_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
PUMP_SWAP_PROGRAM = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
RAYDIUM_LAUNCH_PAD_PROGRAM = "LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj"
RAYDIUM_CPMM_PROGRAM = "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C"
METEORA_DBC_PROGRAM = "dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN"


load_dotenv()

GRPC_ENDPOINT = os.environ.get("GRPC_ENDPOINT")
GRPC_TOKEN = os.environ.get("GRPC_TOKEN")

def save_grpc_error_response(response, directory: str = "grpc_error_responses"):
    """
    Save a gRPC response to a file structure when an error occurs.
    
    Args:
        response: The gRPC response object (SubscribeUpdate)
        error: The exception that was raised
        directory: Base directory to save errors in
    """
    try:
        os.makedirs(directory, exist_ok=True)

        # Get signature from the response
        tx_info = response.transaction.transaction
        signature = base58.b58encode(bytes(tx_info.signature)).decode()
        
        # Save the response as JSON
        response_dict = MessageToDict(
            response,
            preserving_proto_field_name=True,
            use_integers_for_enums=True
        )
        
        # Add metadata
        response_dict['__metadata__'] = {
            'message_type': 'SubscribeUpdate',
            'timestamp': datetime.now().isoformat(),
        }
        
        # Save response to signature.json
        with open(os.path.join(directory, f"{signature}.json"), "w") as f:
            json.dump(response_dict, f, indent=2)
            
    except Exception as e:
        print(f"Error while saving error response: {e}")


def load_grpc_responses(directory: str = "grpc_error_responses") -> List[geyser_pb2.SubscribeUpdate]:
    """
    Load saved gRPC responses from JSON files in a flat directory.

    Returns:
        A list of reconstructed SubscribeUpdate protobuf messages.
    """
    responses = []
    base_dir = Path(directory)

    if not base_dir.exists():
        print(f"Directory '{directory}' does not exist.")
        return responses

    for json_file in base_dir.glob("*.json"):
        try:
            with open(json_file, "r") as f:
                response_dict = json.load(f)

            # Remove metadata if present
            response_dict.pop("__metadata__", None)

            # Parse to protobuf
            response_proto = ParseDict(response_dict, geyser_pb2.SubscribeUpdate())
            responses.append(response_proto)

        except Exception as e:
            print(f"Failed to load or parse {json_file.name}: {e}")

    return responses


async def test_new_txs():    
    accounts = {"pump_fun": [PUMP_FUN_PROGRAM]}

    running = True
    try:
        while running:
            try:
                monitor = AccountsTxStream(GRPC_ENDPOINT, GRPC_TOKEN, accounts)   
                async for response in monitor.start_monitoring():
                    if "pump_fun" in response.filters:
                        try:
                            transaction = TransactionParser.parse_pumpfun_transaction(response, debug=True)
                            print(transaction)
                            if transaction is None:
                                input("enter to continue")
                            #if transaction:
                            #    print(transaction)
                            #    input("enter to continue")
                                #print(f"{time.time() - transaction.block_time} seconds behind realtime")

                        except Exception as e:
                            print(f"Error parsing transaction: {str(e)}")

            except ConnectionTimeoutError as e:
                # Handle timeout - connection went silent
                print(f"Would be logging -> Connection timeout: {e}")
                await asyncio.sleep(5)
                continue

            except RpcError as rpc_error:
                if rpc_error.code() == StatusCode.DATA_LOSS:
                    print("Would be start filling gap")

                print(f"\nGRPC connection error: {rpc_error}")
                print("Attempting to reconnect in 5 seconds...")
                await asyncio.sleep(5)
                continue
                
    except asyncio.CancelledError:
        print("\nAsyncio task was cancelled. Shutting down gracefully...")
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Stopping gracefully...")


def test_unparsed_txs():
    unparsed_responses = load_grpc_responses()

    for response in unparsed_responses:
        transaction = TransactionParser.parse_raydium_launch_pad_transaction(response, debug=True)


if __name__ == "__main__":
    try:
        asyncio.run(test_new_txs())
        #test_unparsed_txs()
    except KeyboardInterrupt:
        print("Force exit detected.")