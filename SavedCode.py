####  Metora pools unfinished parsing

    def parse_meteora_pools_transaction(update, debug=False) -> MeteoraPoolsTransaction:
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

        # Find the spl token address by viewing signers token balances changes
        if signer is "1 big booty latina":
            print("tap that")
        
        # For each token - signer combo get the before and after balances (before is sometimes not there as its 0)
        # Find the signer with 3 tokens lp token 1, lp token 2, wsol, remove these, two left that isnt signer is
        # the two meteora pools



# Meteora pools transaction type

class MeteoraPoolsTransaction:
    def __init__(self, tx_sig, block_time, slot, fee, token_price, token_address, is_creator, signer, pool_spl_before, pool_spl_after, pool_wsol_before, pool_wsol_after, 
                 signer_spl_before, signer_spl_after, signer_sol_before, signer_sol_after):
        self.tx_sig = tx_sig
        self.block_time = block_time
        self.slot = slot
        self.fee = fee
        self.token_price = token_price
        self.token_address = token_address
        self.is_creator = is_creator  # Did the signer of this transaction add the inital liquidity to the pool
        self.signer = signer
        self.pool_spl_before = pool_spl_before
        self.pool_spl_after = pool_spl_after
        self.pool_wsol_before = pool_wsol_before
        self.pool_wsol_after = pool_wsol_after
        self.signer_spl_before = signer_spl_before
        self.signer_spl_after = signer_spl_after
        self.signer_sol_before = signer_sol_before
        self.signer_sol_after = signer_sol_after
        
    def __str__(self):
        return (
            f"MeteoraPoolsTransaction(\n"
            f"  tx_sig: {self.tx_sig},\n"
            f"  block_time: {self.block_time},\n"
            f"  slot: {self.slot},\n"
            f"  fee: {self.fee},\n"
            f"  token_price: {self.token_price},\n"
            f"  token_address: {self.token_address},\n"
            f"  is_creator: {self.is_creator},\n"
            f"  signer: {self.signer},\n"
            f"  pool_spl_before: {self.pool_spl_before},\n"
            f"  pool_spl_after: {self.pool_spl_after},\n"
            f"  pool_wsol_before: {self.pool_wsol_before},\n"
            f"  pool_wsol_after: {self.pool_wsol_after},\n"
            f"  signer_spl_before: {self.signer_spl_before},\n"
            f"  signer_spl_after: {self.signer_spl_after},\n"
            f"  signer_sol_before: {self.signer_sol_before},\n"
            f"  signer_sol_after: {self.signer_sol_after},\n"
            f")"
        )
