import ccxt

def patch_bitmart_withdraw():
    """
    Apply patches to BitMart CCXT implementation to fix withdrawal issues.
    This fixes the 'NoneType' object has no attribute 'find' error.
    """
    # Save original method
    original_method = ccxt.bitmart.get_currency_id_from_code_and_network
    
    # Create patched method
    def patched_get_currency_id_from_code_and_network(self, currencyCode, networkCode):
        """
        Fixed version of the method that handles networkCode correctly
        and prevents the NoneType error.
        """
        if networkCode is None:
            networkCode = self.default_network_code(currencyCode)
            
        # BitMart has special currency IDs for withdrawals with specific networks
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
            # Handle the specific 'find' error
            if "object has no attribute 'find'" in str(e):
                # Fall back to a simple network addition format
                if networkCode:
                    return f"{currencyCode}-{networkCode}"
                else:
                    return currencyCode
            # Re-raise any other AttributeErrors
            raise
    
    # Apply the patch by replacing the method
    ccxt.bitmart.get_currency_id_from_code_and_network = patched_get_currency_id_from_code_and_network

# Apply patch when this module is imported
patch_bitmart_withdraw()
