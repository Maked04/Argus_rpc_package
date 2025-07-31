from solders.pubkey import Pubkey
from typing import Tuple

LAUNCHPAD_POOL_SEED = b"pool"
LAUNCPAD_PROGRAM_ACCOUNT = Pubkey.from_string("LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj")


def get_program_address(program_id: Pubkey, seeds: list) -> Tuple[Pubkey, int]:
    pda, bump = Pubkey.find_program_address(
        seeds=seeds,
        program_id=program_id
    )
    
    return pda, bump


def get_raydium_launch_pad_pool_address(mint_a: str, mint_b: str) -> str:
    pda, bump = get_program_address(
        LAUNCPAD_PROGRAM_ACCOUNT,
        seeds = [
            LAUNCHPAD_POOL_SEED,
            bytes(Pubkey.from_string(mint_a)),
            bytes(Pubkey.from_string(mint_b))
        ]
    )

    return str(pda)