import pandas as pd
from datetime import datetime

def price_storage_contract(
    injection_dates, withdrawal_dates, purchase_prices, sale_prices,
    injection_rate, withdrawal_rate, max_volume, storage_cost_per_month,
    inj_cost_per_unit=0.01, wth_cost_per_unit=0.01
):
    """
    Calculates the net value of a multi-period natural gas storage contract.
    """
    events = []
    # Be flexible with input date formats (strings or datetime-like)
    for d, p in zip(injection_dates, purchase_prices):
        events.append((pd.to_datetime(d), 'inject', p))
    for d, p in zip(withdrawal_dates, sale_prices):
        events.append((pd.to_datetime(d), 'withdraw', p))
        
    events.sort(key=lambda x: x[0])
    
    if not events:
        return 0.0
    
    inventory = 0.0
    cash_flow = 0.0
    
    for date, action, price in events:
        if action == 'inject':
            available_space = max_volume - inventory
            volume_to_inject = min(injection_rate, available_space)
            inventory += volume_to_inject
            cash_flow -= volume_to_inject * price
            cash_flow -= volume_to_inject * inj_cost_per_unit
            
        elif action == 'withdraw':
            volume_to_withdraw = min(withdrawal_rate, inventory)
            inventory -= volume_to_withdraw
            cash_flow += volume_to_withdraw * price
            cash_flow -= volume_to_withdraw * wth_cost_per_unit
            
    first_date = events[0][0]
    last_date = events[-1][0]
    
    storage_days = (last_date - first_date).days
    storage_months = max(1, round(storage_days / 30.4375)) 
    
    total_storage_cost = storage_months * storage_cost_per_month
    cash_flow -= total_storage_cost
    
    return {
        "Final Contract Value": cash_flow,
        "Total Months Billed": storage_months,
        "Total Storage Cost": total_storage_cost,
        "Remaining Inventory": inventory
    }

# --- Execution (Run) Section ---
if __name__ == "__main__":
    print("Loading data and calculating contract value...\n")
    
    try:
        # 1. Dataset load karein
        df = pd.read_csv("Nat_Gas (2).csv")
        df['Dates'] = pd.to_datetime(df['Dates'])
        
        # Ek dictionary banayein jisse date ke hisaab se price mil jaye
        price_map = dict(zip(df['Dates'], df['Prices']))

        # 2. Strategy Dates set karein
        inj_dates = ['2021-05-31', '2021-06-30', '2021-07-31', '2021-08-31']
        wth_dates = ['2021-11-30', '2021-12-31', '2022-01-31', '2022-02-28']

        # Dates ke corresponding prices CSV se nikalen
        inj_prices = [price_map[pd.to_datetime(d)] for d in inj_dates]
        wth_prices = [price_map[pd.to_datetime(d)] for d in wth_dates]

        # 3. Function ko call karein
        result = price_storage_contract(
            injection_dates=inj_dates,
            withdrawal_dates=wth_dates,
            purchase_prices=inj_prices,
            sale_prices=wth_prices,
            injection_rate=250_000,       
            withdrawal_rate=250_000,      
            max_volume=1_000_000,         
            storage_cost_per_month=100_000, 
            inj_cost_per_unit=0.01,       
            wth_cost_per_unit=0.01
        )

        # 4. Result print karein
        for key, value in result.items():
            print(f"{key}: {value:,.2f}")
            
    except FileNotFoundError:
        print("Error: 'Nat_Gas (2).csv' file nahi mili! Kripya check karein ki CSV file aur code same jagah par hain.")
    except Exception as e:
        print(f"Kuch error aayi: {e}")