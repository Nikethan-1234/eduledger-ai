import os
import sqlite3
import random
from datetime import datetime, timedelta
from database import get_db_connection, init_db, DB_PATH

def seed_data():
    # Remove existing db if exists to start fresh
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except OSError:
            pass
            
    # Init schema
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Seed Students
    student_classes = ["Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]
    first_names = ["Liam", "Olivia", "Noah", "Emma", "Oliver", "Ava", "Elijah", "Charlotte", "William", "Sophia",
                   "James", "Amelia", "Benjamin", "Isabella", "Lucas", "Mia", "Henry", "Evelyn", "Alexander", "Harper"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
    
    students = []
    for i in range(100):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        cls = random.choice(student_classes)
        phone = f"+1 (555) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
        cursor.execute("INSERT INTO Student (name, class, guardian_contact) VALUES (?, ?, ?);", (name, cls, phone))
        students.append((cursor.lastrowid, cls))
        
    # 2. Seed FeeRecords and Fee Transactions
    # Terms: Term 1 (Jan 2025), Term 2 (May 2025), Term 3 (Sep 2025)
    terms_info = [
        {"term": "Term 1 2025", "due": "2025-01-15", "amount": 1200.0},
        {"term": "Term 2 2025", "due": "2025-05-15", "amount": 1250.0},
        {"term": "Term 3 2025", "due": "2025-09-15", "amount": 1250.0},
        {"term": "Term 1 2026", "due": "2026-01-15", "amount": 1300.0},
        {"term": "Term 2 2026", "due": "2026-05-15", "amount": 1350.0}
    ]
    
    for s_id, cls in students:
        for term_data in terms_info:
            # Randomize payment status
            rand_val = random.random()
            if rand_val < 0.85: # Paid
                status = "paid"
                amount_paid = term_data["amount"]
            elif rand_val < 0.95: # Partially paid
                status = "partially_paid"
                amount_paid = round(term_data["amount"] * random.uniform(0.3, 0.7), 2)
            else: # Unpaid
                status = "unpaid"
                amount_paid = 0.0
                
            cursor.execute("""
            INSERT INTO FeeRecord (student_id, term, amount_due, amount_paid, due_date, status)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (s_id, term_data["term"], term_data["amount"], amount_paid, term_data["due"], status))
            fee_id = cursor.lastrowid
            
            # Write fee payment transactions
            if amount_paid > 0:
                # Pay within 15 days before/after due date
                due_dt = datetime.strptime(term_data["due"], "%Y-%m-%d")
                pay_days_offset = random.randint(-15, 10)
                pay_date = (due_dt + timedelta(days=pay_days_offset)).strftime("%Y-%m-%d")
                
                category = f"Tuition Fee - {cls}"
                cursor.execute("""
                INSERT INTO TransactionRecord (type, amount, date, category, source_ref_id)
                VALUES ('fee_in', ?, ?, ?, ?);
                """, (amount_paid, pay_date, category, fee_id))
                
    # 3. Seed ExpenseRecords and Expense Transactions
    # Add a history of expenses for the last 18 months (Jan 2025 to June 2026)
    teachers = ["Sarah Jenkins", "Mr. Adams", "Mrs. Gable", "Ms. Collins"]
    expense_categories = ["Science Supplies", "Office Supplies", "Classroom Decor", "Software License", "Staff Utilities", "Athletics Equipment"]
    
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2026, 6, 30)
    current_dt = start_date
    
    expense_count = 0
    while current_dt <= end_date:
        # Generate 3-5 normal expenses per month
        num_expenses = random.randint(3, 5)
        for _ in range(num_expenses):
            # Normal expense
            sub_by = random.choice(teachers)
            cat = random.choice(expense_categories)
            
            # Typical amounts based on category
            if cat == "Science Supplies":
                amt = round(random.uniform(50, 250), 2)
            elif cat == "Office Supplies":
                amt = round(random.uniform(20, 100), 2)
            elif cat == "Classroom Decor":
                amt = round(random.uniform(30, 120), 2)
            elif cat == "Software License":
                amt = round(random.uniform(150, 400), 2)
            elif cat == "Staff Utilities":
                amt = round(random.uniform(80, 200), 2)
            else: # Athletics Equipment
                amt = round(random.uniform(100, 350), 2)
                
            # Random date within current month
            day = random.randint(1, 28)
            exp_date = datetime(current_dt.year, current_dt.month, day).strftime("%Y-%m-%d")
            
            # Status: 90% approved, 10% rejected/pending
            stat_rand = random.random()
            if stat_rand < 0.90:
                status = "approved"
                approver_id = 2 # Principal Marcus
            elif stat_rand < 0.95:
                status = "pending"
                approver_id = None
            else:
                status = "rejected"
                approver_id = 2
                
            cursor.execute("""
            INSERT INTO ExpenseRecord (submitted_by, category, amount, date, receipt_image_path, status, approver_id, ocr_extracted_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (sub_by, cat, amt, exp_date, f"/uploads/receipt_{expense_count}.png", status, approver_id, "{}"))
            expense_id = cursor.lastrowid
            expense_count += 1
            
            if status == "approved":
                cursor.execute("""
                INSERT INTO TransactionRecord (type, amount, date, category, source_ref_id)
                VALUES ('expense_out', ?, ?, ?, ?);
                """, (amt, exp_date, cat, expense_id))
                
        # Advance by 1 month
        if current_dt.month == 12:
            current_dt = datetime(current_dt.year + 1, 1, 1)
        else:
            current_dt = datetime(current_dt.year, current_dt.month + 1, 1)
            
    # 4. Inject 4 Deliberate Anomalies in the last 2 months (May and June 2026) for dashboard detection
    anomalies = [
        # Anomaly 1: Extremely high amount for Office Supplies
        {"submitted_by": "Sarah Jenkins", "category": "Office Supplies", "amount": 1450.00, "date": "2026-06-12", "status": "approved", "approver_id": 2},
        # Anomaly 2: Weird category for teacher submitter ("Athletics Equipment" but massive amount submitted by English Teacher Sarah)
        {"submitted_by": "Sarah Jenkins", "category": "Athletics Equipment", "amount": 920.00, "date": "2026-06-25", "status": "pending", "approver_id": None},
        # Anomaly 3: Weekend transaction in late June (Sunday expense submission for Staff Utilities)
        {"submitted_by": "Mr. Adams", "category": "Staff Utilities", "amount": 420.00, "date": "2026-06-28", "status": "approved", "approver_id": 2}, # June 28, 2026 is a Sunday
        # Anomaly 4: High amount outside of term dates (submitted in mid-July 2025 during summer holidays)
        {"submitted_by": "Mrs. Gable", "category": "Science Supplies", "amount": 890.00, "date": "2025-07-20", "status": "approved", "approver_id": 2}
    ]
    
    for anom in anomalies:
        cursor.execute("""
        INSERT INTO ExpenseRecord (submitted_by, category, amount, date, receipt_image_path, status, approver_id, ocr_extracted_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (anom["submitted_by"], anom["category"], anom["amount"], anom["date"], f"/uploads/receipt_{expense_count}.png", anom["status"], anom["approver_id"], "{}"))
        expense_id = cursor.lastrowid
        expense_count += 1
        
        if anom["status"] == "approved":
            cursor.execute("""
            INSERT INTO TransactionRecord (type, amount, date, category, source_ref_id)
            VALUES ('expense_out', ?, ?, ?, ?);
            """, (anom["amount"], anom["date"], anom["category"], expense_id))
            
    conn.commit()
    conn.close()
    print("Database seeded with synthetic data successfully.")

if __name__ == "__main__":
    seed_data()
