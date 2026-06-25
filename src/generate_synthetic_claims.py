"""
Synthetic claims generator.

Statistical parameters calibrated using:

- IRDAI Annual Report 2023-24
- IMF World Economic Outlook April 2026

Initial dataset design and parameter calibration were assisted by Claude.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

N = 15000

# --- IMF WEO India macro data (actual + projected) ---
macro = {
    2015: {'cpi': 4.91, 'gdp_growth': 8.00},
    2016: {'cpi': 4.94, 'gdp_growth': 8.26},
    2017: {'cpi': 2.49, 'gdp_growth': 6.80},
    2018: {'cpi': 4.86, 'gdp_growth': 6.45},
    2019: {'cpi': 3.72, 'gdp_growth': 3.87},
    2020: {'cpi': 6.62, 'gdp_growth': -5.83},  # COVID crash
    2021: {'cpi': 5.13, 'gdp_growth': 9.05},   # rebound
    2022: {'cpi': 6.70, 'gdp_growth': 7.24},   # inflation surge
    2023: {'cpi': 5.65, 'gdp_growth': 8.20},
    2024: {'cpi': 4.80, 'gdp_growth': 6.50},
    2025: {'cpi': 4.20, 'gdp_growth': 6.20},
    2026: {'cpi': 4.50, 'gdp_growth': 6.10},   # WEO April 2026 projection
}

insurers = [
    'New India Assurance', 'ICICI Lombard', 'Bajaj Allianz',
    'HDFC ERGO', 'Oriental Insurance', 'United India Insurance',
    'National Insurance', 'Reliance General', 'SBI General', 'Tata AIG'
]

states = {
    'Maharashtra': 0.13, 'Uttar Pradesh': 0.11, 'Tamil Nadu': 0.09,
    'Karnataka': 0.08, 'Gujarat': 0.08, 'Rajasthan': 0.07,
    'West Bengal': 0.06, 'Madhya Pradesh': 0.05, 'Delhi': 0.06,
    'Andhra Pradesh': 0.05, 'Telangana': 0.05, 'Kerala': 0.04,
    'Punjab': 0.03, 'Haryana': 0.03, 'Bihar': 0.03,
    'Odisha': 0.02, 'Assam': 0.02, 'Jharkhand': 0.01
}

vehicle_types = ['Private Car', 'Two-Wheeler', 'Commercial Vehicle']
vehicle_weights = [0.45, 0.40, 0.15]

incident_types = ['Collision', 'Theft', 'Fire', 'Natural Disaster', 'Vandalism']
incident_weights = [0.52, 0.22, 0.10, 0.10, 0.06]

garage_types = ['Network Garage', 'Non-Network Garage', 'Cash Settlement']
garage_weights = [0.50, 0.30, 0.20]

# --- Generate claim dates (weighted toward recent years) ---
start = datetime(2015, 1, 1)
end   = datetime(2026, 12, 31)
total_days = (end - start).days

# Slight upward trend in volume over years
year_weights = {y: 1.0 + (y - 2015) * 0.07 for y in range(2015, 2027)}
dates = []
for _ in range(N):
    yr = np.random.choice(list(year_weights.keys()),
                          p=np.array(list(year_weights.values())) /
                            sum(year_weights.values()))
    day_in_year = random.randint(0, 364)
    d = datetime(yr, 1, 1) + timedelta(days=day_in_year)
    if d > end:
        d = end
    dates.append(d)

dates.sort()

# --- Build rows ---
rows = []
for i, claim_date in enumerate(dates):
    yr = claim_date.year

    insurer       = np.random.choice(insurers)
    state         = np.random.choice(list(states.keys()),
                                     p=np.array(list(states.values()))/np.array(list(states.values())).sum())
    vehicle_type  = np.random.choice(vehicle_types, p=vehicle_weights)
    vehicle_age   = int(np.clip(np.random.exponential(4.5), 0, 20))
    policy_age_m  = int(np.random.uniform(1, 60))
    incident_type = np.random.choice(incident_types, p=incident_weights)
    garage_type   = np.random.choice(garage_types,   p=garage_weights)
    claims_12m    = int(np.random.poisson(0.30))
    days_to_report= int(np.clip(np.random.exponential(6), 0, 120))
    # Surveyor mandatory for claims > ₹75k (set after amount is calculated)

    # Base claim amount — Gamma, INR
    base_amount = np.random.gamma(shape=2.2, scale=42000)
    base_amount = float(np.clip(base_amount, 5000, 800000))

    # --- Fraud probability logic (additive, IRDAI-calibrated ~9% rate) ---
    fp = 0.025  # base

    if policy_age_m < 6:              fp += 0.12
    if garage_type == 'Cash Settlement': fp += 0.10
    if incident_type in ('Theft','Fire'): fp += 0.08
    if claims_12m >= 3:               fp += 0.15
    if days_to_report > 30:           fp += 0.07
    if vehicle_age > 12:              fp += 0.06
    if vehicle_type == 'Commercial Vehicle': fp += 0.04
    # Macro: high inflation & GDP contraction years raise fraud
    cpi = macro[yr]['cpi']
    gdp = macro[yr]['gdp_growth']
    if cpi > 6.0:                     fp += 0.04
    if gdp < 0:                       fp += 0.06   # COVID year

    fp = min(fp, 0.92)
    fraud_flag = int(np.random.binomial(1, fp))

    # Inflate claim amount for fraudulent claims
    if fraud_flag == 1:
        base_amount *= np.random.uniform(2.5, 7.0)
        base_amount = min(base_amount, 1500000)

    claim_amount = round(base_amount, 2)
    surveyor_flag = 1 if claim_amount > 75000 else 0

    rows.append({
        'claim_id':            f'CLM-{i+1:06d}',
        'claim_date':          claim_date.strftime('%Y-%m-%d'),
        'claim_year':          yr,
        'claim_month':         claim_date.month,
        'insurer':             insurer,
        'state':               state,
        'vehicle_type':        vehicle_type,
        'vehicle_age_years':   vehicle_age,
        'policy_age_months':   policy_age_m,
        'incident_type':       incident_type,
        'garage_type':         garage_type,
        'claim_amount_inr':    claim_amount,
        'claims_last_12m':     claims_12m,
        'days_to_report':      days_to_report,
        'surveyor_flag':       surveyor_flag,
        'india_cpi':           macro[yr]['cpi'],
        'india_gdp_growth':    macro[yr]['gdp_growth'],
        'fraud_flag':          fraud_flag,
    })

df = pd.DataFrame(rows)

# Quick sanity checks
fraud_rate = df['fraud_flag'].mean()
print(f"Total rows        : {len(df)}")
print(f"Fraud rate        : {fraud_rate:.2%}")
print(f"Date range        : {df['claim_date'].min()} → {df['claim_date'].max()}")
print(f"Avg claim (legit) : ₹{df[df['fraud_flag']==0]['claim_amount_inr'].mean():,.0f}")
print(f"Avg claim (fraud) : ₹{df[df['fraud_flag']==1]['claim_amount_inr'].mean():,.0f}")
print(f"Fraud by year:\n{df.groupby('claim_year')['fraud_flag'].mean().round(3)}")

df.to_csv("data/raw/india_insurance_claims_synthetic.csv", index=False)
print("\nSaved to folder.")