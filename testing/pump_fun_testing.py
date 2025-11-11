from solders.pubkey import Pubkey

from argus_rpc.utils.RPC.pda import get_program_address, get_pump_fun_bonding_curve_address


BONDING_CURVE_SEED = b"bonding-curve"
PUMPFUN_PROGRAM_ACCOUNT = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")

def derive_bonding_curve_account(token_address):
    '''
    getBondingCurvePDA(mint: PublicKey) {
    return PublicKey.findProgramAddressSync(
      [Buffer.from(BONDING_CURVE_SEED), mint.toBuffer()],
      this.program.programId
    )[0];
  }
    '''
    return get_program_address(PUMPFUN_PROGRAM_ACCOUNT, [BONDING_CURVE_SEED, bytes(Pubkey.from_string(token_address))])


def main():
    print(derive_bonding_curve_account("GrfWEooFz5zHwhg9kdKD3kNDY9HUA4Wn7NYs7mKCpump"))
    print(get_pump_fun_bonding_curve_address("GrfWEooFz5zHwhg9kdKD3kNDY9HUA4Wn7NYs7mKCpump"))

if __name__ == "__main__":
    main()