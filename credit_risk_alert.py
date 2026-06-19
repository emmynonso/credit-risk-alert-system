# ============================================
# CREDIT RISK ALERT SYSTEM
# Nigerian Banking Portfolio Project
# ============================================

import pandas as pd
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# --- Email Configuration ---
import os

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

# --- Database Connection ---
conn = sqlite3.connect('credit_risk.db')

# --- Fetch High Risk Borrowers ---
def get_high_risk_borrowers():
    query = """
    SELECT 
        CustomerID, Age, AgeGroup, MonthlyIncome_Formatted,
        TotalLatePayments, DaysLate_90Plus, RiskScore, RiskLevel,
        CBN_RiskBand, Default_Probability_PCT, Prediction_Result
    FROM loan_records
    WHERE DaysLate_90Plus >= 2
    AND Default_Probability_PCT >= 50
    AND CBN_RiskBand IN ('Substandard', 'Doubtful', 'Loss')
    ORDER BY Default_Probability_PCT DESC
    LIMIT 20
    """
    return pd.read_sql_query(query, conn)

# --- Build Email HTML ---
def build_email_body(flagged_df):
    total_flagged = len(flagged_df)
    avg_risk_score = flagged_df['RiskScore'].mean().round(2)
    avg_default_prob = flagged_df['Default_Probability_PCT'].mean().round(2)
    highest_risk = flagged_df['RiskScore'].max()
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
    table_rows = ""
    for _, row in flagged_df.iterrows():
        if row['CBN_RiskBand'] == 'Loss':
            color = '#ff4444'
        elif row['CBN_RiskBand'] == 'Doubtful':
            color = '#ff8800'
        else:
            color = '#ffaa00'
            
        table_rows += f"""
        <tr>
            <td style="padding:8px;border:1px solid #ddd">{row['CustomerID']}</td>
            <td style="padding:8px;border:1px solid #ddd">{row['Age']}</td>
            <td style="padding:8px;border:1px solid #ddd">{row['MonthlyIncome_Formatted']}</td>
            <td style="padding:8px;border:1px solid #ddd">{row['DaysLate_90Plus']}</td>
            <td style="padding:8px;border:1px solid #ddd">{row['RiskScore']}</td>
            <td style="padding:8px;border:1px solid #ddd">{row['RiskLevel']}</td>
            <td style="padding:8px;border:1px solid #ddd;background-color:{color};color:white;font-weight:bold">{row['CBN_RiskBand']}</td>
            <td style="padding:8px;border:1px solid #ddd">{row['Default_Probability_PCT']}%</td>
        </tr>
        """
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin:0; padding:20px; background-color:#f4f4f4;">
        <div style="background-color:#1a1a2e; padding:20px; border-radius:8px; margin-bottom:20px;">
            <h1 style="color:#f0a500; margin:0;">🚨 WARNING CREDIT RISK ALERT!</h1>
            <p style="color:white; margin:5px 0 0 0;">Nigerian Credit Portfolio — Early Warning System</p>
            <p style="color:#aaa; margin:5px 0 0 0; font-size:12px;">Generated: {timestamp}</p>
        </div>
        
        <div style="display:flex; gap:15px; margin-bottom:20px;">
            <div style="background:white; padding:15px; border-radius:8px; flex:1; border-left:4px solid #ff4444;">
                <p style="margin:0; color:#666; font-size:12px;">TOTAL FLAGGED</p>
                <h2 style="margin:5px 0; color:#ff4444;">{total_flagged}</h2>
                <p style="margin:0; color:#666; font-size:12px;">borrowers need attention</p>
            </div>
            <div style="background:white; padding:15px; border-radius:8px; flex:1; border-left:4px solid #ff8800;">
                <p style="margin:0; color:#666; font-size:12px;">AVG RISK SCORE</p>
                <h2 style="margin:5px 0; color:#ff8800;">{avg_risk_score}</h2>
                <p style="margin:0; color:#666; font-size:12px;">out of 100</p>
            </div>
            <div style="background:white; padding:15px; border-radius:8px; flex:1; border-left:4px solid #cc0000;">
                <p style="margin:0; color:#666; font-size:12px;">AVG DEFAULT PROBABILITY</p>
                <h2 style="margin:5px 0; color:#cc0000;">{avg_default_prob}%</h2>
                <p style="margin:0; color:#666; font-size:12px;">model confidence</p>
            </div>
            <div style="background:white; padding:15px; border-radius:8px; flex:1; border-left:4px solid #1a1a2e;">
                <p style="margin:0; color:#666; font-size:12px;">HIGHEST RISK SCORE</p>
                <h2 style="margin:5px 0; color:#1a1a2e;">{highest_risk}</h2>
                <p style="margin:0; color:#666; font-size:12px;">maximum recorded</p>
            </div>
        </div>
        
        <div style="background:#fff3cd; padding:15px; border-radius:8px; margin-bottom:20px; border-left:4px solid #f0a500;">
            <p style="margin:0; color:#856404;">⚠️ <strong>IMMEDIATE ACTION REQUIRED:</strong> The following borrowers have been flagged by our ML-powered credit risk system.</p>
        </div>
        
        <div style="background:white; padding:20px; border-radius:8px; margin-bottom:20px;">
            <h3 style="color:#1a1a2e; margin-top:0;">Flagged Borrowers — Detailed Report</h3>
            <table style="width:100%; border-collapse:collapse; font-size:13px;">
                <thead>
                    <tr style="background-color:#1a1a2e; color:white;">
                        <th style="padding:10px; text-align:left;">Customer ID</th>
                        <th style="padding:10px; text-align:left;">Age</th>
                        <th style="padding:10px; text-align:left;">Monthly Income</th>
                        <th style="padding:10px; text-align:left;">Days 90+ Late</th>
                        <th style="padding:10px; text-align:left;">Risk Score</th>
                        <th style="padding:10px; text-align:left;">Risk Level</th>
                        <th style="padding:10px; text-align:left;">CBN Band</th>
                        <th style="padding:10px; text-align:left;">Default Probability</th>
                    </tr>
                </thead>
                <tbody>{table_rows}</tbody>
            </table>
        </div>
        
        <div style="background:#1a1a2e; padding:15px; border-radius:8px; text-align:center;">
            <p style="color:#aaa; margin:0; font-size:12px;">Automated Credit Risk Scorecard System</p>
        </div>
    </body>
    </html>
    """
    return html

# --- Send Email ---
def send_alert_email():
    flagged = get_high_risk_borrowers()
    
    if len(flagged) == 0:
        print(f"[{datetime.now()}] No high risk borrowers found — no alert sent!")
        return
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"CREDIT RISK ALERT — {datetime.now().strftime('%B %d, %Y')}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    
    html_body = build_email_body(flagged)
    msg.attach(MIMEText(html_body, 'html'))
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print(f"[{datetime.now()}] Alert email sent! Flagged: {len(flagged)}")
    except Exception as e:
        print(f"[{datetime.now()}] Email error: {str(e)}")

# --- Main Execution ---
if __name__ == "__main__":
    print(f"Starting Credit Risk Alert System at {datetime.now()}")
    send_alert_email()
    print(f"Alert system completed at {datetime.now()}")
