# Python Exchange Tester

A simple interactive cryptocurrency exchange trading tool that allows you to test buying and selling tokens on various exchanges using USDT pairs.

## Supported Exchanges

- MEXC
- KuCoin
- HTX (formerly Huobi)
- Gate.io
- BitMart
- Bitget
- Bybit

## Features

- Buy tokens with USDT
- Sell tokens for USDT (specific amount or percentage of holdings)
- Check account balances
- Check token prices
- Interactive step-by-step process for all operations

## Setup

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your API keys (copy from `.env.example`):
   ```
   cp .env.example .env
   ```

3. Edit the `.env` file to add your API keys for the exchanges you want to use.

## Usage

Run the program:
```
python main.py
```

The program will guide you through the following steps:

1. Select an exchange to use
2. Choose an action (buy, sell, check balance, or check price)
3. Enter a token symbol (if needed)
4. Specify amount to buy/sell (if needed)

## Notes

- All operations use live trading mode by default (be careful with API keys that have trading permissions)
- The program only supports USDT trading pairs
- Logs are saved in the `logs` directory