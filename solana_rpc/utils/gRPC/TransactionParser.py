import base58

from solana_rpc.utils.TransactionTypes import *

RAYDIUM_V4_ACCOUNT = '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8'
RAYDIUM_V4_AUTHORITY_ADDRESS = "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"
WSOL_TOKEN_ADDRESS = "So11111111111111111111111111111111111111112"

class TransactionParser:
    @staticmethod
    def parse_raydium_v4_transaction(update, debug=False) -> RaydiumV4Transaction:
        is_creator = False

        tx_info = update.transaction.transaction
        message = tx_info.transaction.message
        meta = tx_info.meta

        num_of_signers = message.header.num_required_signatures

        account_keys = [base58.b58encode(bytes(account_key)).decode() for account_key in message.account_keys]

        signers = account_keys[:num_of_signers]

        pre_balances = meta.pre_balances
        post_balances = meta.post_balances

        pre_token_balances = meta.pre_token_balances
        post_token_balances = meta.post_token_balances

        all_token_balances = []
        for b in pre_token_balances:
            all_token_balances.append(b)
        
        for b in post_token_balances:
            all_token_balances.append(b)


        block_time = update.created_at.seconds
        slot = update.transaction.slot
        fee = meta.fee / 1e9
        signature=base58.b58encode(bytes(tx_info.signature)).decode()

        # Remove no spl change signers
        signers = [signer for signer in signers if signer in [balance.owner for balance in all_token_balances]]
        if len(signers) == 0:
            if debug:
                print(f"DEBUG: No signers for tx: {signature}")
            return None
        
        elif len(signers) > 1:
            if len(signers) >= 3:
                if debug:
                    print(f"DEBUG: 3 or more signers")
                return None
            else:  # If this condition is met then theres 2 signers
                zero_changes = []
                for signer in signers:
                    signer_account_key_index = account_keys.index(signer)
                    pre, post = pre_balances[signer_account_key_index], post_balances[signer_account_key_index]
                    #if pre == 0 and post == 0 or abs(pre - post) == 0:
                    if pre == 0 and post == 0:
                        zero_changes.append(signer)
                if len(zero_changes) == 1:
                    signer = next((signer for signer in signers if signer not in zero_changes))
                else:
                    if debug:
                        print(f"DEBUG: There was 2 signers but unable to determine which one is main signer, tx: {signature}")
                    return None

        signer = signers[0]
        signer_account_key_index = account_keys.index(signer)

        mint_accounts = set([balance.mint for balance in all_token_balances])
        # Only process if theres 2 or 3 mint accounts (2 for normal, 3 for when liquidity is added)
        if len(mint_accounts) not in [2, 3]:
            if debug:
                print(f"Not 2 or 3 mints in: {signature}")
            return None

        raydium_owned_tokens = set([balance.mint for balance in all_token_balances if balance.owner == RAYDIUM_V4_AUTHORITY_ADDRESS])
        if len(raydium_owned_tokens) == 2 and WSOL_TOKEN_ADDRESS in raydium_owned_tokens:
            spl_token_address = next((mint for mint in raydium_owned_tokens if mint != WSOL_TOKEN_ADDRESS))

            pool_spl_before = next((balance.ui_token_amount.ui_amount or 0 for balance in pre_token_balances if balance.mint != WSOL_TOKEN_ADDRESS and balance.owner == RAYDIUM_V4_AUTHORITY_ADDRESS), 0)
            pool_spl_after = next((balance.ui_token_amount.ui_amount or 0 for balance in post_token_balances if balance.mint != WSOL_TOKEN_ADDRESS and balance.owner == RAYDIUM_V4_AUTHORITY_ADDRESS), 0)

            pool_wsol_before = next((balance.ui_token_amount.ui_amount or 0 for balance in pre_token_balances if balance.mint == WSOL_TOKEN_ADDRESS and balance.owner == RAYDIUM_V4_AUTHORITY_ADDRESS), 0)
            pool_wsol_after = next((balance.ui_token_amount.ui_amount or 0 for balance in post_token_balances if balance.mint == WSOL_TOKEN_ADDRESS and balance.owner == RAYDIUM_V4_AUTHORITY_ADDRESS), 0)

            if pool_spl_after - pool_spl_before == 0:
                return None

            token_price = abs((pool_wsol_after - pool_wsol_before) / (pool_spl_after - pool_spl_before))

        else:
            if debug:
                print(f"There isn't 2 raydium owned tokens, one being wsol: {signature}")
            return None
        
        if len(mint_accounts) == 3:
            # I've observed when inital liquidity is added there should just be one token change which is the signer receiving lp mint tokens
            other_token_mint = next(mint for mint in mint_accounts if mint != WSOL_TOKEN_ADDRESS and mint != spl_token_address)
            
            other_token_changes = [balance for balance in all_token_balances if balance.mint == other_token_mint and balance.owner == signer]
            if len(other_token_changes) == 1 and pool_wsol_before == 0 and pool_spl_before == 0:
                is_creator = True
                other_token_change = other_token_changes[0]
                if other_token_change in post_token_balances:  # Should only have post change as they're being given first lp tokens
                    post_token_balances.remove(other_token_change)
                    all_token_balances.remove(other_token_change)
                else:
                    if debug:
                        print(f"Weird situation here where looks like creator tx but signer had some lp tokens before, tx: {signature}")
                    return None
            else:
                if debug:
                    print(f"There was 3 mint tokens in tx but wasn't inital liquidity being added, tx: {signature}")
                return None  # Not a creation transaction so can't handle it
        
        # AT THIS POINT EITHER EXTRA MINT HAS BEEN REMOVED OR RETURNED NONE
        signer_sol_before, signer_sol_after = pre_balances[signer_account_key_index], post_balances[signer_account_key_index]
        signer_sol_change = (signer_sol_after - signer_sol_before) / 1e9

        signer_owned_tokens = set([balance.mint for balance in all_token_balances if balance.owner == signer])

        if WSOL_TOKEN_ADDRESS in signer_owned_tokens:
            signer_wsol_before = next((balance.ui_token_amount.ui_amount or 0 for balance in pre_token_balances if balance.mint == WSOL_TOKEN_ADDRESS and balance.owner == signer), 0)
            signer_wsol_after = next((balance.ui_token_amount.ui_amount or 0 for balance in post_token_balances if balance.mint == WSOL_TOKEN_ADDRESS and balance.owner == signer), 0)
            signer_wsol_change = signer_wsol_after - signer_wsol_before
            signer_sol_change += signer_wsol_change

        signer_spl_before = next((balance.ui_token_amount.ui_amount or 0 for balance in pre_token_balances if balance.mint == spl_token_address and balance.owner == signer), 0)
        signer_spl_after = next((balance.ui_token_amount.ui_amount or 0 for balance in post_token_balances if balance.mint == spl_token_address and balance.owner == signer), 0)

        if signer_spl_after - signer_spl_before == 0: # or abs(pool_wsol_after-pool_wsol_before) < 0.05:
            if debug:
                print(f"DEBUG: Not including tx as either no spl change or sol change is less than 0.05 SOL")
            return None

        return RaydiumV4Transaction(tx_sig=signature,
                                    block_time=block_time,
                                    slot=slot,
                                    fee=fee,
                                    token_price=token_price,
                                    token_address=spl_token_address,
                                    is_creator=is_creator,
                                    signer=signer,
                                    pool_spl_before=pool_spl_before,
                                    pool_spl_after=pool_spl_after,
                                    pool_wsol_before=pool_wsol_before,
                                    pool_wsol_after=pool_wsol_after,
                                    signer_spl_before=signer_spl_before,
                                    signer_spl_after=signer_spl_after,
                                    signer_sol_change=signer_sol_change)

    @staticmethod
    def parse_pumpfun_transaction(update, debug=False) -> PumpFunTransaction:
        tx_info = update.transaction.transaction
        message = tx_info.transaction.message
        meta = tx_info.meta

        num_of_signers = message.header.num_required_signatures

        account_keys = [base58.b58encode(bytes(account_key)).decode() for account_key in message.account_keys]

        signers = account_keys[:num_of_signers]

        pre_balances = meta.pre_balances
        post_balances = meta.post_balances

        pre_token_balances = meta.pre_token_balances
        post_token_balances = meta.post_token_balances

        all_token_balances = []
        for b in pre_token_balances:
            all_token_balances.append(b)
        
        for b in post_token_balances:
            all_token_balances.append(b)

        block_time = update.created_at.seconds
        slot = update.transaction.slot
        fee = meta.fee / 1e9
        signature=base58.b58encode(bytes(tx_info.signature)).decode()
                
        signers = [signer for signer in signers if signer in [balance.owner for balance in all_token_balances]]

        mint_accounts = set([balance.mint for balance in all_token_balances])

        # If more than one skip tx 
        if len(mint_accounts) > 1:
            if debug:
                print(f"DEBUG, more than two different spl tokens for tx: {signature}")
            return None
        elif len(mint_accounts) == 0:
            if debug:
                print(f"DEBUG, no spl token balance changes for tx: {signature}")
            return None
        else:
            token_address = mint_accounts.pop()
        
        if len(signers) == 1:
            signer = signers[0]
        else:
            if len(signers) == 2:
                signer = [signer for signer in signers if signer != token_address][0]  # On token creation we've seen two signers, one creator and one mint address so get creator
            else:
                if debug:
                    print(f"ERROR, more than 2 signer wallets for tx: {signature}")
                return None

        # We're assuming theres only two changes so if more print warning message
        if len(pre_token_balances) > 2 or len(post_token_balances) > 2:
            # Monitor this print to see if its some weird fee thing being sent to: ZG98FUCjb8mJ824Gbs6RsgVmr1FhXb2oNiJHa2dwmPd
            if debug:
                print(f"ERROR, more than two or only one balance changes for tx: {signature} so returning None")
            return None

        # All wallets in pre or post (Should be signer and bonding curve address)
        spl_accounts = [balance.owner for balance in all_token_balances]
        if signer not in spl_accounts:
            if debug:
                print(f"ERROR, no spl changes for signer wallet for tx: {signature}")
            return None

        if len(spl_accounts) < 2:
            if debug:
                print(f"ERROR, less than two accounts with spl changes for tx: {signature}")
            return None

        non_signer_accounts = list({account for account in spl_accounts if account != signer})  # Remove duplicates as there may be 1 for post and 1 for pre
        if len(non_signer_accounts) == 1:  # For transactions we can handle there should only be one spl change account other than signer
            bonding_curve_address = non_signer_accounts[0]
        else:
            if debug:
                print(f"ERROR, only signer had spl changes so can't get bonding curve changes for tx: {signature}")
            return None
        
        signer_spl_before = next((balance.ui_token_amount.ui_amount or 0 for balance in pre_token_balances if balance.owner == signer), 0)
        signer_spl_after = next((balance.ui_token_amount.ui_amount or 0 for balance in post_token_balances if balance.owner == signer), 0)

        bonding_curve_spl_before = next((balance.ui_token_amount.ui_amount or 0 for balance in pre_token_balances if balance.owner == bonding_curve_address), 0)
        bonding_curve_spl_after = next((balance.ui_token_amount.ui_amount or 0 for balance in post_token_balances if balance.owner == bonding_curve_address), 0)
        if bonding_curve_address not in account_keys:
            if debug:
                print(f"Bonding curve address not in account keys, pretty sure it means nothing was swapped, usually on token creation")
            return None 
        bonding_curve_account_key_index = account_keys.index(bonding_curve_address)
        bonding_curve_sol_before, bonding_curve_sol_after = pre_balances[bonding_curve_account_key_index]/1e9, post_balances[bonding_curve_account_key_index]/1e9

        if bonding_curve_spl_after - bonding_curve_spl_before == 0:
            return None

        signer_account_key_index = account_keys.index(signer)
        signer_sol_before, signer_sol_after = pre_balances[signer_account_key_index]/1e9, post_balances[signer_account_key_index]/1e9

        token_price = abs((bonding_curve_sol_after - bonding_curve_sol_before) / (bonding_curve_spl_after - bonding_curve_spl_before))

        if signer_spl_after - signer_spl_before == 0:# or abs(bonding_curve_sol_after - bonding_curve_sol_before) < 0.05:
            if debug:
                print(f"DEBUG: Not including tx as either no spl change or sol change is less than 0.05 SOL")
            return None

        return PumpFunTransaction(
            tx_sig=signature,
            block_time=block_time,
            slot=slot,
            fee=fee,
            token_price=token_price,
            token_address=token_address,
            is_creator = True if bonding_curve_spl_before == 0 else False,
            signer=signer,
            bc_spl_before=bonding_curve_spl_before,
            bc_spl_after=bonding_curve_spl_after,
            bc_sol_before=bonding_curve_sol_before,
            bc_sol_after=bonding_curve_sol_after,
            signer_spl_before=signer_spl_before,
            signer_spl_after=signer_spl_after,
            signer_sol_before=signer_sol_before,
            signer_sol_after=signer_sol_after
        )
    
    @staticmethod 
    def contains_program(update, program_address) -> bool:
        message = update.transaction.transaction.transaction.message
        account_keys = [base58.b58encode(bytes(account_key)).decode() for account_key in message.account_keys]

        return program_address in account_keys
    
    @staticmethod
    def get_tx_signature(update):
        tx_info = update.transaction.transaction
        signature=base58.b58encode(bytes(tx_info.signature)).decode()

        return signature
