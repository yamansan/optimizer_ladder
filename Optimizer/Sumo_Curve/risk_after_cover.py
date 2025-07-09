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

# ---------------------------------------------------------------------------
# Basic helpers (kept identical to the NB for traceability)
# ---------------------------------------------------------------------------

def breakeven(price: float, current_price: float) -> float:
    """Return the breakeven constant (ticks) depending on direction."""
    return -3.0 if current_price > price else 3.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def R_survival(
    current_price: Union[str, float],
    R0: float,
    *,
    tech_levels_dec: np.ndarray | List[float] = TECH_LEVELS_DEC,
    stop_loss: float = -10_0000.0,
    NBM: float = 25.0,
    pnl_0: float = 0.0,
) -> Tuple[Dict[float, float], float, float]:
    """Compute the risk curve that lets you survive to the stop_loss.

    Parameters
    ----------
    current_price : str | float
        Current market price.  Strings must be CBOT 32nds (e.g. "111'08+").
    R0 : float
        Current risk (positive = long, negative = short).
    tech_levels_dec : array-like
        Sorted list/array of technical levels in decimal format.
    stop_loss : float, default -10_000
        Dollar PnL at which we give up.
    NBM : int, default 25
        Nearest Break-Even Margin (in 1/16th of a point).
    pnl_0 : float, default 0
        PnL accumulated so far in the on-going trade.

    Returns
    -------
    risk_curve : dict {price_level : target_risk}
        Dictionary of the risk that should be held after each level is crossed.
    extreme_level : float
        The farthest level we can survive before hitting the stop loss.
    ticks_to_extreme : float
        Distance to *extreme_level* expressed in ticks (1/32nd).
    """
    # ------------------------------------------------------------------
    # Convert price to decimal early; keep the string for debug/logging only.
    # ------------------------------------------------------------------
    cp_dec = zn_to_decimal(current_price) if isinstance(current_price, str) else current_price

    # ------------------------------------------------------------------
    # Build the list of technical levels within ±NBM/16 around current price
    # ------------------------------------------------------------------
    nbm_high = cp_dec + NBM / 16.0
    nbm_low  = cp_dec - NBM / 16.0

    lvls_above = levels_crossed(cp_dec, nbm_high, tech_levels_dec)
    lvls_below = levels_crossed(cp_dec, nbm_low,  tech_levels_dec)

    # Make sure *current price* is present at index 0 in both lists
    if not lvls_above or lvls_above[0] != cp_dec:
        lvls_above.insert(0, cp_dec)
    if not lvls_below or lvls_below[0] != cp_dec:
        lvls_below.insert(0, cp_dec)

    # Filter so that first two levels are ≥ 3/16 apart
    while len(lvls_above) > 1 and (lvls_above[1] - lvls_above[0]) < 3 / 16:
        lvls_above.pop(1)
    while len(lvls_below) > 1 and (lvls_below[0] - lvls_below[1]) < 3 / 16:
        lvls_below.pop(1)

    # ------------------------------------------------------------------
    # Pre-compute coefficient products for above & below directions
    # ------------------------------------------------------------------
    d_above = np.diff(lvls_above)
    d_below = np.diff(lvls_below)

    coeff_above: List[float] = []
    prod = d_above[0] if len(d_above) else 0.0
    if prod:
        coeff_above.append(prod)
        for i in range(1, len(d_above)):
            prod *= 1 + d_above[i] / (breakeven(lvls_above[i], cp_dec) / 16)
            coeff_above.append(prod)

    coeff_below: List[float] = []
    prod = d_below[0] if len(d_below) else 0.0
    if prod:
        coeff_below.append(prod)
        for i in range(1, len(d_below)):
            prod *= 1 + d_below[i] / (breakeven(lvls_below[i], cp_dec) / 16)
            coeff_below.append(prod)

    # ------------------------------------------------------------------
    # Search how far we can go before stop_loss is violated
    # ------------------------------------------------------------------
    new_stop = stop_loss - pnl_0

    def _find_extreme(risk: float, coeffs: List[float], levels: List[float]) -> Tuple[float, int]:
        for idx, c in enumerate(coeffs):
            if risk * c * 16 <= new_stop:
                return levels[idx], idx
        # if we exhaust the loop w/out triggering stop, we can survive all
        return levels[len(coeffs)], len(coeffs)  # last level

    if R0 > 0:  # long risk ⇒ danger is *below*
        extreme, idx = _find_extreme(R0, coeff_below, lvls_below)
        coeffs      = coeff_below
        levels      = lvls_below
    elif R0 < 0:  # short risk ⇒ danger is *above*
        extreme, idx = _find_extreme(R0, coeff_above, lvls_above)
        coeffs      = coeff_above
        levels      = lvls_above
    else:
        # Flat position – nothing to do
        return {}, cp_dec, 0.0

    # ------------------------------------------------------------------
    # Build the risk curve – start at current price then walk toward extreme
    # ------------------------------------------------------------------
    risk_curve: Dict[float, float] = {cp_dec: R0}
    for i in range(1, idx + 1):
        lvl   = levels[i]
        coeff = coeffs[i - 1]
        risk_curve[lvl] = R0 * coeff / (breakeven(lvl, cp_dec) / 16)

    ticks_to_extreme = abs(extreme - cp_dec) * 16

    # ------------------------------------------------------------------
    # Verbose logging (can be silenced by the caller)
    # ------------------------------------------------------------------
    logger.debug("R_survival → current=%s (%.5f), R0=%s, extreme=%.5f (%s ticks)",
                 current_price, cp_dec, R0, extreme, ticks_to_extreme)

    risk_curve = {k: float(v) for k, v in risk_curve.items()}
    print("Risk Curve: ", risk_curve)
    return risk_curve, extreme, ticks_to_extreme
# ---------------------------------------------------------------------------
# Streaming functionality
# ---------------------------------------------------------------------------

def calculate_net_position(fills_df) -> float:
    """Calculate net position from fills dataframe."""
    net_position = 0.0
    for _, row in fills_df.iterrows():
        quantity = float(row['Quantity'])
        if row['SideName'] == 'BUY':
            net_position += quantity
        elif row['SideName'] == 'SELL':
            net_position -= quantity
    return net_position


def stream_r_survival(
    input_file: str = "data/output/ladder/continuous_fills.csv",
    output_file: str = "r_survival_streaming.csv",
    interval: float = 2.0
) -> None:
    """Stream R_survival calculations based on continuous fills.
    
    Parameters
    ----------
    input_file : str
        Path to continuous fills CSV file
    output_file : str  
        Path to output CSV file for R_survival results
    interval : float
        Polling interval in seconds
    """
    print(f"Starting R_survival streaming monitor...")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"Interval: {interval}s")
    
    last_processed_count = 0
    
    # Create output file with headers
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Date', 'Time', 'SideName', 'Quantity', 'Price', 'OrderId', 'Exchange', 
            'Contract', 'CurrentUser', 'risk_curve', 'extreme_level', 'ticks_to_extreme'
        ])
    
    while True:
        try:
            if not os.path.exists(input_file):
                time.sleep(interval)
                continue
                
            # Read the CSV file
            df = pd.read_csv(input_file)
            
            # Filter for Eric, CME, ZN Jun25
            mask = (df['CurrentUser'] == 'Eric') & (df['Exchange']=='CME') & (df['Contract'] == 'ZN Sep25')
            filtered_df = df[mask].copy()

            # Check if we have new data
            current_count = len(filtered_df)
            if current_count <= last_processed_count:
                time.sleep(interval)
                continue
                
            if filtered_df.empty:
                time.sleep(interval)
                continue
            
            # Create net_position column
            filtered_df['signed_quantity'] = np.where(filtered_df['SideName'] == 'BUY', 
                                                     filtered_df['Quantity'], 
                                                     -filtered_df['Quantity'])
            filtered_df['net_position'] = (62.5)*filtered_df['signed_quantity'].cumsum()
            
            # Process only new rows
            new_rows = filtered_df.iloc[last_processed_count:]
            
            for idx, row in new_rows.iterrows():
                net_position = row['net_position']
                current_price = float(row['Price'])
                
                # Skip if position is flat
                if net_position == 0:
                    continue
                
                # Calculate R_survival
                try:
                    risk_curve, extreme_level, ticks_to_extreme = R_survival(
                        current_price=current_price,
                        R0=net_position
                    )
                    
                    # Write result to output
                    with open(output_file, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            row['Date'],
                            row['Time'],
                            row['SideName'],
                            row['Quantity'],
                            row['Price'],
                            row['OrderId'],
                            row['Exchange'],
                            row['Contract'],
                            row['CurrentUser'],
                            str(risk_curve),
                            extreme_level,
                            ticks_to_extreme
                        ])
                    
                    print(f"[{row['Date']} {row['Time']}] R0={net_position:.1f}, Price={current_price}, "
                          f"Extreme={extreme_level:.5f}, Ticks={ticks_to_extreme:.1f}")
                    
                except Exception as e:
                    print(f"Error calculating R_survival: {e}")
            
            last_processed_count = current_count
            
        except Exception as e:
            print(f"Error processing file: {e}")
            
        time.sleep(interval)


if __name__ == "__main__":
    # Run the streaming monitor
    stream_r_survival() 