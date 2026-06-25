import pandas as pd
df=pd.read_csv("india_insurance_claims_synthetic.csv")
df.head()
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

features = [
    'claim_amount_inr',
    'vehicle_age_years',
    'policy_age_months',
    'claims_last_12m',
    'days_to_report',
    'india_cpi',
    'india_gdp_growth',
]

X = StandardScaler().fit_transform(df[features])

model = IsolationForest(contamination=0.10, random_state=42)
model.fit(X)

df['anomaly_score'] = model.decision_function(X).round(4)
df['anomaly_flag']  = (model.predict(X) == -1).astype(int)

def risk_label(score):
    if score < -0.025:   return 'High Risk'
    elif score < 0: return 'Medium Risk'
    else:               return 'Low Risk'

df['risk_level'] = df['anomaly_score'].apply(risk_label)

df.to_csv(
    "outputs/claims_scored.csv",
    index=False
)