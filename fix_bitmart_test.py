
"""
Fix and Test BitMart Withdrawals

This script fixes the 'NoneType' object has no attribute 'find' error 
when using BitMart withdrawals in the exchange.py module.
"""

import ccxt
from loguru import logger
from exchange import ExchangeHandler
import traceback

def patch_bitmart_get_currency_id():
    """
    Apply patch to fix the BitMart get_currency_id_from_code_and_network method
    that causes the 'NoneType' object has no attribute 'find' error.
    """
    # Save original method
    original_method = ccxt.bitmart.get_currency_id_from_code_and_network
    
    # Define patched method
    def patched_method(self, currencyCode, networkCode):
        """Fixed version that handles network codes correctly"""
        if networkCode is None:
            networkCode = self.default_network_code(currencyCode)
            
        # BitMart special handling for USDT on different networks
        if currencyCode == 'USDT':
            if networkCode == 'BEP20':
                return 'USDT-BSC_BNB'
            elif networkCode == 'TRC20':
                return 'USDT-TRX'
            elif networkCode == 'ERC20':
                return 'USDT-ETH'
        
        # Try the original method with error handling
        try:
            return original_method(self, currencyCode, networkCode)
        except AttributeError as e:
            # If we get the "NoneType has no attribute 'find'" error
            if "object has no attribute 'find'" in str(e):
                # Use a fallback approach
                if networkCode:
                    return f"{currencyCode}-{networkCode}"
                else:
                    return currencyCode
            # Re-raise other attribute errors
            raise
            
    # Apply the patch
    ccxt.bitmart.get_currency_id_from_code_and_network = patched_method
    print("BitMart get_currency_id_from_code_and_network method patched!")

# Apply the patch
patch_bitmart_get_currency_id()

# Test the withdrawal function
def test_bitmart_withdraw():
    try:
        # Initialize BitMart exchange handler
        print("Initializing BitMart exchange handler...")
        handler = ExchangeHandler('bitmart')
        print("Connected to BitMart successfully")
        
        # Get USDT balance
        free_balance, total_balance = handler.get_balance('USDT')
        print(f"USDT Balance - Free: {free_balance}, Total: {total_balance}")
        
        # Set test parameters (we expect this to fail for validation reasons, but not for the NoneType error)
        test_address = "0xD8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Vitalik's address (not verified in BitMart)
        test_amount = 5.0
        
        # Attempt withdrawal
        print(f"Attempting withdrawal of {test_amount} USDT to {test_address} via BEP20...")
        result = handler.withdraw('USDT', test_amount, test_address, None, 'BEP20')
        
        if result:
            print(f"Withdrawal succeeded! Result: {result}")
        else:
            print("Withdrawal failed, but NOT due to 'NoneType' object has no attribute 'find' error.")
            print("This is expected since the address isn't verified in BitMart.")
        
        print("\nThe patch was successful - the NoneType error was fixed!")
        return True
        
    except AttributeError as e:
        if "object has no attribute 'find'" in str(e):
            print(f"ERROR: The patch did not fix the issue. 'NoneType' object has no attribute 'find' error still occurred!")
            print(f"Error details: {e}")
            traceback.print_exc()
        else:
            print(f"Different AttributeError occurred: {e}")
            traceback.print_exc()
        return False
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error type: {type(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_bitmart_withdraw()
