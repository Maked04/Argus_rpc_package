import asyncio
import base58
from dotenv import load_dotenv
import time
import os
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed, Processed
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from spl.token.instructions import (
    get_associated_token_address,
    create_associated_token_account,
    transfer_checked,
    TransferCheckedParams,
)
from spl.token.constants import TOKEN_PROGRAM_ID
from solana.rpc.types import TxOpts

load_dotenv()

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


async def main():
    client = AsyncClient(RPC_ENDPOINT)
    
    # Load source wallet
    source_wallet_private = os.environ.get("WALLET_1_PRIV")
    if not source_wallet_private:
        raise ValueError("WALLET_1_PRIV not found in environment variables")
    
    source_private_key_bytes = base58.b58decode(source_wallet_private)
    source_wallet = Keypair.from_bytes(source_private_key_bytes)
    source_wallet_pub = source_wallet.pubkey()
    print(f"Source wallet: {source_wallet_pub}")

    # Load destination wallet
    dest_wallet_private = os.environ.get("WALLET_2_PRIV")
    if not dest_wallet_private:
        raise ValueError("WALLET_2_PRIV not found in environment variables")
    
    dest_private_key_bytes = base58.b58decode(dest_wallet_private)
    dest_wallet = Keypair.from_bytes(dest_private_key_bytes)
    dest_wallet_pub = dest_wallet.pubkey()
    print(f"Destination wallet: {dest_wallet_pub}")

    mint_address = Pubkey.from_string("EBKSfNPfVPBbh2PworA5rpHm3Y98m8QL29b1r3Jvpump")
    source_token_account = Pubkey.from_string("5n3T8E5To3fzAYFbzV198omLMesjsWmx5TZXCcqMuaEa")

    # IMPORTANT: Amount must be in smallest units (like lamports)
    # For 6 decimals: 0.00001 tokens = 10 smallest units
    decimals = 6
    amount_in_tokens = 0.00001
    amount = int(amount_in_tokens * (10 ** decimals))  # Convert to smallest units
    
    print(f"\nTransferring {amount_in_tokens} tokens ({amount} smallest units)")
    print(f"Mint: {mint_address}")
    print(f"From: {source_token_account}")

    s_t = time.time()
    success = await transfer_tokens(
        client=client,
        source_wallet=source_wallet,
        safe_wallet_pubkey=dest_wallet_pub,
        mint_pubkey=mint_address,
        source_token_account=source_token_account,
        amount=amount,
        decimals=decimals
    )
    
    if success:
        print("\n✅ Transfer completed successfully!")
        print(f"it took {time.time() - s_t} seconds to get transfer tokens")
    else:
        print("\n❌ Transfer failed after all retries")
    
    await client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nForce exit detected.")