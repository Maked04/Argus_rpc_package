import asyncio
import os
from dotenv import load_dotenv

# RPC STUFF
from argus_rpc.RPClient import RPCClient
from argus_rpc.utils.RPC.RPCRequests import getTransactionRequest
from argus_rpc.utils.RPC.RPCResponses import RPCTransaction
from argus_rpc.utils.RPC.TransactionParser import extract_pump_fun_transaction

load_dotenv()

RPC_ENDPOINT = os.environ.get("RPC_ENDPOINT")
RPC_RPS = os.environ.get("RPC_RPS")

DEX_PARSERS = {"pump_fun": extract_pump_fun_transaction}

async def test_txs(tx_sigs, dex):
    transactions = await get_transactions(tx_sigs)

    for transaction in transactions:
        try:
            parsed_transaction = DEX_PARSERS[dex](transaction, debug=True)
            print(parsed_transaction)
        except Exception as e:
            print(f"Error parsing {transaction.signature}: {e}")

async def get_transactions(tx_sigs) -> RPCTransaction:
    rpc_client = RPCClient(endpoints_list=[(RPC_ENDPOINT, int(RPC_RPS))])

    try:
        requests = [getTransactionRequest(sig) for sig in tx_sigs]
        txs = await rpc_client.distribute_and_send_requests(requests)

        return [tx for tx in txs if tx]

    finally:
        await rpc_client.close()


async def main():
    transactions = ["44vbZJHojDLBBXsofSGMHsadmbn97AS7uQDaz3pHB3U8rqEmgczY9erqmREVNwoUytkd2xQX8Gynu7d1zv5Exb8A"]
    await test_txs(transactions, "pump_fun")


if __name__ == "__main__":
    asyncio.run(main())