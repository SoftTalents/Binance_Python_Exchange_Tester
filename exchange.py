import ccxt
from loguru import logger
import config

class ExchangeHandler:
    def __init__(self, exchange_id, sandbox=False):
        """Initialize exchange connection with API keys from config"""
        
        # Validate exchange is supported
        exchange_id = exchange_id.lower()
        if exchange_id not in config.SUPPORTED_EXCHANGES:
            supported = ", ".join(config.SUPPORTED_EXCHANGES)
            logger.error(f"Exchange {exchange_id} is not supported. Supported exchanges: {supported}")
            raise ValueError(f"Unsupported exchange: {exchange_id}")
        
        # Initialize with appropriate credentials for each exchange
        exchange_options = {
            'enableRateLimit': True
        }
        
        if exchange_id == 'mexc':
            exchange_options.update({
                'apiKey': config.MEXC_API_KEY,
                'secret': config.MEXC_API_SECRET,
            })
            exchange_class = ccxt.mexc
            
        elif exchange_id == 'kucoin':
            exchange_options.update({
                'apiKey': config.KUCOIN_API_KEY,
                'secret': config.KUCOIN_API_SECRET,
                'password': config.KUCOIN_API_PASSPHRASE
            })
            exchange_class = ccxt.kucoin
            
        elif exchange_id == 'htx':
            exchange_options.update({
                'apiKey': config.HTX_API_KEY,
                'secret': config.HTX_API_SECRET,
            })
            exchange_class = ccxt.htx
            
        elif exchange_id == 'gateio':
            exchange_options.update({
                'apiKey': config.GATE_API_KEY,
                'secret': config.GATE_API_SECRET,
            })
            exchange_class = ccxt.gateio
            
        elif exchange_id == 'bitmart':
            exchange_options.update({
                'apiKey': config.BITMART_API_KEY,
                'secret': config.BITMART_API_SECRET,
                'uid': config.BITMART_MEMO
            })
            exchange_class = ccxt.bitmart
            
        elif exchange_id == 'bitget':
            exchange_options.update({
                'apiKey': config.BITGET_API_KEY,
                'secret': config.BITGET_API_SECRET,
                'password': config.BITGET_API_PASSPHRASE
            })
            exchange_class = ccxt.bitget
            
        elif exchange_id == 'bybit':
            exchange_options.update({
                'apiKey': config.BYBIT_API_KEY,
                'secret': config.BYBIT_API_SECRET,
            })
            exchange_class = ccxt.bybit
        
        # Create exchange instance
        self.exchange = exchange_class(exchange_options)
        self.exchange_id = exchange_id
        
        # Use sandbox/testnet if specifically requested
        if sandbox and hasattr(self.exchange, 'set_sandbox_mode'):
            self.exchange.set_sandbox_mode(True)
            logger.info(f"Using {exchange_id} sandbox/testnet mode")
        else:
            logger.info(f"Using {exchange_id} live trading mode")
        
        # Load markets
        logger.info(f"Connecting to {exchange_id}...")
        self.exchange.load_markets()
        logger.info(f"Connected to {exchange_id} successfully")
        
    def check_pair_exists(self, symbol):
        """Check if trading pair exists on exchange and format it properly"""
        try:
            # Try to standardize the symbol format
            symbol = symbol.upper()
            
            # If no separator provided, add USDT as the quote currency
            if '/' not in symbol:
                symbol = f"{symbol}/{config.QUOTE_CURRENCY}"
            
            # Check if the symbol exists in markets
            if symbol not in self.exchange.markets:
                logger.error(f"Trading pair {symbol} not found on {self.exchange_id}")
                return False, None
            
            return True, symbol
            
        except Exception as e:
            logger.error(f"Error checking pair existence: {e}")
            return False, None
    
    def get_ticker(self, symbol):
        """Get current ticker data for symbol"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            logger.info(f"Current price for {symbol}: {ticker['last']}")
            return ticker
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None
    
    def get_balance(self, currency=None):
        """
        Get balance for specified currency or all currencies with non-zero balance
        
        Args:
            currency: Specific currency to check, or None for all balances
            
        Returns:
            For specific currency: (free_balance, total_balance)
            For all currencies: Dictionary of non-zero balances
        """
        try:
            balances = self.exchange.fetch_balance()
            
            if currency:
                # Get specific currency balance
                currency = currency.split('/')[0] if '/' in currency else currency
                currency = currency.upper()
                
                if currency in balances['free']:
                    free_balance = balances['free'][currency]
                    total_balance = balances['total'][currency]
                    logger.info(f"{currency} balance - Free: {free_balance}, Total: {total_balance}")
                    return free_balance, total_balance
                else:
                    logger.warning(f"No balance found for {currency}")
                    return 0, 0
            else:
                # Return all non-zero balances
                non_zero = {}
                for curr, amount in balances['free'].items():
                    if amount > 0:
                        non_zero[curr] = {
                            'free': amount,
                            'total': balances['total'][curr]
                        }
                return non_zero
                
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            if currency:
                return 0, 0
            else:
                return {}
    
    def buy_token(self, symbol, amount):
        """
        Buy token at market price
        
        Args:
            symbol: Trading pair
            amount: Amount to buy in USDT
            
        Returns:
            Order information or None if failed
        """
        try:
            # Get current price
            ticker = self.get_ticker(symbol)
            if not ticker:
                return None
            
            current_price = ticker['last']
            logger.info(f"Buying {symbol} at ~{current_price}")
            
            # Calculate amount of base currency to buy
            base_currency = symbol.split('/')[0]
            quote_currency = symbol.split('/')[1]
            base_amount = amount / current_price
            
            # Check if we have enough balance
            free_balance, _ = self.get_balance(quote_currency)
            if free_balance < amount:
                logger.error(f"Insufficient balance: {free_balance} {quote_currency}, need {amount}")
                return None
            
            # Format according to exchange precision
            market = self.exchange.markets[symbol]
            if 'precision' in market and 'amount' in market['precision']:
                base_amount = self.exchange.amount_to_precision(symbol, base_amount)
            
            # Place order - handle special cases for exchanges like HTX that require price for market buy
            order = None
            
            if self.exchange_id == 'htx':
                # For HTX, pass createMarketBuyOrderRequiresPrice=False and use amount as cost
                order = self.exchange.create_market_buy_order(
                    symbol, 
                    amount,  # For HTX, pass the cost (USDT amount) directly
                    params={'createMarketBuyOrderRequiresPrice': False}
                )
            elif hasattr(self.exchange, 'options') and self.exchange.options.get('createMarketBuyOrderRequiresPrice', False):
                # For other exchanges that might require price parameter
                # Use the current price and calculate the base amount
                order = self.exchange.create_market_buy_order(
                    symbol,
                    float(base_amount),
                    params={'createMarketBuyOrderRequiresPrice': False, 'cost': amount}
                )
            else:
                # Standard market buy order
                order = self.exchange.create_market_buy_order(symbol, float(base_amount))
                
            logger.info(f"Buy order placed and executed: {order['id']}")
            
            # Get filled details
            if 'price' in order and order['price']:
                filled_price = order['price']
            else:
                # Some exchanges don't return price in the order response
                filled_price = current_price
                
            logger.info(f"Bought {base_amount} {base_currency} at approximately {filled_price} {quote_currency}")
            
            return {
                'id': order['id'],
                'symbol': symbol,
                'amount': float(base_amount),
                'price': filled_price,
                'cost': amount,
                'side': 'buy',
                'datetime': order.get('datetime', ''),
                'status': order.get('status', 'closed')
            }
            
        except Exception as e:
            logger.error(f"Error buying token: {e}")
            return None
    
    def sell_token(self, symbol, amount=None, percentage=100):
        """
        Sell token at market price
        
        Args:
            symbol: Trading pair
            amount: Amount to sell in base currency, if None sell percentage of holdings
            percentage: Percentage of holdings to sell if amount is None (1-100)
            
        Returns:
            Order information or None if failed
        """
        try:
            # Get current price
            ticker = self.get_ticker(symbol)
            if not ticker:
                return None
            
            current_price = ticker['last']
            base_currency = symbol.split('/')[0]
            
            # Get balance of base currency
            free_balance, _ = self.get_balance(base_currency)
            
            # Determine amount to sell
            if amount is None:
                amount = free_balance * (percentage / 100)
            
            if free_balance < amount:
                logger.error(f"Insufficient balance: {free_balance} {base_currency}, need {amount}")
                return None
            
            # Format according to exchange precision
            market = self.exchange.markets[symbol]
            if 'precision' in market and 'amount' in market['precision']:
                amount = self.exchange.amount_to_precision(symbol, amount)
            
            logger.info(f"Selling {amount} {base_currency} at ~{current_price}")
            
            # Place order
            order = self.exchange.create_market_sell_order(symbol, float(amount))
            logger.info(f"Sell order placed and executed: {order['id']}")
            
            # Get filled details
            if 'price' in order and order['price']:
                filled_price = order['price']
            else:
                # Some exchanges don't return price in the order response
                filled_price = current_price
                
            total_value = float(amount) * filled_price
            logger.info(f"Sold {amount} {base_currency} at approximately {filled_price}, total value: {total_value}")
            
            return {
                'id': order['id'],
                'symbol': symbol,
                'amount': float(amount),
                'price': filled_price,
                'cost': total_value,
                'side': 'sell',
                'datetime': order.get('datetime', ''),
                'status': order.get('status', 'closed')
            }
            
        except Exception as e:
            logger.error(f"Error selling token: {e}")
            return None
    
    def get_deposit_address(self, currency='USDT', network='BEP20', create_if_needed=True):
        """
        Get BEP20 deposit address for USDT
        
        Args:
            currency: Currency code (always USDT)
            network: Network/chain to use (always BEP20)
            create_if_needed: Create a new address if none exists
            
        Returns:
            Dictionary with address info or None if failed
        """
        try:
            # Force USDT and BEP20
            currency = 'USDT'
            network = 'BEP20'
            
            logger.info(f"Getting BEP20 deposit address for USDT on {self.exchange_id}")
            
            # Normalize network parameter for different exchanges
            network_param = 'BEP20'
            
            # Exchange-specific network parameter handling
            if self.exchange_id == 'kucoin':
                network_param = 'BSC' # KuCoin uses 'BSC' rather than 'BEP20 (BSC)'
            elif self.exchange_id in ['bitmart', 'mexc']:
                network_param = 'BSC'
            elif self.exchange_id == 'bybit':
                network_param = 'BSC (BEP20)'
            elif self.exchange_id in ['gateio', 'htx']:
                network_param = 'BEP20' # HTX uses uppercase 'BSC'
            elif self.exchange_id == 'bitget':
                network_param = 'bsc'
            
            # Try to fetch existing address
            try:
                params = {'network': network_param}
                # For HTX and Bitget, use 'chain' parameter instead of 'network'
                if self.exchange_id in ['bitget', 'bitmart']:
                    params = {'chain': network_param}
                
                # For specific exchanges, handle variations in the API
                if self.exchange_id == 'kucoin':
                    # KuCoin needs to specify the account type for Trading Account
                    params['type'] = 'trade'
                elif self.exchange_id == 'bybit':
                    # Bybit uses accountType parameter for Unified Trading Account
                    params['accountType'] = 'UNIFIED'
                    
                address_info = self.exchange.fetch_deposit_address(currency, params)
                if address_info and 'address' in address_info and address_info['address']:
                    logger.info(f"Found existing {network} deposit address for {currency}")
                    return address_info
            except Exception as e:
                logger.warning(f"No existing deposit address found: {e}")
                
            # Create address if requested and supported
            if create_if_needed:
                if hasattr(self.exchange, 'has') and self.exchange.has.get('createDepositAddress'):
                    try:
                        params = {'network': network_param}
                        # For HTX and Bitget, use 'chain' parameter instead of 'network'
                        if self.exchange_id in ['htx', 'bitget']:
                            params = {'chain': network_param}
                            
                        # For specific exchanges, handle variations in the API
                        if self.exchange_id == 'kucoin':
                            # KuCoin needs to specify the account type for Trading Account
                            params['type'] = 'trade'
                        elif self.exchange_id == 'bybit':
                            # Bybit uses accountType parameter for Unified Trading Account
                            params['accountType'] = 'UNIFIED'
                            
                        logger.info(f"Creating new {network} deposit address for {currency}")
                        address_info = self.exchange.create_deposit_address(currency, params)
                        return address_info
                    except Exception as e:
                        logger.error(f"Error creating deposit address: {e}")
                else:
                    logger.warning(f"{self.exchange_id} does not support creating deposit addresses via API")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting deposit address: {e}")
            return None
    
    def withdraw(self, currency='USDT', amount=0, address='', tag=None, network='BEP20'):
        """
        Withdraw BEP20 USDT to an external address
        
        Args:
            currency: Currency code (always USDT)
            amount: Amount to withdraw
            address: Destination address
            tag: Tag/memo for the transaction (if needed)
            network: Network/chain to use (always BEP20)
            
        Returns:
            Dictionary with withdrawal info or None if failed
        """
        try:
            # Force USDT and BEP20
            currency = 'USDT'
            network = 'BEP20'
            
            # Validate amount
            if amount <= 0:
                logger.error("Invalid withdrawal amount: {amount}")
                return None
                
            # Validate address
            if not address:
                logger.error("Withdrawal address cannot be empty")
                return None
                
            # Check available balance
            free_balance, _ = self.get_balance(currency)
            if free_balance < amount:
                logger.error(f"Insufficient balance: {free_balance} USDT, need {amount}")
                return None
                
            logger.info(f"Withdrawing {amount} USDT to {address} via BEP20")
            
            # Exchange-specific network parameter handling
            network_param = 'BEP20'
            params = {}
            
            # Configure withdrawal parameters based on exchange
            if self.exchange_id == 'mexc':
                network_param = 'BSC'
                params = {'network': network_param}
                
            elif self.exchange_id == 'kucoin':
                network_param = 'BSC'
                params = {
                    'network': network_param,
                    'type': 'trade'  # Specify withdrawal from Trading Account
                }
                
            elif self.exchange_id == 'htx':
                network_param = 'BSC'
                params = {'chain': network_param}
                
            elif self.exchange_id == 'gateio':
                network_param = 'BSC'
                params = {'network': network_param}
                
            elif self.exchange_id == 'bitmart':
                network_param = 'BSC'
                params = {'network': network_param}
                
            elif self.exchange_id == 'bitget':
                network_param = 'bsc'
                params = {'chain': network_param, 'networkName': network_param}
                
            elif self.exchange_id == 'bybit':
                network_param = 'BSC (BEP20)'
                params = {
                    'network': network_param,
                    'accountType': 'UNIFIED'  # Specify withdrawal from Unified Trading Account
                }
            
            # Execute withdrawal
            withdrawal = self.exchange.withdraw(currency, amount, address, tag, params)
            logger.info(f"Withdrawal initiated: {withdrawal}")
            
            return withdrawal
            
        except Exception as e:
            logger.error(f"Error withdrawing funds: {e}")
            return None
    
    def fetch_deposits(self, currency='USDT', limit=20):
        """
        Fetch recent USDT deposits
        
        Args:
            currency: Currency code (always USDT)
            limit: Maximum number of deposits to fetch
            
        Returns:
            List of deposit transactions or None if failed
        """
        try:
            # Force USDT
            currency = 'USDT'
            logger.info("Fetching recent USDT deposits")
            
            # Check if exchange supports deposit fetching
            if not hasattr(self.exchange, 'has') or not self.exchange.has.get('fetchDeposits'):
                logger.warning(f"{self.exchange_id} does not support fetching deposits via API")
                return None
            
            # Fetch deposits
            params = {}
            
            # Exchange-specific parameters
            if self.exchange_id == 'kucoin':
                params['type'] = 'trade'  # Specify Trading Account
            elif self.exchange_id == 'bybit':
                params['accountType'] = 'UNIFIED'  # Specify Unified Trading Account
            
            deposits = self.exchange.fetch_deposits(currency, None, limit, params)
            
            if deposits:
                logger.info(f"Found {len(deposits)} deposits for {currency}")
                return deposits
            else:
                logger.info(f"No deposits found for {currency}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching deposits: {e}")
            return None
    
    def fetch_withdrawals(self, currency='USDT', limit=20):
        """
        Fetch recent USDT withdrawals
        
        Args:
            currency: Currency code (always USDT)
            limit: Maximum number of withdrawals to fetch
            
        Returns:
            List of withdrawal transactions or None if failed
        """
        try:
            # Force USDT
            currency = 'USDT'
            logger.info("Fetching recent USDT withdrawals")
            
            # Check if exchange supports withdrawal fetching
            if not hasattr(self.exchange, 'has') or not self.exchange.has.get('fetchWithdrawals'):
                logger.warning(f"{self.exchange_id} does not support fetching withdrawals via API")
                return None
            
            # Fetch withdrawals
            params = {}
            
            # Exchange-specific parameters
            if self.exchange_id == 'kucoin':
                params['type'] = 'trade'  # Specify Trading Account
            elif self.exchange_id == 'bybit':
                params['accountType'] = 'UNIFIED'  # Specify Unified Trading Account
            
            withdrawals = self.exchange.fetch_withdrawals(currency, None, limit, params)
            
            if withdrawals:
                logger.info(f"Found {len(withdrawals)} withdrawals for {currency}")
                return withdrawals
            else:
                logger.info(f"No withdrawals found for {currency}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching withdrawals: {e}")
            return None
    
    def get_transaction_status(self, transaction_id, transaction_type='withdrawal', currency='USDT'):
        """
        Get the status of a USDT deposit or withdrawal transaction
        
        Args:
            transaction_id: ID of the transaction to check
            transaction_type: Type of transaction ('withdrawal' or 'deposit')
            currency: Currency code (always USDT)
            
        Returns:
            Transaction info or None if not found
        """
        try:
            # Force USDT
            currency = 'USDT'
            if transaction_type.lower() == 'withdrawal':
                transactions = self.fetch_withdrawals(currency)
            else:
                transactions = self.fetch_deposits(currency)
                
            if not transactions:
                return None
                
            # Look for transaction by ID
            for transaction in transactions:
                if transaction['id'] == transaction_id:
                    return transaction
            
            logger.warning(f"Transaction {transaction_id} not found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting transaction status: {e}")
            return None