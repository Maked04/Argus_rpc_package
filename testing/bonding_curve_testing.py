import asyncio
import sys

# RPC STUFF
from argus_rpc.RPClient import RPCClient
from argus_rpc.RPClient import RPCClient
from argus_rpc.utils.RPC.RPCRequests import getAccountInfoRequest

from argus_rpc.utils.RPC.structs import LAUNCHPAD_POOL_LAYOUT
from argus_rpc.utils.RPC.pda import get_raydium_launch_pad_pool_address


async def get_account_data(account_address):
    rpc_client = RPCClient(endpoints_list=[("https://solana-mainnet.g.alchemy.com/v2/f2K7ti4z-5WH8DlE3Va1MwAipkNMun9X", 1000)])

    request = getAccountInfoRequest(account_address)

    account_info = await rpc_client._send_request(request)

    await rpc_client.close()

    account_info.decode_data(LAUNCHPAD_POOL_LAYOUT)

    return account_info.decoded_data


def get_initial_price(pool_info):
    return (pool_info.virtualB / pool_info.virtualA) * (10 ** (pool_info.mintDecimalsA - pool_info.mintDecimalsB))

def get_end_price(pool_info):
    return ((pool_info.virtualB + pool_info.totalFundRaisingB) / (pool_info.virtualA - pool_info.totalSellA)) * (10 ** (pool_info.mintDecimalsA - pool_info.mintDecimalsB))



async def main():
    mintA = "9kXtgQuzvm4e6Sfvyak9eYAvJ3aZ3CYMR8Ez81wqbonk"
    mintB = "So11111111111111111111111111111111111111112"

    market_account = get_raydium_launch_pad_pool_address(mintA, mintB)
    
    pool_info = await get_account_data(market_account)

    print(f"Inital price: {get_initial_price(pool_info)}")
    print(f"End price: {get_end_price(pool_info)}")


if __name__ == "__main__":
    if sys.platform == 'win32':
        # Set event loop policy to avoid ProactorEventLoop issues
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())