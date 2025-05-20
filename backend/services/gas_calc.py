# backend/services/gas_calc.py

def calc_usd_cost(gas_gwei: float, eth_price_usd: float, gas_limit: int) -> float:
    """
    Calculate transaction fee in USD.

    gas_gwei: base fee in Gwei
    eth_price_usd: ETH/USD price
    gas_limit: transaction gas limit (e.g., 21000 or 65000)
    """
    gas_eth = gas_gwei * gas_limit / 1e9  # Convert Gwei to ETH
    return round(gas_eth * eth_price_usd, 4)
