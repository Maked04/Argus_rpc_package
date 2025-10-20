from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed, Processed
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solders.system_program import TransferParams, transfer
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from solana.rpc.types import TxOpts
import asyncio

# Compute budget settings
COMPUTE_UNIT_LIMIT = 200_000
COMPUTE_UNIT_PRICE = 50_000


async def send_sol(
    client: AsyncClient,
    sender: Keypair,
    recipient_pubkey: Pubkey,
    amount_sol: float,
    max_retries: int = 3
) -> bool:
    """
    Send SOL from sender to recipient.
    
    Args:
        client: Solana RPC client
        sender: Keypair of the sender (must have enough SOL + fees)
        recipient_pubkey: Public key of the recipient
        amount_sol: Amount of SOL to send (in SOL, not lamports)
        max_retries: Number of retry attempts
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Convert SOL to lamports (1 SOL = 1,000,000,000 lamports)
    LAMPORTS_PER_SOL = 1_000_000_000
    amount_lamports = int(amount_sol * LAMPORTS_PER_SOL)
    
    for attempt in range(max_retries):
        try:
            print(f"\n{'=' * 60}")
            print(f"SOL Transfer attempt {attempt + 1}/{max_retries}")
            print(f"{'=' * 60}")
            print(f"From: {sender.pubkey()}")
            print(f"To: {recipient_pubkey}")
            print(f"Amount: {amount_sol} SOL ({amount_lamports} lamports)")
            
            instructions = []
            
            # Add compute budget instructions
            instructions.append(set_compute_unit_limit(COMPUTE_UNIT_LIMIT))
            instructions.append(set_compute_unit_price(COMPUTE_UNIT_PRICE))
            
            # Create transfer instruction
            transfer_ix = transfer(
                TransferParams(
                    from_pubkey=sender.pubkey(),
                    to_pubkey=recipient_pubkey,
                    lamports=amount_lamports
                )
            )
            instructions.append(transfer_ix)
            
            # Get fresh blockhash
            print("Fetching fresh blockhash...")
            recent_blockhash_resp = await client.get_latest_blockhash(commitment=Processed)
            recent_blockhash = recent_blockhash_resp.value.blockhash
            print(f"Blockhash: {recent_blockhash}")
            
            # Create and sign transaction
            message = MessageV0.try_compile(
                payer=sender.pubkey(),
                instructions=instructions,
                address_lookup_table_accounts=[],
                recent_blockhash=recent_blockhash,
            )
            
            tx = VersionedTransaction(message, [sender])
            
            # Send transaction
            print(f"Sending transaction...")
            tx_opts = TxOpts(
                skip_preflight=False,
                preflight_commitment=Processed,
                max_retries=3
            )
            
            sig = await client.send_transaction(tx, opts=tx_opts)
            print(f"Transaction signature: {sig.value}")
            print(f"View on Solscan: https://solscan.io/tx/{sig.value}")
            
            # Confirm transaction
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
                
                print(f"✅ Successfully sent {amount_sol} SOL to {recipient_pubkey}")
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
            print(f"❌ Error sending SOL (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in 2 seconds...")
                await asyncio.sleep(2)
            else:
                import traceback
                traceback.print_exc()
                return False
    
    return False


async def get_sol_balance(client: AsyncClient, pubkey: Pubkey) -> float:
    """
    Get SOL balance of an account.
    
    Args:
        client: Solana RPC client
        pubkey: Public key to check balance
        
    Returns:
        float: Balance in SOL
    """
    try:
        response = await client.get_balance(pubkey, commitment=Confirmed)
        lamports = response.value
        sol_balance = lamports / 1_000_000_000
        return sol_balance
    except Exception as e:
        print(f"Error fetching balance: {e}")
        return 0.0


# Example usage
async def main():
    import base58
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    RPC_ENDPOINT = os.environ.get("HELIUS_ENDPOINT", "https://api.mainnet-beta.solana.com")
    client = AsyncClient(RPC_ENDPOINT)
    
    # Load sender wallet
    sender_private = os.environ.get("WALLET_1_PRIV")
    if not sender_private:
        raise ValueError("WALLET_1_PRIV not found in environment variables")
    
    sender_private_key_bytes = base58.b58decode(sender_private)
    sender = Keypair.from_bytes(sender_private_key_bytes)
    
    # Load recipient wallet
    recipient_private = os.environ.get("WALLET_2_PRIV")
    if not recipient_private:
        raise ValueError("WALLET_2_PRIV not found in environment variables")
    
    recipient_private_key_bytes = base58.b58decode(recipient_private)
    recipient = Keypair.from_bytes(recipient_private_key_bytes)
    recipient_pubkey = recipient.pubkey()
    
    print("=== Initial Balances ===")
    sender_balance = await get_sol_balance(client, sender.pubkey())
    recipient_balance = await get_sol_balance(client, recipient_pubkey)
    print(f"Sender balance: {sender_balance:.6f} SOL")
    print(f"Recipient balance: {recipient_balance:.6f} SOL")
    
    # Send 0.001 SOL
    amount_to_send = 0.01
    
    success = await send_sol(
        client=client,
        sender=sender,
        recipient_pubkey=recipient_pubkey,
        amount_sol=amount_to_send
    )
    
    if success:
        print("\n=== Final Balances ===")
        # Wait a moment for balance to update
        await asyncio.sleep(2)
        sender_balance_after = await get_sol_balance(client, sender.pubkey())
        recipient_balance_after = await get_sol_balance(client, recipient_pubkey)
        print(f"Sender balance: {sender_balance_after:.6f} SOL")
        print(f"Recipient balance: {recipient_balance_after:.6f} SOL")
        
        print(f"\n💰 Sender change: {sender_balance_after - sender_balance:.6f} SOL")
        print(f"💰 Recipient change: {recipient_balance_after - recipient_balance:.6f} SOL")
    
    await client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nForce exit detected.")