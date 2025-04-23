import sys
import os
from loguru import logger

import config
from exchange import ExchangeHandler
from blockchain import BlockchainHandler

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
    print("5. Get deposit address")
    print("6. Withdraw funds")
    print("7. Check deposit history")
    print("8. Check withdrawal history")
    print("9. Deposit USDT to exchange")
    
    while True:
        choice = input("\nSelect action (1-9): ")
        if choice == '1':
            return 'buy'
        elif choice == '2':
            return 'sell'
        elif choice == '3':
            return 'balance'
        elif choice == '4':
            return 'price'
        elif choice == '5':
            return 'deposit'
        elif choice == '6':
            return 'withdraw'
        elif choice == '7':
            return 'deposit_history'
        elif choice == '8':
            return 'withdrawal_history'
        elif choice == '9':
            return 'deposit_crypto'
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
    """Perform a single operation (buy, sell, check balance, check price, deposit, withdraw)"""
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
                
        elif action == 'deposit':
            # Get and display deposit address for USDT on BEP20 network only
            currency = 'USDT'
            network = 'BEP20'
            
            # Get deposit address
            print(f"\nGetting BEP20 deposit address for USDT...")
            address_info = exchange_handler.get_deposit_address(currency, network)
            
            if address_info and 'address' in address_info:
                print("\n=== Deposit Address ===")
                print(f"Currency: {currency}")
                print(f"Network: {address_info.get('network', network)}")
                print(f"Address: {address_info['address']}")
                
                # Display tag/memo if available
                if 'tag' in address_info and address_info['tag']:
                    print(f"Tag/Memo: {address_info['tag']}")
                    print("\nIMPORTANT: You must include both the address AND tag when depositing!")
                
                print("\nIMPORTANT: Make sure to send only via the correct network!")
            else:
                print(f"\nFailed to get deposit address. Check the logs for details.")
        
        elif action == 'withdraw':
            # Withdraw USDT via BEP20 network to an external address
            currency = 'USDT'
            network = 'BEP20'
            
            # Check available balance
            free_balance, total_balance = exchange_handler.get_balance(currency)
            if free_balance <= 0:
                print(f"You don't have any USDT to withdraw.")
                return
            
            print(f"\nAvailable balance: {free_balance} USDT")
            
            # Get withdrawal amount
            while True:
                try:
                    amount_input = input(f"Enter amount to withdraw (max {free_balance} USDT): ").strip()
                    amount = float(amount_input)
                    if amount <= 0:
                        print("Amount must be greater than zero.")
                        continue
                    if amount > free_balance:
                        print(f"Amount exceeds available balance of {free_balance} USDT.")
                        continue
                    break
                except ValueError:
                    print("Please enter a valid number.")
            
            # Get destination address
            address = input("Enter BEP20 destination address for USDT: ").strip()
            if not address:
                print("Address cannot be empty.")
                return
            
            # Ask if a tag/memo is required
            tag_required = input("Does this withdrawal require a tag/memo? (y/n): ").strip().lower()
            tag = None
            if tag_required in ['y', 'yes']:
                tag = input("Enter tag/memo: ").strip()
            
            # Confirm withdrawal
            print(f"\n=== Withdrawal Details ===")
            print(f"Currency: USDT")
            print(f"Amount: {amount}")
            print(f"Network: BEP20")
            print(f"Address: {address}")
            if tag:
                print(f"Tag/Memo: {tag}")
                
            confirm = input("\nConfirm withdrawal? (y/n): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("Withdrawal cancelled.")
                return
            
            # Execute withdrawal
            print(f"\nInitiating withdrawal of {amount} {currency} to {address} via {network}...")
            result = exchange_handler.withdraw(currency, amount, address, tag, network)
            
            if result:
                print("\n=== Withdrawal Initiated Successfully ===")
                print(f"Transaction ID: {result.get('id', 'N/A')}")
                print(f"Status: {result.get('status', 'Processing')}")
                print("\nIMPORTANT: Check the exchange's withdrawal history to track the status.")
            else:
                print("\nWithdrawal failed. Check the logs for details.")
        
        elif action == 'deposit_history':
            # View deposit history for USDT only
            currency = 'USDT'
            
            # Get deposit history
            print("\nFetching recent USDT deposits...")
            deposits = exchange_handler.fetch_deposits(currency)
            
            if deposits:
                print(f"\n=== Recent {currency} Deposits ===")
                for i, deposit in enumerate(deposits, 1):
                    print(f"\nDeposit #{i}:")
                    print(f"Transaction ID: {deposit.get('id', 'N/A')}")
                    print(f"Amount: {deposit.get('amount', 'N/A')} {deposit.get('currency', currency)}")
                    print(f"Status: {deposit.get('status', 'N/A')}")
                    print(f"Date: {deposit.get('datetime', 'N/A')}")
                    print(f"Network: {deposit.get('network', 'N/A')}")
                    print(f"Address: {deposit.get('address', 'N/A')}")
                    if 'tag' in deposit and deposit['tag']:
                        print(f"Tag/Memo: {deposit['tag']}")
            elif deposits == []:
                print(f"\nNo recent {currency} deposits found.")
            else:
                print(f"\nFailed to fetch deposit history. Check the logs for details.")
        
        elif action == 'withdrawal_history':
            # View withdrawal history for USDT only
            currency = 'USDT'
            
            # Get withdrawal history
            print("\nFetching recent USDT withdrawals...")
            withdrawals = exchange_handler.fetch_withdrawals(currency)
            
            if withdrawals:
                print(f"\n=== Recent {currency} Withdrawals ===")
                for i, withdrawal in enumerate(withdrawals, 1):
                    print(f"\nWithdrawal #{i}:")
                    print(f"Transaction ID: {withdrawal.get('id', 'N/A')}")
                    print(f"Amount: {withdrawal.get('amount', 'N/A')} {withdrawal.get('currency', currency)}")
                    print(f"Status: {withdrawal.get('status', 'N/A')}")
                    print(f"Date: {withdrawal.get('datetime', 'N/A')}")
                    print(f"Network: {withdrawal.get('network', 'N/A')}")
                    print(f"Address: {withdrawal.get('address', 'N/A')}")
                    if 'tag' in withdrawal and withdrawal['tag']:
                        print(f"Tag/Memo: {withdrawal['tag']}")
                    print(f"Fee: {withdrawal.get('fee', {}).get('cost', 'N/A')} {withdrawal.get('fee', {}).get('currency', '')}")
            elif withdrawals == []:
                print(f"\nNo recent {currency} withdrawals found.")
            else:
                print(f"\nFailed to fetch withdrawal history. Check the logs for details.")
                
        elif action == 'deposit_crypto':
            # Initialize blockchain handler
            blockchain_handler = BlockchainHandler()
            
            if not blockchain_handler.connected:
                print("\nFailed to connect to Binance Smart Chain. Check your internet connection.")
                return
                
            # Get deposit address from exchange
            currency = 'USDT'
            network = 'BEP20'
            
            print(f"\nGetting BEP20 deposit address for USDT...")
            address_info = exchange_handler.get_deposit_address(currency, network)
            
            if not address_info or 'address' not in address_info:
                print(f"\nFailed to get deposit address. Check the logs for details.")
                return
                
            deposit_address = address_info['address']
            
            # Display tag/memo if available
            tag = None
            if 'tag' in address_info and address_info['tag']:
                tag = address_info['tag']
                print(f"\nDeposit address has a tag/memo: {tag}")
                print("Both address AND tag are required for this deposit!")
            
            # Display deposit address
            print("\n=== Deposit Information ===")
            print(f"Exchange: {exchange_handler.exchange_id.upper()}")
            print(f"Currency: {currency}")
            print(f"Network: {network}")
            print(f"Address: {deposit_address}")
            if tag:
                print(f"Tag/Memo: {tag}")
            
            # Get private key from config
            private_key = config.WALLET_PRIVATE_KEY
            
            if not private_key:
                print("\nNo wallet private key found in .env file.")
                print("Please add your WALLET_PRIVATE_KEY to the .env file and try again.")
                return
            
            # Validate private key
            is_valid, sender_address = blockchain_handler.validate_private_key(private_key)
            
            if not is_valid:
                print("\nInvalid private key format in .env file. Please check and try again.")
                return
                
            print(f"\nWallet address: {sender_address}")
            
            # Get USDT balance
            usdt_balance = blockchain_handler.get_usdt_balance(sender_address)
            
            if usdt_balance <= 0:
                print(f"\nNo USDT balance found in wallet {sender_address}")
                return
                
            print(f"Available USDT balance: {usdt_balance}")
            
            # Get amount from config
            amount = config.DEPOSIT_AMOUNT
            
            if amount <= 0:
                print("\nInvalid deposit amount in .env file. Amount must be greater than zero.")
                return
            
            if amount > usdt_balance:
                print(f"\nDeposit amount in .env file ({amount} USDT) exceeds available balance ({usdt_balance} USDT).")
                return
            
            # Confirm deposit
            print(f"\n=== Deposit Confirmation ===")
            print(f"You are about to deposit {amount} USDT to {exchange_handler.exchange_id.upper()}")
            print(f"From wallet: {sender_address}")
            print(f"To address: {deposit_address}")
            if tag:
                print(f"With tag/memo: {tag}")
            
            confirm = input("\nConfirm deposit? (y/n): ").strip().lower()
            
            if confirm not in ['y', 'yes']:
                print("Deposit cancelled.")
                return
            
            # Execute deposit
            print(f"\nInitiating deposit of {amount} USDT to {exchange_handler.exchange_id.upper()}...")
            
            tx_hash = blockchain_handler.transfer_usdt(private_key, deposit_address, amount)
            
            if tx_hash:
                print("\n=== Deposit Initiated Successfully ===")
                print(f"Transaction hash: {tx_hash}")
                print(f"Amount: {amount} USDT")
                print("\nIMPORTANT: It may take some time for the deposit to be credited to your exchange account.")
                print(f"You can check the transaction status at https://bscscan.com/tx/{tx_hash}")
                print("You can also check your deposit history on the exchange once it's processed.")
            else:
                print("\nDeposit failed. Check the logs for details.")
    
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