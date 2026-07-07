import sys
import os

# Adjust path to import backend modules
sys.path.append(os.path.dirname(__file__))

from database import get_db_connection, DB_PATH
from ml_engine import detect_anomalies, forecast_revenue
from assistant import run_assistant_query

def verify():
    print("=== EduLedger AI Backend Verification ===")
    
    # 1. Database Check
    if not os.path.exists(DB_PATH):
        print("[-] Database file not found!")
        sys.exit(1)
    print("[+] Database file exists.")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tables = ["User", "Student", "FeeRecord", "ExpenseRecord", "TransactionRecord"]
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t};")
        count = cursor.fetchone()[0]
        print(f"[+] Table '{t}' exists and has {count} record(s).")
        
    conn.close()
    
    # 2. Anomaly Detection check
    print("\n--- Testing Anomaly Detection & SHAP ---")
    anoms = detect_anomalies()
    flagged = [a for a in anoms if a["is_anomaly"]]
    print(f"[+] Total expenses analyzed: {len(anoms)}")
    print(f"[+] Anomalies flagged: {len(flagged)}")
    
    for f in flagged[:3]:
        print(f"  * Ref #{f['id']} - Amount: ${f['amount']:.2f} by {f['submitted_by']} - Explanation: {f['explanation']}")
        
    if len(flagged) == 0:
        print("[-] Error: No anomalies flagged! We injected 4 anomalies in seed.py.")
        sys.exit(1)
        
    # 3. Forecasting check
    print("\n--- Testing Revenue Forecasting ---")
    fc = forecast_revenue(3)
    print(f"[+] Forecast returned {len(fc)} months of predictions.")
    for f in fc:
        print(f"  * Month: {f['month']} - Predicted Revenue: ${f['forecast']:.2f}")
        
    if len(fc) < 3:
        print("[-] Error: Forecasting did not return at least 3 months.")
        sys.exit(1)
        
    # 4. Assistant routing check
    print("\n--- Testing AI Assistant Chat (Mock Mode) ---")
    queries = [
        "How much fee is pending?",
        "Which class has the highest outstanding amount?",
        "Any unusual expenses this week?"
    ]
    
    for q in queries:
        print(f"\nUser: \"{q}\"")
        res = run_assistant_query(q)
        print(f"Assistant: {res['response']}")
        print(f"Tool Executed: {res['tool_calls'][0]['name'] if res['tool_calls'] else 'none'}")
        
    print("\n[+] Verification successful! Backend is ready for hackathon deployment.")

if __name__ == "__main__":
    verify()
