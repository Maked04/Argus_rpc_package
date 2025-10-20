import asyncio
from dotenv import load_dotenv
import os
import time
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed, Processed
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solana.rpc.types import TxOpts
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from spl.token.instructions import (
    get_associated_token_address,
    create_associated_token_account,
    transfer_checked,
    TransferCheckedParams,
)
from spl.token.constants import TOKEN_PROGRAM_ID
import base58
from grpc import RpcError, StatusCode

# GRPC STUFF
from argus_rpc.gRPCClient import ConnectionTimeoutError
from argus_rpc.AccountsChangesStream import AccountsChangesStream
from argus_rpc.utils.gRPC.AccountParser import AccountChangeParser

load_dotenv()

GRPC_ENDPOINT = os.environ.get("GRPC_ENDPOINT")
GRPC_TOKEN = os.environ.get("GRPC_TOKEN")
RPC_ENDPOINT = os.environ.get("HELIUS_ENDPOINT", "https://api.mainnet-beta.solana.com")

# Compute budget settings
COMPUTE_UNIT_LIMIT = 200_000
COMPUTE_UNIT_PRICE = 50_000


async def get_token_decimals(client: AsyncClient, mint_address: str) -> int:
    """Fetch token decimals from the mint account"""
    try:
        mint_pubkey = Pubkey.from_string(mint_address)
        response = await client.get_account_info(mint_pubkey, commitment=Confirmed)
        
        if response.value and response.value.data:
            # Decimals is at byte 44 in the mint account
            decimals = response.value.data[44]
            return decimals
    except Exception as e:
        print(f"Error fetching decimals for mint {mint_address}: {e}")
    
    return 9  # Default fallback


async def check_token_account_exists(client: AsyncClient, token_account: Pubkey) -> bool:
    """Check if a token account exists"""
    try:
        response = await client.get_account_info(token_account, commitment=Confirmed)
        return response.value is not None
    except Exception as e:
        print(f"Error checking token account: {e}")
        return False


async def transfer_tokens(
    client: AsyncClient,
    source_wallet: Keypair,
    safe_wallet_pubkey: Pubkey,
    mint_pubkey: Pubkey,
    source_token_account: Pubkey,
    amount: int,
    decimals: int,
    max_retries: int = 3
):
    """
    Transfer tokens from source to safe wallet.
    Creates associated token account if needed.
    """
    for attempt in range(max_retries):
        try:
            print(f"\n{'=' * 60}")
            print(f"Transfer attempt {attempt + 1}/{max_retries}")
            print(f"{'=' * 60}")
            
            # Get the destination associated token account
            dest_token_account = get_associated_token_address(
                safe_wallet_pubkey,
                mint_pubkey
            )
            
            print(f"Source token account: {source_token_account}")
            print(f"Destination token account: {dest_token_account}")
            
            # Check if destination token account exists
            dest_exists = await check_token_account_exists(client, dest_token_account)
            print(f"Destination account exists: {dest_exists}")
            
            instructions = []
            
            # Add compute budget instructions
            instructions.append(set_compute_unit_limit(COMPUTE_UNIT_LIMIT))
            instructions.append(set_compute_unit_price(COMPUTE_UNIT_PRICE))
            
            # Create associated token account if it doesn't exist
            if not dest_exists:
                print(f"Creating associated token account for safe wallet...")
                create_ata_ix = create_associated_token_account(
                    payer=source_wallet.pubkey(),
                    owner=safe_wallet_pubkey,
                    mint=mint_pubkey
                )
                instructions.append(create_ata_ix)
            
            # Transfer tokens
            transfer_ix = transfer_checked(
                TransferCheckedParams(
                    program_id=TOKEN_PROGRAM_ID,
                    source=source_token_account,
                    mint=mint_pubkey,
                    dest=dest_token_account,
                    owner=source_wallet.pubkey(),
                    amount=amount,
                    decimals=decimals,
                    signers=[]
                )
            )
            instructions.append(transfer_ix)
            
            # Get FRESH recent blockhash with Processed commitment for speed
            print("Fetching fresh blockhash...")
            recent_blockhash_resp = await client.get_latest_blockhash(commitment=Processed)
            recent_blockhash = recent_blockhash_resp.value.blockhash
            print(f"Blockhash: {recent_blockhash}")
            
            # Create and sign transaction
            message = MessageV0.try_compile(
                payer=source_wallet.pubkey(),
                instructions=instructions,
                address_lookup_table_accounts=[],
                recent_blockhash=recent_blockhash,
            )
            
            tx = VersionedTransaction(message, [source_wallet])
            
            # Send transaction with skip_preflight for faster submission
            print(f"Sending transaction to transfer {amount} tokens...")
            tx_opts = TxOpts(
                skip_preflight=False,
                preflight_commitment=Processed,
                max_retries=3
            )
            
            sig = await client.send_transaction(tx, opts=tx_opts)
            print(f"Transaction signature: {sig.value}")
            print(f"View on Solscan: https://solscan.io/tx/{sig.value}")
            
            # Confirm transaction with timeout
            print("Confirming transaction...")
            try:
                confirmation = await asyncio.wait_for(
                    client.confirm_transaction(sig.value, commitment=Confirmed),
                    timeout=60.0
                )
                
                if confirmation.value[0].err:
                    print(f"❌ Transaction failed: {confirmation.value[0].err}")
                    if attempt < max_retries - 1:
                        print(f"Retrying in 2 seconds...")
                        await asyncio.sleep(2)
                        continue
                    return False
                
                print(f"✅ Successfully transferred {amount / (10 ** decimals)} tokens to safe wallet")
                return True
                
            except asyncio.TimeoutError:
                print("⏱️  Transaction confirmation timed out")
                print(f"Transaction may still succeed. Check: https://solscan.io/tx/{sig.value}")
                if attempt < max_retries - 1:
                    print(f"Retrying in 2 seconds...")
                    await asyncio.sleep(2)
                    continue
                return False
            
        except Exception as e:
            print(f"❌ Error transferring tokens (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in 2 seconds...")
                await asyncio.sleep(2)
            else:
                import traceback
                traceback.print_exc()
                return False
    
    return False


async def handle_account_update(
    parsed_response: dict,
    client: AsyncClient,
    source_wallet: Keypair,
    safe_wallet_pubkey: Pubkey
):
    """Handle account update and transfer tokens if needed"""
    try:
        mint_address = parsed_response.get('mint')
        amount = parsed_response.get('amount')
        account_address = parsed_response.get('account_address')
        
        if not mint_address or amount is None or amount == 0:
            print("No tokens to transfer or invalid data")
            return
        
        print(f"\n🔔 Token account update detected!")
        print(f"Account: {account_address}")
        print(f"Mint: {mint_address}")
        print(f"Amount: {amount}")
        s_t = time.time()

        # Get token decimals
        decimals = await get_token_decimals(client, mint_address)
        print(f"Decimals: {decimals}")
        
        # Convert addresses to Pubkey objects
        mint_pubkey = Pubkey.from_string(mint_address)
        source_token_account = Pubkey.from_string(account_address)
        
        # Transfer tokens
        success = await transfer_tokens(
            client=client,
            source_wallet=source_wallet,
            safe_wallet_pubkey=safe_wallet_pubkey,
            mint_pubkey=mint_pubkey,
            source_token_account=source_token_account,
            amount=amount,
            decimals=decimals
        )
        
        if success:
            print("✅ Transfer completed successfully")
            print(f"it took {time.time() - s_t} seconds to get transfer tokens")
        else:
            print("❌ Transfer failed")
            
    except Exception as e:
        print(f"Error handling account update: {e}")
        import traceback
        traceback.print_exc()


async def airdrop_safety_monitor(hacked_wallet_env_vars: list[str], safe_wallet_env_var: str):
    wallet_addresses = []
    wallet_addresses_lower = []
    wallet_keypairs = {}

    print("Monitoring wallets for token transfers:")
    for env_var in set(hacked_wallet_env_vars):
        wallet_priv = os.environ.get(env_var)
        if not wallet_priv:
            raise ValueError(f"{env_var} not found in environment variables")

        private_key_bytes = base58.b58decode(wallet_priv)
        wallet_keypair = Keypair.from_bytes(private_key_bytes)
        wallet_address = str(wallet_keypair.pubkey())
        wallet_address_lower = wallet_address.lower()

        wallet_addresses.append(wallet_address)
        wallet_addresses_lower.append(wallet_address_lower)
        wallet_keypairs[wallet_address_lower] = wallet_keypair

        print(f"    {str(wallet_keypair.pubkey())}")


    safe_wallet_priv = os.environ.get(safe_wallet_env_var)
    safe_wallet_private_key_bytes = base58.b58decode(safe_wallet_priv)
    safe_wallet_keypair = Keypair.from_bytes(safe_wallet_private_key_bytes)
    safe_wallet_pub = safe_wallet_keypair.pubkey()


    print(f"Safety wallet: {safe_wallet_pub}")

    # Create RPC client
    client = AsyncClient(RPC_ENDPOINT)
    
    running = True
    try:
        while running:
            try:
                monitor = AccountsChangesStream(GRPC_ENDPOINT, GRPC_TOKEN, wallet_addresses)
                
                async for response in monitor.start_monitoring():
                    parsed_response = AccountChangeParser.parse_account_update(response)
                    print(f"\n📊 Account Update: {parsed_response}")
                    if parsed_response:
                        owner_wallet_address_lower = parsed_response['token_owner'].lower()
                        if owner_wallet_address_lower in wallet_addresses_lower:
                            source_wallet = wallet_keypairs[owner_wallet_address_lower]
                            await handle_account_update(
                                parsed_response,
                                client,
                                source_wallet,
                                safe_wallet_pub
                            )
                    
            except ConnectionTimeoutError as e:
                print(f"Connection timeout: {e}")
                await asyncio.sleep(5)
                continue
            except RpcError as rpc_error:
                if rpc_error.code() == StatusCode.DATA_LOSS:
                    print("Data loss detected")
                print(f"\nGRPC connection error: {rpc_error}")
                print("Attempting to reconnect in 5 seconds...")
                await asyncio.sleep(5)
                continue
                
    except asyncio.CancelledError:
        print("\nAsyncio task was cancelled. Shutting down gracefully...")
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Stopping gracefully...")
    finally:
        await client.close()

async def main():
    hacked_wallet_env_vars = ["WALLET_2_PRIV"]
    safe_wallet_env_var = "WALLET_1_PRIV"

    await airdrop_safety_monitor(hacked_wallet_env_vars, safe_wallet_env_var)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Force exit detected.")