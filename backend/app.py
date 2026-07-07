import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from database import get_db_connection, init_db, sync_expense_to_transaction
from ocr_engine import process_receipt
from ml_engine import detect_anomalies, forecast_revenue
from assistant import run_assistant_query

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure database is initialized
init_db()

# Serve uploaded receipt images
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# 1. Login Endpoint (Mock Role Selector)
@app.route("/api/login", methods=["POST"])
def login():
    data = request.json or {}
    role = data.get("role", "teacher")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM User WHERE role = ? LIMIT 1;", (role,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({
            "success": True,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "role": user["role"]
            }
        })
    return jsonify({"success": False, "error": "Role not found"}), 404

# 2. Dashboard Stats Summary
@app.route("/api/dashboard/stats", methods=["GET"])
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total Revenue Fee collections (fee_in)
    cursor.execute("SELECT SUM(amount) as total FROM TransactionRecord WHERE type = 'fee_in';")
    total_revenue = cursor.fetchone()["total"] or 0.0
    
    # Total Expenses (expense_out)
    cursor.execute("SELECT SUM(amount) as total FROM TransactionRecord WHERE type = 'expense_out';")
    total_expenses = cursor.fetchone()["total"] or 0.0
    
    # Outstanding fees
    cursor.execute("SELECT SUM(amount_due - amount_paid) as pending FROM FeeRecord;")
    pending_fees = cursor.fetchone()["pending"] or 0.0
    
    conn.close()
    
    return jsonify({
        "total_revenue": round(total_revenue, 2),
        "total_expenses": round(total_expenses, 2),
        "net_balance": round(total_revenue - total_expenses, 2),
        "pending_fees": round(pending_fees, 2)
    })

# 3. Dashboard Chart Data
@app.route("/api/dashboard/charts", methods=["GET"])
def get_charts():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Monthly revenue vs expenses (past 12 months)
    # Get last 12 active months
    cursor.execute("""
        SELECT strftime('%Y-%m', date) as month_str,
               SUM(CASE WHEN type = 'fee_in' THEN amount ELSE 0 END) as revenue,
               SUM(CASE WHEN type = 'expense_out' THEN amount ELSE 0 END) as expenses
        FROM TransactionRecord
        GROUP BY month_str
        ORDER BY month_str ASC;
    """)
    monthly_rows = cursor.fetchall()
    
    monthly_trend = []
    for r in monthly_rows:
        monthly_trend.append({
            "month": r["month_str"],
            "revenue": round(r["revenue"], 2),
            "expenses": round(r["expenses"], 2)
        })
        
    # Take last 12 items for visual space
    monthly_trend = monthly_trend[-12:]
    
    # 2. Fee collection rate by class (bar chart)
    cursor.execute("""
        SELECT Student.class, SUM(FeeRecord.amount_due) as total_due, SUM(FeeRecord.amount_paid) as total_paid
        FROM FeeRecord
        JOIN Student ON FeeRecord.student_id = Student.id
        GROUP BY Student.class;
    """)
    class_rows = cursor.fetchall()
    class_rates = []
    for r in class_rows:
        due = r["total_due"] or 1.0
        paid = r["total_paid"] or 0.0
        rate = (paid / due) * 100
        class_rates.append({
            "class": r["class"],
            "rate": round(rate, 1),
            "paid": round(paid, 2),
            "due": round(due, 2)
        })
        
    # 3. Expense breakdown by category (pie chart)
    cursor.execute("""
        SELECT category, SUM(amount) as total
        FROM TransactionRecord
        WHERE type = 'expense_out'
        GROUP BY category;
    """)
    cat_rows = cursor.fetchall()
    expense_breakdown = [{"category": r["category"], "value": round(r["total"], 2)} for r in cat_rows]
    
    conn.close()
    
    return jsonify({
        "monthly_trend": monthly_trend,
        "class_rates": class_rates,
        "expense_breakdown": expense_breakdown
    })

# 4. Forecast Endpoint
@app.route("/api/dashboard/forecast", methods=["GET"])
def get_forecast():
    # Predict next 3 months
    forecast = forecast_revenue(3)
    return jsonify(forecast)

# 5. Anomalies Endpoint
@app.route("/api/dashboard/anomalies", methods=["GET"])
def get_anomalies():
    # Detect outliers using Isolation Forest/statistical fallbacks
    anoms = detect_anomalies()
    return jsonify(anoms)

# 6. Expenses Submission (OCR pipeline)
@app.route("/api/expenses/upload", methods=["POST"])
def upload_expense():
    if "receipt" not in request.files:
        return jsonify({"success": False, "error": "No receipt file uploaded"}), 400
        
    file = request.files["receipt"]
    submitted_by = request.form.get("submitted_by", "Sarah Jenkins")
    
    if file.filename == "":
        return jsonify({"success": False, "error": "Empty filename"}), 400
        
    # Save original receipt
    filename = file.filename
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)
    
    # Execute OCR Pipeline
    api_key = os.getenv("ANTHROPIC_API_KEY")
    ocr_data = process_receipt(file_path, api_key=api_key)
    
    # Add prep prefix path if preprocessed image exists
    prep_filename = "prep_" + filename
    prep_path = os.path.join(app.config["UPLOAD_FOLDER"], prep_filename)
    has_preprocessed = os.path.exists(prep_path)
    
    # Store pending expense record in DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ExpenseRecord (submitted_by, category, amount, date, receipt_image_path, status, approver_id, ocr_extracted_json)
        VALUES (?, ?, ?, ?, ?, 'pending', NULL, ?);
    """, (
        submitted_by,
        ocr_data["category_guess"],
        ocr_data["amount"],
        ocr_data["date"],
        f"/uploads/{prep_filename if has_preprocessed else filename}",
        json.dumps(ocr_data)
    ))
    expense_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "expense": {
            "id": expense_id,
            "submitted_by": submitted_by,
            "category": ocr_data["category_guess"],
            "amount": ocr_data["amount"],
            "date": ocr_data["date"],
            "receipt_image_path": f"/uploads/{prep_filename if has_preprocessed else filename}",
            "raw_text": ocr_data.get("raw_text", ""),
            "extracted_via": ocr_data.get("extracted_via", "fallback")
        }
    })

# 7. Approvals Endpoint
@app.route("/api/expenses/pending", methods=["GET"])
def get_pending_expenses():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ExpenseRecord WHERE status = 'pending';")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route("/api/expenses/approve", methods=["POST"])
def approve_expense():
    data = request.json or {}
    expense_id = data.get("expense_id")
    action = data.get("action")  # 'approved' or 'rejected'
    approver_id = data.get("approver_id", 2)
    
    # Optional edited values
    category = data.get("category")
    amount = data.get("amount")
    date = data.get("date")
    
    if not expense_id or action not in ["approved", "rejected"]:
        return jsonify({"success": False, "error": "Invalid request parameters"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if action == "approved":
        # HOD might have edited fields before approving to fix OCR errors
        if category and amount is not None and date:
            cursor.execute("""
                UPDATE ExpenseRecord 
                SET status = 'approved', approver_id = ?, category = ?, amount = ?, date = ?
                WHERE id = ?;
            """, (approver_id, category, float(amount), date, expense_id))
        else:
            cursor.execute("""
                UPDATE ExpenseRecord 
                SET status = 'approved', approver_id = ?
                WHERE id = ?;
            """, (approver_id, expense_id))
        conn.commit()
        conn.close()
        
        # Sync to ledger (TransactionRecord)
        sync_expense_to_transaction(expense_id)
    else:
        cursor.execute("UPDATE ExpenseRecord SET status = 'rejected', approver_id = ? WHERE id = ?;", (approver_id, expense_id))
        conn.commit()
        conn.close()
        
    return jsonify({"success": True, "message": f"Expense {action} successfully"})

# 8. Assistant Query Chat Endpoint
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json or {}
    query = data.get("query", "")
    
    if not query.strip():
        return jsonify({"error": "Empty query"}), 400
        
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    result = run_assistant_query(query, api_key=api_key)
    
    return jsonify(result)

if __name__ == "__main__":
    # Run server on environment port or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
