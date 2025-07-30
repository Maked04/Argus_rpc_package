import asyncio
from grpc import RpcError
import os

# GRPC STUFF
from argus_rpc.AccountsTxStream import AccountsTxStream
from argus_rpc.utils.gRPC.TransactionParser import TransactionParser

RAYDIUM_V4_PROGRAM = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
PUMP_FUN_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
PUMP_SWAP_PROGRAM = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
RAYDIUM_LAUNCH_PAD_PROGRAM = "LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj"
RAYDIUM_CPMM_PROGRAM = "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C"

GRPC_ENDPOINT = os.environ.get("GRPC_ENDPOINT")
GRPC_TOKEN = os.environ.get("GRPC_TOKEN")


async def main():    
    accounts = {"pump_fun": ["6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"]}

    running = True
    try:
        while running:
            try:
                monitor = AccountsTxStream(GRPC_ENDPOINT, GRPC_TOKEN, accounts)   
                async for response in monitor.start_monitoring():
                    if "pump_fun" in response.filters:
                        try:
                            transaction = TransactionParser.parse_pumpfun_transaction(response)
                            if transaction:
                                print(transaction)
                                running = False
                                break

                        except Exception as e:
                            print(f"Error parsing transaction: {str(e)}")

            except RpcError as rpc_error:
                print(f"\nGRPC connection error: {rpc_error}")
                print("Attempting to reconnect in 5 seconds...")
                await asyncio.sleep(5)
                continue
                
    except asyncio.CancelledError:
        print("\nAsyncio task was cancelled. Shutting down gracefully...")
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Stopping gracefully...")




if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Force exit detected.")