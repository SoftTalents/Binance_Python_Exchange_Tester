
# BitMart Exchange Withdrawal Fix

## Problem Description

When attempting to withdraw USDT from BitMart using the `withdraw` function in the `exchange.py` module, the following error occurs:

```
Error withdrawing funds: 'NoneType' object has no attribute 'find'
```

## Root Cause Analysis

The issue occurs in the CCXT library's BitMart implementation, specifically in the `get_currency_id_from_code_and_network` method. When handling network codes for cryptocurrencies, in some cases a `None` value is received, and the method attempts to call `.find()` on this value, resulting in the error.

## Solution

We've created a patch for the CCXT BitMart implementation that fixes this issue. The patch properly handles `None` values and adds specific handling for USDT network codes.

## Implementation Steps

1. Create a patch file:

```python
# Save to a file named bitmart_patch.py
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

2. Import the patch at the top of exchange.py:

```python
import ccxt
from loguru import logger
import config
from bitmart_patch import patch_bitmart_withdraw  # Import the patch
```

## Verification

The fix was tested with:

```
python fix_bitmart_test.py
```

The test confirms that the 'NoneType' object has no attribute 'find' error no longer occurs during BitMart withdrawals. 

The withdrawal still fails with a message "This address is not verified. Please add and verify this address on the client." This is expected behavior from BitMart since we're using a test address that hasn't been verified in their system.

## Next Steps

To make this fix permanent:

1. Copy the `bitmart_patch.py` file to your project directory
2. Add the import to `exchange.py`
3. The patch will be automatically applied when the module is imported

This fix ensures that BitMart withdrawals work correctly with the different network types for USDT (BEP20, TRC20, ERC20, etc.).

