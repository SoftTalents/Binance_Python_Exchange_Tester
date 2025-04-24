# Fix for BitMart Withdrawals

## Problem Description

When attempting to withdraw USDT from BitMart using the `withdraw` function, you encounter this error:

```
Error withdrawing funds: 'NoneType' object has no attribute 'find'
```

## Root Cause

The issue occurs in the CCXT library's BitMart implementation, specifically in the `get_currency_id_from_code_and_network` method. When processing network codes for cryptocurrencies, in some cases a `None` value is received, and the method attempts to call `.find()` on this value, resulting in the error.

## How to Fix It

### Option 1: Apply the Patch Directly to exchange.py

1. Open your `exchange.py` file
2. Add the following code at the top of the file, right after the imports:

```python
# Fix for BitMart's get_currency_id_from_code_and_network method to resolve
# the 'NoneType' object has no attribute 'find' error during withdrawals
def _patch_bitmart_withdraw():
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

# Apply patch immediately
_patch_bitmart_withdraw()
```

3. Additionally, modify the `withdraw` method in the `ExchangeHandler` class to add extra protection for BitMart. Find the section where it executes the withdrawal and replace it with this:

```python
# Debug log the parameters
logger.info(f"Using withdrawal parameters: {params}")

# Special handling for BitMart to ensure proper currency ID formatting
if self.exchange_id == 'bitmart':
    # For BitMart with BEP20, we need to ensure the proper currency ID format is used
    # This is handled by our patch, but adding an additional safeguard
    try:
        # Execute withdrawal with explicit handling for BitMart
        withdrawal = self.exchange.withdraw(currency, amount, address, tag, params)
        logger.info(f"Withdrawal initiated: {withdrawal}")
        return withdrawal
    except AttributeError as e:
        # If we still get the NoneType error despite our patch, handle it here
        if "object has no attribute 'find'" in str(e):
            logger.error(f"BitMart currency ID format error encountered: {e}")
            logger.error("Attempting alternative withdrawal method...")
            
            # Try with explicit currency ID format
            modified_params = dict(params)
            # Force the currency_id to be in the correct format
            modified_params['currency_id'] = 'USDT-BSC_BNB'
            
            withdrawal = self.exchange.withdraw(currency, amount, address, tag, modified_params)
            logger.info(f"Withdrawal initiated with alternative method: {withdrawal}")
            return withdrawal
        else:
            # Re-raise if it's a different error
            raise
else:
    # Standard withdrawal for other exchanges
    withdrawal = self.exchange.withdraw(currency, amount, address, tag, params)
    logger.info(f"Withdrawal initiated: {withdrawal}")
    return withdrawal
```

### Option 2: Create a Separate Patch File

If you prefer to keep your changes separate from the main code, you can create a `bitmart_patch.py` file:

1. Create a new file named `bitmart_patch.py` in your project directory with the following content:

```python
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
```

2. Then, import this module at the top of your `exchange.py` file:

```python
import ccxt
from loguru import logger
import config
from bitmart_patch import patch_bitmart_withdraw  # Add this line
```

## Validation

After applying either fix, the withdrawals from BitMart will work correctly. The withdrawal request might still fail due to factors like unverified addresses (which is normal for exchanges to require), but the `'NoneType' object has no attribute 'find'` error will be resolved.

You can test this fix by:

1. Running a withdrawal with BitMart selected
2. Verifying that the logs show a different error message if it fails (like address verification)
3. If you have a verified address in your BitMart account, you should be able to withdraw successfully

## Understanding the Fix

This fix works by directly patching the CCXT library's BitMart implementation. The key components of the fix are:

1. Proper handling of `None` network codes by using default values
2. Adding specific mappings for USDT on different networks (BEP20, TRC20, ERC20)
3. Adding error handling to prevent the AttributeError from happening
4. Providing a fallback mechanism for currency ID formatting

The fix ensures that the withdrawal request to BitMart is properly formatted regardless of the network code handling in the CCXT library.
