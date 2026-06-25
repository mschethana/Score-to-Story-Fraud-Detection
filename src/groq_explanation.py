import pandas as pd
import os
from groq import Groq

client = Groq(api_key=os.environ['GROQ_API_KEY'])
df = pd.read_csv("outputs/claims_scored.csv")

top_claims = set(
    df.sort_values('anomaly_score')
      .head(20)['claim_id']
)

def get_insight(row):

    if row['claim_id'] not in top_claims:
        return 'AI analysis not requested.'

    # Skip non-anomalies
    if row['anomaly_flag'] == 0:
        return 'No anomaly detected.'

    prompt = f"""
You are an insurance fraud analyst.

Write exactly 2 concise sentences explaining why this motor insurance claim appears suspicious.

Claim Amount: INR {row['claim_amount_inr']:,.0f}
Policy Age: {row['policy_age_months']} months
Prior Claims: {row['claims_last_12m']}
Days To Report: {row['days_to_report']}
Vehicle Age: {row['vehicle_age_years']} years
Incident Type: {row['incident_type']}
Garage Type: {row['garage_type']}
India CPI: {row['india_cpi']}
India GDP Growth: {row['india_gdp_growth']}
Anomaly Score: {row['anomaly_score']}
Risk Level: {row['risk_level']}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=80
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Insight unavailable: {str(e)}"

print("Generating AI insights for flagged claims...")

df['ai_insight'] = df.apply(get_insight, axis=1)

flagged = int(df['anomaly_flag'].sum())
df['ai_analysis_requested'] = df['claim_id'].isin(top_claims)

print(f"Done. Insights generated for {flagged} flagged claims.")
df.to_csv(
    "data/processed/claims_AI_enriched.csv",
    index=False
)
