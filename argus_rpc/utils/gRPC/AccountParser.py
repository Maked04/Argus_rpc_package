import base58
import struct
from typing import Optional, Dict, Any

class AccountChangeParser:
    """Parser for Solana account changes, specifically for detecting token account updates"""
    
    # SPL Token Program ID
    TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
    
    @staticmethod
    def parse_account_update(update) -> Optional[Dict[str, Any]]:
        """
        Parse an account update from gRPC stream
        
        Returns:
            Dictionary with account info if it's a token account, None otherwise
        """
        if not hasattr(update, 'account') or not update.account or not update.account.account:
            print("here1")
            return None
        
        account = update.account.account
        slot = update.account.slot
        
        # Decode the account pubkey
        account_pubkey = base58.b58encode(bytes(account.pubkey)).decode()
        
        # Decode the owner (program that owns this account)
        owner = base58.b58encode(bytes(account.owner)).decode()
        
        # Get basic account info
        lamports = account.lamports
        data = bytes(account.data)
        
        # Parse token account data
        token_info = AccountChangeParser.parse_token_account_data(data)
        if not token_info:
            print("here2")
            return None
        
        return {
            'account_address': account_pubkey,
            'slot': slot,
            'lamports': lamports,
            'owner': owner,
            'mint': token_info['mint'],
            'token_owner': token_info['owner'],
            'amount': token_info['amount'],
            'decimals': token_info['decimals'],
            'ui_amount': token_info['ui_amount'],
            'write_version': account.write_version,
            'txn_signature': base58.b58encode(bytes(account.txn_signature)).decode() if account.txn_signature else None
        }
    
    @staticmethod
    def parse_token_account_data(data: bytes) -> Optional[Dict[str, Any]]:
        """
        Parse SPL token account data
        
        Token account layout:
        - mint: 32 bytes (pubkey)
        - owner: 32 bytes (pubkey)
        - amount: 8 bytes (u64)
        - delegate: 36 bytes (COption<Pubkey>)
        - state: 1 byte
        - is_native: 12 bytes (COption<u64>)
        - delegated_amount: 8 bytes (u64)
        - close_authority: 36 bytes (COption<Pubkey>)
        """
        if len(data) < 165:  # Minimum size for token account
            return None
        
        try:
            # Extract mint (first 32 bytes)
            mint = base58.b58encode(data[0:32]).decode()
            
            # Extract owner (next 32 bytes)
            owner = base58.b58encode(data[32:64]).decode()
            
            # Extract amount (next 8 bytes, little-endian u64)
            amount = struct.unpack('<Q', data[64:72])[0]
            
            # For decimals, we'd need to fetch mint info separately
            # For now, we'll return raw amount and set decimals to None
            # In practice, you should cache mint decimals or fetch them
            
            return {
                'mint': mint,
                'owner': owner,
                'amount': amount,
                'decimals': None,  # Would need to fetch from mint account
                'ui_amount': None  # Calculate as: amount / (10 ** decimals)
            }
            
        except Exception as e:
            return None
    
    @staticmethod
    def is_new_token_account(update) -> bool:
        """
        Check if this update represents a newly created token account
        This would indicate a potential airdrop
        """
        if not hasattr(update, 'account') or not update.account:
            return False
        
        # Check if this is marked as a startup account (exists at subscription time)
        # If is_startup is False, it's a new account created after subscription
        return not update.account.is_startup
    
    @staticmethod
    def get_account_signature(update) -> Optional[str]:
        """Extract the transaction signature that caused this account change"""
        if (hasattr(update, 'account') and 
            update.account and 
            update.account.account and 
            update.account.account.txn_signature):
            return base58.b58encode(bytes(update.account.account.txn_signature)).decode()
        return None