class PumpFunTransaction:
    def __init__(self, tx_sig, block_time, slot, fee, token_price, token_address, is_creator, signer, bc_spl_before, bc_spl_after, bc_sol_before, bc_sol_after, 
                 signer_spl_before, signer_spl_after, signer_sol_before, signer_sol_after):
        self.tx_sig = tx_sig
        self.block_time = block_time
        self.slot = slot
        self.fee = fee
        self.token_price = token_price
        self.token_address = token_address
        self.is_creator = is_creator
        self.signer = signer
        self.bc_spl_before = bc_spl_before
        self.bc_spl_after = bc_spl_after
        self.bc_sol_before = bc_sol_before
        self.bc_sol_after = bc_sol_after
        self.signer_spl_before = signer_spl_before
        self.signer_spl_after = signer_spl_after
        self.signer_sol_before = signer_sol_before
        self.signer_sol_after = signer_sol_after
        
    def __str__(self):
        return (
            f"PumpFunTransaction(\n"
            f"  tx_sig: {self.tx_sig},\n"
            f"  block_time: {self.block_time},\n"
            f"  slot: {self.slot},\n"
            f"  fee: {self.fee},\n"
            f"  token_price: {self.token_price},\n"
            f"  token_address: {self.token_address},\n"
            f"  is_creator: {self.is_creator},\n"
            f"  signer: {self.signer},\n"
            f"  bc_spl_before: {self.bc_spl_before},\n"
            f"  bc_spl_after: {self.bc_spl_after},\n"
            f"  bc_sol_before: {self.bc_sol_before},\n"
            f"  bc_sol_after: {self.bc_sol_after},\n"
            f"  signer_spl_before: {self.signer_spl_before},\n"
            f"  signer_spl_after: {self.signer_spl_after},\n"
            f"  signer_sol_before: {self.signer_sol_before},\n"
            f"  signer_sol_after: {self.signer_sol_after}\n"
            f")"
        )

class RaydiumV4Transaction:
    def __init__(self, tx_sig, block_time, slot, fee, token_price, token_address, is_creator, signer, pool_spl_before, pool_spl_after, pool_wsol_before, pool_wsol_after, 
                 signer_spl_before, signer_spl_after, signer_sol_change):
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
        self.signer_sol_change = signer_sol_change  # This includes sol and wsol used in transaction
        
    def __str__(self):
        return (
            f"Raydiumv4Transaction(\n"
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
            f"  signer_sol_change: {self.signer_sol_change},\n"
            f")"
        )
    
class RaydiumCPMMTransaction:
    def __init__(self, tx_sig, block_time, slot, fee, token_price, token_address, is_creator, signer, pool_spl_before, pool_spl_after, pool_wsol_before, pool_wsol_after, 
                 signer_spl_before, signer_spl_after, signer_sol_change):
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
        self.signer_sol_change = signer_sol_change  # This includes sol and wsol used in transaction
        
    def __str__(self):
        return (
            f"RaydiumCPMMTransaction(\n"
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
            f"  signer_sol_change: {self.signer_sol_change},\n"
            f")"
        )
    
class PumpSwapTransaction:
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
            f"PumpSwapTransaction(\n"
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
    

class RaydiumLaunchPadTransaction:
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
            f"RaydiumLaunchPadTransaction(\n"
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
    
class MeteoraDBCTransaction:
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
            f"MeteoraDBCTransaction(\n"
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