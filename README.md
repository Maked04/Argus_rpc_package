This git repo contains a package for extracting data from the Solana Blockchain.

Main entry points

gRPClient / AccountsTxStream

Used to subscribe to accounts etc to receive updates on changes

i.e AccountsTxStream is used to get updates when a listed account participates in a transaction e.ge Subscribe to the Raydium V4 program account to get all raydium v4 transactions

RPClient

Used to make regular json rpc calls

Utils

Seperate utils foor RPC and gRPC used to parse and decode the data received from respective rpc, the 2 main types are RaydiumV4Transaction and PumpFunTransaction which store transaction data like: Token price, balances, fees, signer etc
