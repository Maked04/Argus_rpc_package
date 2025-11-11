from solders.pubkey import Pubkey
from typing import Tuple

LAUNCHPAD_POOL_SEED = b"pool"
LAUNCPAD_PROGRAM_ACCOUNT = Pubkey.from_string("LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj")

BONDING_CURVE_SEED = b"bonding-curve"
PUMPFUN_PROGRAM_ACCOUNT = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")


def get_program_address(program_id: Pubkey, seeds: list) -> Tuple[Pubkey, int]:
    pda, bump = Pubkey.find_program_address(
        seeds=seeds,
        program_id=program_id
    )
    
    return pda, bump


def get_raydium_launch_pad_pool_address(mint_a: str, mint_b: str) -> str:
    mint_a = mint_a.strip()
    mint_b = mint_b.strip()
    
    pda, bump = get_program_address(
        LAUNCPAD_PROGRAM_ACCOUNT,
        seeds = [
            LAUNCHPAD_POOL_SEED,
            bytes(Pubkey.from_string(mint_a)),
            bytes(Pubkey.from_string(mint_b))
        ]
    )

    return str(pda)


def get_pump_fun_bonding_curve_address(token_address: str) -> str:
    token_address = token_address.strip()
    pda, bump = get_program_address(
        PUMPFUN_PROGRAM_ACCOUNT, 
        seeds = [
            BONDING_CURVE_SEED, 
            bytes(Pubkey.from_string(token_address))
        ]
    )

    return str(pda)