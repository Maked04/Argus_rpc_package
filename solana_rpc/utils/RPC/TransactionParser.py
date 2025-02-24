from .RPCResponses import RPCTransaction
from solana_rpc.utils.TransactionTypes import *


RAYDIUM_V4_PROGRAM_ADDRESS = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
RAYDIUM_V4_AUTHORITY_ADDRESS = "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"
WSOL_TOKEN_ADDRESS = "So11111111111111111111111111111111111111112"


def remove_no_spl_changes(pre_balances, post_balances):
    """ Removes pre balance and post balance for account where change was 0 """

    account_balances = {balance['accountIndex']: 0 for balance in pre_balances + post_balances}

    for balance in post_balances:
        account_balances[balance['accountIndex']] += balance["uiTokenAmount"].get("uiAmount") or 0
    for balance in pre_balances:
        account_balances[balance['accountIndex']] -= balance["uiTokenAmount"].get("uiAmount") or 0

    account_indexes_to_remove = [account_index for account_index, spl_change in account_balances.items() if spl_change == 0]

    pre_balances = [balance for balance in pre_balances if balance['accountIndex'] not in account_indexes_to_remove]
    post_balances = [balance for balance in post_balances if balance['accountIndex'] not in account_indexes_to_remove]

    return pre_balances, post_balances

def get_pump_fun_spl_balances(transaction: RPCTransaction, debug=False):
    """ Pump fun transactions are direct sol - token swap and so only 1 spl token 
        2 sets of changes are the signers and the bonding curves token holdings
        
        This method returns signer and bonding curves balances, the token mint address, used signer address and the bonding curve address"""

    SPL_pre_balances = transaction.pre_token_balances
    SPL_post_balances = transaction.post_token_balances

    # Remove balances where change is 0
    SPL_pre_balances, SPL_post_balances = remove_no_spl_changes(SPL_pre_balances, SPL_post_balances)

    signer_wallets = [key["pubkey"] for key in transaction.accounts if key['signer']]
    # Only count signers that have spl change
    signer_wallets = [signer for signer in signer_wallets if signer in [balance["owner"] for balance in SPL_pre_balances + SPL_post_balances]]

    # Token address should be the mint of any balance in spls
    # Get all mints
    mint_accounts = set([balance['mint'] for balance in SPL_post_balances + SPL_post_balances])
    # If more than one skip tx 
    if len(mint_accounts) > 1:
        if debug:
            print(f"ERROR, more than two different spl tokens for tx: {transaction.signature}")
        return None
    elif len(mint_accounts) == 0:
        if debug:
            print(f"ERROR, no spl token balance changes for tx: {transaction.signature}")
        return None
    else:
        token_address = mint_accounts.pop()
    
    if len(signer_wallets) == 1:
        signer = signer_wallets[0]
    else:
        if len(signer_wallets) == 2:
            signer = [signer for signer in signer_wallets if signer != token_address][0]  # On token creation we've seen two signers, one creator and one mint address so get creator
        else:
            if debug:
                print(f"ERROR, more than 2 signer wallets for tx: {transaction.signature}")
            return None

    # We're assuming theres only two changes so if more print warning message
    if len(SPL_pre_balances) > 2 or len(SPL_post_balances) > 2:
        # Monitor this print to see if its some weird fee thing being sent to: ZG98FUCjb8mJ824Gbs6RsgVmr1FhXb2oNiJHa2dwmPd
        if debug:
            print(f"ERROR, more than two or only one balance changes for tx: {transaction.signature} so returning None")
        return None

    # All wallets in pre or post (Should be signer and bonding curve address)
    spl_accounts = [balance['owner'] for balance in SPL_pre_balances + SPL_post_balances]
    if signer not in spl_accounts:
        if debug:
            print(f"ERROR, no spl changes for signer wallet for tx: {transaction.signature}")
        return None

    if len(spl_accounts) < 2:
        if debug:
            print(f"ERROR, less than two accounts with spl changes for tx: {transaction.signature}")
        return None

    non_signer_accounts = list({account for account in spl_accounts if account != signer})  # Remove duplicates as there may be 1 for post and 1 for pre
    if len(non_signer_accounts) == 1:  # For transactions we can handle there should only be one spl change account other than signer
        bonding_curve_address = non_signer_accounts[0]
    else:
        print(f"ERROR, only signer had spl changes so can't get bonding curve changes for tx: {transaction.signature}")
        return None

    signer_spl_before = next((balance["uiTokenAmount"].get("uiAmount") or 0 for balance in SPL_pre_balances if balance['owner'] == signer), 0)
    signer_spl_after = next((balance["uiTokenAmount"].get("uiAmount") or 0 for balance in SPL_post_balances if balance['owner'] == signer), 0)

    bonding_curve_spl_before = next((balance["uiTokenAmount"].get("uiAmount") or 0 for balance in SPL_pre_balances if balance['owner'] == bonding_curve_address), 0)
    bonding_curve_spl_after = next((balance["uiTokenAmount"].get("uiAmount") or 0 for balance in SPL_post_balances if balance['owner'] == bonding_curve_address), 0)

    return bonding_curve_spl_before, bonding_curve_spl_after, signer_spl_before, signer_spl_after, token_address, signer, bonding_curve_address

def get_addresses_sol_balances(transaction: RPCTransaction, address, debug=False):
    """ Returns the given addresses sol balance changes within the given transaction info """
    pre_balances = transaction.pre_balances
    post_balances = transaction.post_balances
    account_keys = transaction.accounts

    wallet_index = next((index for index, key in enumerate(account_keys) if key['pubkey'] == address), None)
    if wallet_index is None:
        if debug:
            print(f"Unable to find {address} in account keys of tx: {transaction.signature}")
        return None
    
    return pre_balances[wallet_index] / 1e9, post_balances[wallet_index] /1e9

def extract_pump_fun_transaction(transaction: RPCTransaction, debug=False) -> PumpFunTransaction:
    result = get_pump_fun_spl_balances(transaction, debug=debug)
    if not result:
        return None
    bonding_curve_spl_before, bonding_curve_spl_after, signer_spl_before, signer_spl_after, token_address, signer, bonding_curve_address = result

    result = get_addresses_sol_balances(transaction, bonding_curve_address, debug=debug)
    if not result:
        return None
    bonding_curve_sol_before, bonding_curve_sol_after = result

    if bonding_curve_spl_after - bonding_curve_spl_before == 0:
        return None
    token_price = abs((bonding_curve_sol_after - bonding_curve_sol_before) / (bonding_curve_spl_after - bonding_curve_spl_before))

    result = get_addresses_sol_balances(transaction, signer, debug=debug)
    if not result:
        return None
    signer_sol_before, signer_sol_after = result

    if signer_spl_after - signer_spl_before == 0:# or abs(bonding_curve_sol_after - bonding_curve_sol_before) < 0.05:
            if debug:
                print(f"DEBUG: Not including tx as either no spl change or sol change is less than 0.05 SOL")
            return None

    return PumpFunTransaction(
        tx_sig=transaction.signature,
        block_time=transaction.block_time,
        slot=transaction.slot,
        fee=transaction.fee,
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

def extract_raydium_v4_transaction(transaction: RPCTransaction, debug=False) -> RaydiumV4Transaction:
    '''This method parses normal swaps and liquidity added transactions, it filters where sol balance change is very low as this throws off price
    and also filters if theres no spl change for the signer'''
    is_creator = False

    # Extract spl changes
    SPL_pre_balances = transaction.pre_token_balances
    SPL_post_balances = transaction.post_token_balances
    signer_wallets = [key["pubkey"] for key in transaction.accounts if key['signer']]
    signer_wallets = [signer for signer in signer_wallets if signer in [balance["owner"] for balance in SPL_pre_balances + SPL_post_balances]]
    if len(signer_wallets) == 0:
        if debug:
            print(f"No signers for: {transaction.signature}")
        return None
    # Could filter ones which are signer and writable and have spl changes
    elif len(signer_wallets) > 1:
        if len(signer_wallets) > 2:
            if debug:
                print(f"More than 2 signers for tx: {transaction.signature}")
            return None
        else:
            # If one signer has no sol change, other is main signer
            zero_changes = []
            for signer in signer_wallets:
                pre, post = get_addresses_sol_balances(transaction, signer)
                if pre == 0 and post == 0:
                    zero_changes.append(signer)
            if len(zero_changes) == 1:
                signer = next((signer for signer in signer_wallets if signer not in zero_changes))
            else:
                if debug:
                    print(f"There was 2 signers but unable to determine which one is main signer, tx: {transaction.signature}")
                return None

    signer = signer_wallets[0]

    mint_accounts = set([balance['mint'] for balance in SPL_pre_balances + SPL_post_balances])
    # Only process if theres 2 or 3 mint accounts (2 for normal, 3 for when liquidity is added)
    if len(mint_accounts) not in [2, 3]:
        if debug:
            print(f"Not 2 or 3 mints in: {transaction.signature}")
        return None

    # Get mint of changes where owner is raydium v4 authority
    raydium_owned_tokens = set([balance['mint'] for balance in SPL_pre_balances + SPL_post_balances if balance["owner"] == RAYDIUM_V4_AUTHORITY_ADDRESS])
    # If theres two raydium owned token changes and one is wsol
    if len(raydium_owned_tokens) == 2 and WSOL_TOKEN_ADDRESS in raydium_owned_tokens:
        spl_token_address = next((mint for mint in raydium_owned_tokens if mint != WSOL_TOKEN_ADDRESS))

        pool_spl_before = next((balance["uiTokenAmount"].get("uiAmount") or 0 for balance in SPL_pre_balances if balance['mint'] != WSOL_TOKEN_ADDRESS and balance["owner"] == RAYDIUM_V4_AUTHORITY_ADDRESS), 0)
        pool_spl_after = next((balance["uiTokenAmount"].get("uiAmount") or 0 for balance in SPL_post_balances if balance['mint'] != WSOL_TOKEN_ADDRESS and balance["owner"] == RAYDIUM_V4_AUTHORITY_ADDRESS), 0)

        pool_wsol_before = next((balance["uiTokenAmount"].get("uiAmount") or 0 for balance in SPL_pre_balances if balance['mint'] == WSOL_TOKEN_ADDRESS and balance["owner"] == RAYDIUM_V4_AUTHORITY_ADDRESS), 0)
        pool_wsol_after = next((balance["uiTokenAmount"].get("uiAmount") or 0 for balance in SPL_post_balances if balance['mint'] == WSOL_TOKEN_ADDRESS and balance["owner"] == RAYDIUM_V4_AUTHORITY_ADDRESS), 0)

        if pool_spl_after - pool_spl_before == 0:
            return None

        token_price = abs((pool_wsol_after - pool_wsol_before) / (pool_spl_after - pool_spl_before))

    else:
        if debug:
            print(f"There isn't 2 raydium owned tokens, one being wsol: {transaction.signature}")
        return None

    # If theres 3 different spl tokens, for creation wsol, spl token, lp spl token
    if len(mint_accounts) == 3:
        # I've observed when inital liquidity is added there should just be one token change which is the signer receiving lp mint tokens
        other_token_mint = next(mint for mint in mint_accounts if mint != WSOL_TOKEN_ADDRESS and mint != spl_token_address)
        
        other_token_changes = [balance for balance in SPL_pre_balances + SPL_post_balances if balance["mint"] == other_token_mint and balance["owner"] == signer]
        if len(other_token_changes) == 1 and pool_wsol_before == 0 and pool_spl_before == 0:
            is_creator = True
            other_token_change = other_token_changes[0]
            if other_token_change in SPL_post_balances:  # Should only have post change as they're being given first lp tokens
                SPL_post_balances.remove(other_token_change)
            else:
                if debug:
                    print(f"Weird situation here where looks like creator tx but signer had some lp tokens before, tx: {transaction.signature}")
                return None
        else:
            if debug:
                print(f"There was 3 mint tokens in tx but wasn't inital liquidity being added, tx: {transaction.signature}")
            return None  # Not a creation transaction so can't handle it
    # AT THIS POINT EITHER EXTRA MINT HAS BEEN REMOVED OR RETURNED NONE
    signer_sol_before, signer_sol_after = get_addresses_sol_balances(transaction, signer)
    signer_sol_change = signer_sol_after - signer_sol_before

    signer_owned_tokens = set([balance['mint'] for balance in SPL_pre_balances + SPL_post_balances if balance["owner"] == signer])
    if WSOL_TOKEN_ADDRESS in signer_owned_tokens:
        signer_wsol_before = next((balance["uiTokenAmount"].get("uiAmount") or 0 for balance in SPL_pre_balances if balance['mint'] == WSOL_TOKEN_ADDRESS and balance['owner'] == signer), 0)
        signer_wsol_after = next((balance["uiTokenAmount"].get("uiAmount") or 0 for balance in SPL_post_balances if balance['mint'] == WSOL_TOKEN_ADDRESS and balance['owner'] == signer), 0)
        signer_wsol_change = signer_wsol_after - signer_wsol_before
        signer_sol_change += signer_wsol_change

    signer_spl_before = next((balance["uiTokenAmount"].get("uiAmount") or 0 for balance in SPL_pre_balances if balance['mint'] == spl_token_address and balance['owner'] == signer), 0)
    signer_spl_after = next((balance["uiTokenAmount"].get("uiAmount") or 0 for balance in SPL_post_balances if balance['mint'] == spl_token_address and balance['owner'] == signer), 0)
    
    if signer_spl_after - signer_spl_before == 0: # or abs(pool_wsol_after-pool_wsol_before) < 0.05:
        return None
        
    return RaydiumV4Transaction(
        transaction.signature,
        transaction.block_time,
        transaction.slot,
        transaction.fee, 
        token_price, 
        spl_token_address, 
        is_creator, 
        signer, 
        pool_spl_before, 
        pool_spl_after, 
        pool_wsol_before, 
        pool_wsol_after, 
        signer_spl_before, 
        signer_spl_after, 
        signer_sol_change)