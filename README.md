# Cryptocurrency Exchange Tester

A command-line tool for interacting with various cryptocurrency exchanges, supporting market operations, balance checking, deposits, and withdrawals.

## Supported Exchanges

- MEXC
- KuCoin
- HTX (formerly Huobi)
- Gate.io
- BitMart
- Bitget
- Bybit

## Features

- Buy/sell tokens with market orders
- Check account balances
- Check token prices
- Get deposit addresses
- Withdraw funds
- Check deposit/withdrawal history
- **NEW**: Deposit USDT directly from your wallet to exchanges

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your API keys for the exchanges you want to use

## Usage

Run the tool with:

```
python main.py
```

Follow the interactive prompts to:
1. Select an exchange
2. Choose an action
3. Provide necessary details for the selected action

## Deposit and Withdrawal Functionality

### Deposit

The tool supports direct deposits of BEP20 USDT from your wallet to your exchange account:

1. Set up your wallet details in the `.env` file:
   ```
   WALLET_PRIVATE_KEY=0x1234...  # Your wallet's private key
   DEPOSIT_AMOUNT=10.5           # Amount to deposit in USDT
   ```
2. Select "Deposit USDT to exchange" from the actions menu
3. The tool will fetch your deposit address from the selected exchange
4. Review the deposit details (using private key and amount from .env file)
5. Confirm the transaction

### Withdrawal

The tool supports automated withdrawals of BEP20 USDT from your exchange account to a designated address:

1. Set up withdrawal details in the `.env` file:
   ```
   DEPOSIT_AMOUNT=10.5           # Amount to withdraw in USDT (uses same amount as deposit)
   WITHDRAWAL_ADDRESS=0x5678...  # Destination address for withdrawals
   ```
2. Select "Withdraw funds" from the actions menu
3. The tool will automatically withdraw the configured amount to the configured address

**Important Notes for Direct Deposits:**
- Only BEP20 USDT is supported for direct deposits
- You need BNB in your wallet for gas fees (at least 0.005 BNB recommended)
- Private keys are sensitive information - use this feature in a secure environment
- Always double-check the deposit address and amount before confirming

## Security Considerations

- API keys should have withdrawal permissions only if you plan to use the withdrawal feature
- Your private key is stored in the `.env` file - make sure this file is secured properly:
  - Keep the `.env` file out of version control
  - Set appropriate file permissions (readable only by you)
  - Consider storing a limited amount in the wallet used for testing
- Consider using a dedicated wallet with limited funds for testing

## License

MIT