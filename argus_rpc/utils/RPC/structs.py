from construct import Struct, Int64ul, Bytes, Array, Int8ub

# Define the structure of LIQUIDITY_STATE_LAYOUT_V4
LIQUIDITY_STATE_LAYOUT_V4 = Struct(
    "status" / Int64ul,
    "nonce" / Int64ul,
    "maxOrder" / Int64ul,
    "depth" / Int64ul,
    "baseDecimal" / Int64ul,
    "quoteDecimal" / Int64ul,
    "state" / Int64ul,
    "resetFlag" / Int64ul,
    "minSize" / Int64ul,
    "volMaxCutRatio" / Int64ul,
    "amountWaveRatio" / Int64ul,
    "baseLotSize" / Int64ul,
    "quoteLotSize" / Int64ul,
    "minPriceMultiplier" / Int64ul,
    "maxPriceMultiplier" / Int64ul,
    "systemDecimalValue" / Int64ul,
    "minSeparateNumerator" / Int64ul,
    "minSeparateDenominator" / Int64ul,
    "tradeFeeNumerator" / Int64ul,
    "tradeFeeDenominator" / Int64ul,
    "pnlNumerator" / Int64ul,
    "pnlDenominator" / Int64ul,
    "swapFeeNumerator" / Int64ul,
    "swapFeeDenominator" / Int64ul,
    "baseNeedTakePnl" / Int64ul,
    "quoteNeedTakePnl" / Int64ul,
    "quoteTotalPnl" / Int64ul,
    "baseTotalPnl" / Int64ul,
    "poolOpenTime" / Int64ul,
    "punishPcAmount" / Int64ul,
    "punishCoinAmount" / Int64ul,
    "orderbookToInitTime" / Int64ul,
    "swapBaseInAmount" / Bytes(16),  # 128-bit as 16 bytes
    "swapQuoteOutAmount" / Bytes(16),  # 128-bit as 16 bytes
    "swapBase2QuoteFee" / Int64ul,
    "swapQuoteInAmount" / Bytes(16),  # 128-bit as 16 bytes
    "swapBaseOutAmount" / Bytes(16),  # 128-bit as 16 bytes
    "swapQuote2BaseFee" / Int64ul,
    "baseVault" / Bytes(32),  # Assuming public key is 32 bytes
    "quoteVault" / Bytes(32),
    "baseMint" / Bytes(32),
    "quoteMint" / Bytes(32),
    "lpMint" / Bytes(32),
    "openOrders" / Bytes(32),
    "marketId" / Bytes(32),
    "marketProgramId" / Bytes(32),
    "targetOrders" / Bytes(32),
    "withdrawQueue" / Bytes(32),
    "lpVault" / Bytes(32),
    "owner" / Bytes(32),
    "lpReserve" / Int64ul,
    "padding" / Array(3, Int64ul)
)


# Define the LaunchpadVestingSchedule structure
LAUNCHPAD_VESTING_SCHEDULE_LAYOUT = Struct(
    "totalLockedAmount" / Int64ul,
    "cliffPeriod" / Int64ul,
    "unlockPeriod" / Int64ul,
    "startTime" / Int64ul,
    "totalAllocatedShare" / Int64ul
)

# Define the LaunchpadPool structure
LAUNCHPAD_POOL_LAYOUT = Struct(
    "_reserved_0" / Int64ul,
    "epoch" / Int64ul,
    "bump" / Int8ub,
    "status" / Int8ub,
    "mintDecimalsA" / Int8ub,
    "mintDecimalsB" / Int8ub,
    "migrateType" / Int8ub,
    "supply" / Int64ul,
    "totalSellA" / Int64ul,
    "virtualA" / Int64ul,
    "virtualB" / Int64ul,
    "realA" / Int64ul,
    "realB" / Int64ul,
    "totalFundRaisingB" / Int64ul,
    "protocolFee" / Int64ul,
    "platformFee" / Int64ul,
    "migrateFee" / Int64ul,
    "vestingSchedule" / LAUNCHPAD_VESTING_SCHEDULE_LAYOUT,  # Embedded struct
    "configId" / Bytes(32),  # publicKey
    "platformId" / Bytes(32),  # publicKey
    "mintA" / Bytes(32),  # publicKey
    "mintB" / Bytes(32),  # publicKey
    "vaultA" / Bytes(32),  # publicKey
    "vaultB" / Bytes(32),  # publicKey
    "creator" / Bytes(32),  # publicKey
    "_reserved" / Array(8, Int64ul))