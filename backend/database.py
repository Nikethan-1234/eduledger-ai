import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "school.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. User Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS User (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('teacher', 'approver', 'admin'))
    );
    """)
    
    # 2. Student Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Student (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        class TEXT NOT NULL,
        guardian_contact TEXT NOT NULL
    );
    """)
    
    # 3. FeeRecord Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS FeeRecord (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        term TEXT NOT NULL,
        amount_due REAL NOT NULL,
        amount_paid REAL NOT NULL DEFAULT 0.0,
        due_date TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('unpaid', 'partially_paid', 'paid')),
        FOREIGN KEY (student_id) REFERENCES Student (id)
    );
    """)
    
    # 4. ExpenseRecord Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ExpenseRecord (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submitted_by TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        receipt_image_path TEXT,
        status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
        approver_id INTEGER,
        ocr_extracted_json TEXT,
        FOREIGN KEY (approver_id) REFERENCES User (id)
    );
    """)
    
    # 5. Transaction Table (Shared spine)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TransactionRecord (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL CHECK(type IN ('fee_in', 'expense_out')),
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        category TEXT NOT NULL,
        source_ref_id INTEGER NOT NULL
    );
    """)
    
    # Create index for fast queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transaction_date ON TransactionRecord(date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transaction_type ON TransactionRecord(type);")
    
    # Insert Mock Users if none exist
    cursor.execute("SELECT COUNT(*) FROM User;")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO User (name, role) VALUES (?, ?);
        """, [
            ("Sarah Jenkins", "teacher"),
            ("Principal Marcus", "approver"),
            ("Admin Root", "admin")
        ])
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

# Helper to sync approved ExpenseRecord to TransactionRecord
def sync_expense_to_transaction(expense_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM ExpenseRecord WHERE id = ?;", (expense_id,))
    expense = cursor.fetchone()
    
    if expense and expense["status"] == "approved":
        # Check if already synced to avoid duplicates
        cursor.execute("SELECT COUNT(*) FROM TransactionRecord WHERE type = 'expense_out' AND source_ref_id = ?;", (expense_id,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            INSERT INTO TransactionRecord (type, amount, date, category, source_ref_id)
            VALUES ('expense_out', ?, ?, ?, ?);
            """, (expense["amount"], expense["date"], expense["category"], expense_id))
            conn.commit()
            
    conn.close()

# Helper to sync FeeRecord payment to TransactionRecord
def sync_fee_payment_to_transaction(fee_id, payment_amount, payment_date):
    if payment_amount <= 0:
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT FeeRecord.*, Student.name as student_name, Student.class as student_class 
    FROM FeeRecord 
    JOIN Student ON FeeRecord.student_id = Student.id 
    WHERE FeeRecord.id = ?;
    """, (fee_id,))
    fee = cursor.fetchone()
    
    if fee:
        # We record the transaction
        # The category will reflect fee income from class
        category = f"Tuition Fee - {fee['student_class']}"
        cursor.execute("""
        INSERT INTO TransactionRecord (type, amount, date, category, source_ref_id)
        VALUES ('fee_in', ?, ?, ?, ?);
        """, (payment_amount, payment_date, category, fee_id))
        conn.commit()
        
    conn.close()

if __name__ == "__main__":
    init_db()
