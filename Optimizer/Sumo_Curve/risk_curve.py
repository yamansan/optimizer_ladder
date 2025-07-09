from __future__ import annotations

"""trading.risk

High-level risk utilities including the `R_survival` function that the live
engine will query every time it receives fresh market data.

The code is a cleaned-up, script-ready extraction of the logic you developed
in the Jupyter notebook.
"""

from typing import Dict, List, Tuple, Union
import logging
import numpy as np
import sys
import os
import pandas as pd
import time
import csv

# Add the workspace root to Python path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, workspace_root)

from Optimizer.risk_utils import (
    zn_to_decimal,
    decimal_to_zn,  # noqa: F401 – exposed for convenience
    levels_crossed,
    TECH_LEVELS_DEC,
)

logger = logging.getLogger(__name__)

def breakeven(price, current_price):
    """
    This function determines the breakeven at each price. For now, it is a constant.
    """
    if current_price > price:
        return -3.0
    else:
        return 3
    

def R_dict(current_price,  tech_levels_dec, stop_loss = -10000, NBM=25, pnl_0=0):
    """
    This function calculates the risk dictionary i.e. the risk for each NBM level above and below the current price.
    """

    # Convert the current price to a decimal if it is a string.
    if isinstance(current_price, str):
        current_price_dec = zn_to_decimal(current_price)
    else:
        current_price_dec = current_price
    
    # Calculate the NBM levels above and below the current price.
    NBM_levels_above_dec = levels_crossed(current_price_dec, current_price_dec + NBM/16, tech_levels_dec)
    NBM_levels_below_dec = levels_crossed(current_price_dec, current_price_dec - NBM/16, tech_levels_dec)

    # levels_above are all the prices where we add some negative risk.
    # If the current price itself is not a technical level, we add it to the list of levels_above since we are starting with a risk.
    if NBM_levels_above_dec[0] == current_price_dec:
        levels_above = NBM_levels_above_dec
    else:
        levels_above = [current_price_dec] + NBM_levels_above_dec
    
    # levels_below are all the prices where we add some positve risk.
    # If the current price itself is not a technical level, we add it to the list of levels_below since we are starting with a risk.
    if NBM_levels_below_dec[0] == current_price_dec:
        levels_below = NBM_levels_below_dec
    else:
        levels_below = [current_price_dec] + NBM_levels_below_dec
    
    # Filter levels_above: ensure minimum distance of 16/3 between consecutive levels
    while len(levels_above) > 1 and (levels_above[1] - levels_above[0]) < 3/16:
        levels_above.pop(1)  # Remove the second element
        
    # Filter levels_below: ensure minimum distance of 16/3 between consecutive levels  
    while len(levels_below) > 1 and (levels_below[0] - levels_below[1]) < 3/16:
        levels_below.pop(1)  # Remove the second element


    # Calculate the deltaL for the levels_above and levels_below.
    deltaL_above = np.array(levels_above[1:]) - np.array(levels_above[:-1])
    deltaL_below = np.array(levels_below[1:]) - np.array(levels_below[:-1])
    
    # Calculate the product coefficient for the levels_above and levels_below.
    # coeff_above looks like the following: deltaL_above[0] * (1 + (deltaL_above[1] / breakeven(levels_above[0])) ) * (1 + (deltaL_above[2] / breakeven(levels_above[1])) ) * ...
    prod = deltaL_above[0]
    coeff_above = [prod]
    for i in range(1, len(deltaL_above)):
        prod = prod * (1 + (deltaL_above[i] / (breakeven(levels_above[i], current_price_dec)/16 ) ) ) # 3/16 is the pnl breakeven constant
        coeff_above.append(prod)

    prod = deltaL_below[0]
    coeff_below = [prod]
    for i in range(1, len(deltaL_below)):
        prod = prod * (1 + (deltaL_below[i] / (breakeven(levels_below[i], current_price_dec)/16) ) ) # 3/16 is the pnl breakeven constant
        coeff_below.append(prod)
    
    # coeff_above and coeff_below are in decimal form.

    R0_above = (stop_loss / coeff_above[-1])/16 # 16 is the number of ticks in a basis point
    R0_below = (stop_loss / coeff_below[-1])/16 # 16 is the number of ticks in a basis point

    print("current_price_dec: ", current_price_dec)
    print("levels_above: ", levels_above)
    print("levels_below: ", levels_below)
    print("R0_above: ", R0_above)
    print("R0_below: ", R0_below)
    print("coeff_above: ", coeff_above)
    print("coeff_below: ", coeff_below)
    print("deltaL_above: ", deltaL_above)
    print("deltaL_below: ", deltaL_below)

    print("Length of coeff_above: ", len(coeff_above))
    print("Length of coeff_below: ", len(coeff_below))
    print("Length of levels_above: ", len(levels_above))
    print("Length of levels_below: ", len(levels_below))

    # Initialize the risk dictionary.
    R_dict_result = {current_price_dec: R0_above}

    for i in range(1, len(levels_above)):
        R_dict_result[levels_above[i]] = R0_above * coeff_above[i-1]/(breakeven(levels_above[i], current_price_dec)/16)

    for i in range(1, len(levels_below)):
        R_dict_result[levels_below[i]] = R0_below * coeff_below[i-1]/(breakeven(levels_below[i], current_price_dec)/16)

    return R_dict_result, R0_above, R0_below


print(R_dict("111'01", TECH_LEVELS_DEC))