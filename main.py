import sys
import os
from loguru import logger

import config
from exchange import ExchangeHandler

def setup_logging():
    """Configure logging settings"""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    logger.remove()  # Remove default handler
    logger.add("logs/exchange_tester_{time}.log", rotation="500 MB", level=config.LOG_LEVEL)
    logger.add(lambda msg: print(msg), level=config.LOG_LEVEL)  # Also print to console

def select_exchange():
    """Interactive function to select exchange"""
    print("\n=== Available Exchanges ===")
    
    for i, exchange in enumerate(config.SUPPORTED_EXCHANGES, 1):
        print(f"{i}. {exchange.upper()}")
    
    while True:
        choice = input("\nSelect exchange (1-7): ")
        try:
            index = int(choice) - 1
            if 0 <= index < len(config.SUPPORTED_EXCHANGES):
                selected = config.SUPPORTED_EXCHANGES[index]
                print(f"\nSelected exchange: {selected.upper()}")
                return selected
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a number.")

def select_action():
    """Interactive function to select action"""
    print("\n=== Available Actions ===")
    print("1. Buy token")
    print("2. Sell token")
    print("3. Check balance")
    print("4. Check token price")
    
    while True:
        choice = input("\nSelect action (1-4): ")
        if choice == '1':
            return 'buy'
        elif choice == '2':
            return 'sell'
        elif choice == '3':
            return 'balance'
        elif choice == '4':
            return 'price'
        else:
            print("Invalid selection. Please try again.")

def get_token_symbol():
    """Get token symbol from user"""
    while True:
        symbol = input("\nEnter token symbol (e.g., BTC): ").strip()
        if symbol:
            return symbol
        print("Symbol cannot be empty. Please try again.")

def get_amount(action, currency):
    """Get amount for buy/sell"""
    while True:
        if action == 'buy':
            prompt = f"\nEnter amount to spend in {currency}: "
        else:  # sell
            prompt = f"\nEnter amount to sell in {currency} (or press Enter to sell by percentage): "
        
        amount_input = input(prompt).strip()
        
        # For sell, empty input means use percentage
        if action == 'sell' and not amount_input:
            return get_percentage()
        
        try:
            amount = float(amount_input)
            if amount <= 0:
                print("Amount must be greater than zero.")
                continue
            return amount
        except ValueError:
            print("Please enter a valid number.")

def get_percentage():
    """Get percentage for sell"""
    while True:
        percentage_input = input("\nEnter percentage of holdings to sell (1-100): ").strip()
        try:
            percentage = float(percentage_input)
            if 0 < percentage <= 100:
                return None, percentage  # Return (None, percentage) for sell by percentage
            else:
                print("Percentage must be between 1 and 100.")
        except ValueError:
            print("Please enter a valid number.")

def ask_continue():
    """Ask if user wants to continue with another operation"""
    while True:
        choice = input("\nDo you want to continue with another operation? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            return True
        elif choice in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'")

def perform_operation():
    """Perform a single operation (buy, sell, check balance, check price)"""
    try:
        # Step 1: Select exchange
        exchange_id = select_exchange()
        
        # Step 2: Initialize exchange handler
        exchange_handler = ExchangeHandler(exchange_id, sandbox=False)
        
        # Step 3: Select action
        action = select_action()
        
        if action in ['buy', 'sell', 'price']:
            # Step 2: Get token symbol
            base_symbol = get_token_symbol()
            
            # Format symbol with USDT
            symbol = f"{base_symbol.upper()}/{config.QUOTE_CURRENCY}"
            
            # Check if symbol exists
            exists, formatted_symbol = exchange_handler.check_pair_exists(symbol)
            if not exists:
                print(f"Trading pair {symbol} not found on {exchange_handler.exchange_id.upper()}. Please check the symbol and try again.")
                return
            
            symbol = formatted_symbol
            
            if action == 'buy':
                # Step 3a: For buy, get amount in USDT
                amount = get_amount('buy', config.QUOTE_CURRENCY)
                
                # Execute buy
                print(f"\nExecuting buy: {amount} {config.QUOTE_CURRENCY} of {symbol}...")
                result = exchange_handler.buy_token(symbol, amount)
                
                if result:
                    print("\n=== Buy Executed Successfully ===")
                    print(f"Order ID: {result['id']}")
                    print(f"Amount: {result['amount']} {symbol.split('/')[0]}")
                    print(f"Price: approx. {result['price']} {symbol.split('/')[1]}")
                    print(f"Total cost: {result['cost']} {symbol.split('/')[1]}")
                else:
                    print("\nBuy operation failed. Check the logs for details.")
            
            elif action == 'sell':
                # Step 3b: For sell, get amount in base currency or percentage
                base_currency = symbol.split('/')[0]  # e.g., BTC in BTC/USDT
                
                # Get current balance first
                free_balance, total_balance = exchange_handler.get_balance(base_currency)
                if free_balance <= 0:
                    print(f"You don't have any {base_currency} to sell.")
                    return
                
                print(f"\nAvailable balance: {free_balance} {base_currency}")
                
                # Get amount or percentage
                amount_input = get_amount('sell', base_currency)
                
                # Check if it's (None, percentage) for percentage-based sell
                if isinstance(amount_input, tuple):
                    amount, percentage = amount_input
                    sell_amount = None  # Signal to use percentage
                else:
                    amount = amount_input
                    percentage = 100  # Default if specific amount
                    sell_amount = amount
                
                # Execute sell
                if sell_amount:
                    print(f"\nExecuting sell: {sell_amount} {base_currency}...")
                else:
                    print(f"\nExecuting sell: {percentage}% of {base_currency} holdings...")
                
                result = exchange_handler.sell_token(symbol, sell_amount, percentage)
                
                if result:
                    print("\n=== Sell Executed Successfully ===")
                    print(f"Order ID: {result['id']}")
                    print(f"Amount sold: {result['amount']} {symbol.split('/')[0]}")
                    print(f"Price: approx. {result['price']} {symbol.split('/')[1]}")
                    print(f"Total value: {result['cost']} {symbol.split('/')[1]}")
                else:
                    print("\nSell operation failed. Check the logs for details.")
            
            elif action == 'price':
                # Get and display price info
                ticker = exchange_handler.get_ticker(symbol)
                if ticker:
                    print(f"\n=== Price Information for {symbol} ===")
                    print(f"Last price: {ticker['last']} {config.QUOTE_CURRENCY}")
                    print(f"Bid: {ticker.get('bid', 'N/A')} {config.QUOTE_CURRENCY}")
                    print(f"Ask: {ticker.get('ask', 'N/A')} {config.QUOTE_CURRENCY}")
                    print(f"24h high: {ticker.get('high', 'N/A')} {config.QUOTE_CURRENCY}")
                    print(f"24h low: {ticker.get('low', 'N/A')} {config.QUOTE_CURRENCY}")
                    print(f"24h volume: {ticker.get('volume', 'N/A')} {symbol.split('/')[0]}")
                else:
                    print(f"\nFailed to get price information for {symbol}.")
        
        elif action == 'balance':
            # Get and display balances
            balances = exchange_handler.get_balance()
            
            if balances:
                print("\n=== Available Balances ===")
                # First show USDT balance if available
                if config.QUOTE_CURRENCY in balances:
                    usdt_balance = balances[config.QUOTE_CURRENCY]
                    print(f"{config.QUOTE_CURRENCY}: {usdt_balance['free']} (Total: {usdt_balance['total']})")
                    
                # Then show other balances
                for currency, amounts in balances.items():
                    if currency != config.QUOTE_CURRENCY:
                        print(f"{currency}: {amounts['free']} (Total: {amounts['total']})")
            else:
                print("\nNo balances found or error retrieving balances.")
    
    except Exception as e:
        logger.error(f"Error during operation: {e}")
        print(f"\nAn error occurred: {e}")

def main():
    # Setup logging
    setup_logging()
    
    print("\n==================================")
    print("=== Cryptocurrency Exchange Tester ===")
    print("==================================")
    
    try:
        # Main program loop
        while True:
            # Perform one operation (includes exchange selection)
            perform_operation()
            
            # Ask if user wants to continue
            if not ask_continue():
                break
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\nAn error occurred: {e}")
    
    finally:
        print("\nDone. Thank you for using the Cryptocurrency Exchange Tester!")

if __name__ == "__main__":
    main()