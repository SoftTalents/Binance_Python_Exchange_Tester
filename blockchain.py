from loguru import logger
from web3 import Web3
from eth_account import Account
import time

class BlockchainHandler:
    def __init__(self, network='bsc'):
        """Initialize blockchain connection"""
        # Binance Smart Chain RPC nodes
        # Using both public and backup nodes for redundancy
        self.bsc_rpc_urls = [
            "https://bsc-dataseed.binance.org/",
            "https://bsc-dataseed1.binance.org/",
            "https://bsc-dataseed2.binance.org/",
            "https://bsc-dataseed3.binance.org/",
            "https://bsc-dataseed4.binance.org/",
            "https://endpoints.omniatech.io/v1/bsc/mainnet/public",
            "https://bsc.publicnode.com",
        ]
        
        # USDT token contract on BSC (BEP20)
        self.usdt_address = "0x55d398326f99059fF775485246999027B3197955"
        
        # USDT token ABI (only what we need for transfers)
        self.usdt_abi = [
            {
                "inputs": [
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"}
                ],
                "name": "transfer",
                "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "decimals",
                "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        # Connect to BSC
        self.w3 = None
        self.connected = self.connect_to_blockchain()
        
        if self.connected:
            # Initialize USDT contract
            self.usdt_contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(self.usdt_address),
                abi=self.usdt_abi
            )
            
            # Get USDT decimals
            self.usdt_decimals = self.usdt_contract.functions.decimals().call()
            logger.info(f"USDT decimals: {self.usdt_decimals}")
    
    def connect_to_blockchain(self):
        """Connect to BSC using available RPC nodes with failover"""
        for rpc_url in self.bsc_rpc_urls:
            try:
                logger.info(f"Connecting to BSC via {rpc_url}")
                web3 = Web3(Web3.HTTPProvider(rpc_url))
                
                if web3.is_connected():
                    logger.info(f"Connected to BSC node: {rpc_url}")
                    self.w3 = web3
                    return True
                else:
                    logger.warning(f"Failed to connect to BSC node: {rpc_url}")
            except Exception as e:
                logger.warning(f"Error connecting to {rpc_url}: {e}")
                
        logger.error("Failed to connect to any BSC node")
        return False
    
    def get_usdt_balance(self, address):
        """Get USDT balance for an address"""
        if not self.connected:
            logger.error("Not connected to blockchain")
            return 0
            
        try:
            address = self.w3.to_checksum_address(address)
            balance_wei = self.usdt_contract.functions.balanceOf(address).call()
            balance = balance_wei / (10 ** self.usdt_decimals)
            logger.info(f"USDT balance for {address}: {balance}")
            return balance
        except Exception as e:
            logger.error(f"Error getting USDT balance: {e}")
            return 0
    
    def transfer_usdt(self, private_key, to_address, amount):
        """
        Transfer USDT from wallet to exchange deposit address
        
        Args:
            private_key: Private key of the sender wallet
            to_address: Deposit address to send funds to
            amount: Amount of USDT to send
            
        Returns:
            Transaction hash if successful, None if failed
        """
        if not self.connected:
            logger.error("Not connected to blockchain")
            return None
            
        try:
            # Derive address from private key
            account = Account.from_key(private_key)
            from_address = account.address
            
            # Convert addresses to checksum format
            from_address = self.w3.to_checksum_address(from_address)
            to_address = self.w3.to_checksum_address(to_address)
            
            # Check sender's USDT balance
            balance = self.get_usdt_balance(from_address)
            if balance < amount:
                logger.error(f"Insufficient USDT balance: {balance}, need {amount}")
                return None
                
            # Check sender's BNB balance for gas
            bnb_balance_wei = self.w3.eth.get_balance(from_address)
            bnb_balance = self.w3.from_wei(bnb_balance_wei, 'ether')
            
            # Ensure we have at least 0.005 BNB for gas
            if bnb_balance < 0.005:
                logger.error(f"Insufficient BNB for gas: {bnb_balance}, need at least 0.005 BNB")
                return None
                
            # Convert USDT amount to wei (considering decimals)
            amount_wei = int(amount * (10 ** self.usdt_decimals))
            
            # Prepare transaction
            logger.info(f"Preparing transaction to send {amount} USDT from {from_address} to {to_address}")
            
            # Get nonce for the sender address
            nonce = self.w3.eth.get_transaction_count(from_address)
            
            # Estimate gas for the transaction
            gas_estimate = self.usdt_contract.functions.transfer(
                to_address, 
                amount_wei
            ).estimate_gas({'from': from_address})
            
            # Get current gas price with 10% boost for faster confirmation
            gas_price = int(self.w3.eth.gas_price * 1.1)
            
            # Build transaction
            transaction = self.usdt_contract.functions.transfer(
                to_address,
                amount_wei
            ).build_transaction({
                'from': from_address,
                'gas': gas_estimate,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': 56  # BSC chain ID
            })
            
            # Sign transaction
            signed_txn = Account.sign_transaction(transaction, private_key)
            
            # Send transaction
            logger.info("Sending transaction...")
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            tx_hash_hex = self.w3.to_hex(tx_hash)
            logger.info(f"Transaction sent: {tx_hash_hex}")
            
            # Wait for transaction receipt
            logger.info("Waiting for transaction confirmation...")
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if tx_receipt.status == 1:
                logger.info(f"Transaction confirmed: {tx_hash_hex}")
                return tx_hash_hex
            else:
                logger.error(f"Transaction failed: {tx_hash_hex}")
                return None
                
        except Exception as e:
            logger.error(f"Error transferring USDT: {e}")
            return None
            
    def validate_address(self, address):
        """Validate if an address is valid"""
        try:
            # Try to convert to checksum address
            checksum_address = self.w3.to_checksum_address(address)
            return True
        except:
            return False
            
    def validate_private_key(self, private_key):
        """Validate if a private key is valid and return the address if successful"""
        try:
            # Try to derive address from private key
            account = Account.from_key(private_key)
            address = account.address
            return True, address
        except:
            return False, None
            
    def get_transaction_status(self, tx_hash):
        """Get the status of a transaction"""
        try:
            # Get transaction receipt
            tx_receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            if tx_receipt is None:
                return "Pending"
            elif tx_receipt.status == 1:
                return "Confirmed"
            else:
                return "Failed"
        except Exception as e:
            logger.error(f"Error getting transaction status: {e}")
            return "Unknown"
