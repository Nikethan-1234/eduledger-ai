import os
import json
import sqlite3
from datetime import datetime, timedelta
import anthropic
from database import get_db_connection
from ml_engine import detect_anomalies, forecast_revenue

# ==========================================
# 1. TOOL / DATABASE QUERY FUNCTIONS
# ==========================================

def get_pending_fees(class_name=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if class_name:
        cursor.execute("""
            SELECT SUM(amount_due - amount_paid) as pending
            FROM FeeRecord
            JOIN Student ON FeeRecord.student_id = Student.id
            WHERE Student.class = ? AND FeeRecord.status != 'paid';
        """, (class_name,))
        pending = cursor.fetchone()["pending"] or 0.0
        result = {"class": class_name, "pending_fees": round(pending, 2)}
    else:
        cursor.execute("SELECT SUM(amount_due - amount_paid) as pending FROM FeeRecord WHERE status != 'paid';")
        pending = cursor.fetchone()["pending"] or 0.0
        
        # Also get class breakdown
        cursor.execute("""
            SELECT Student.class, SUM(amount_due - amount_paid) as pending
            FROM FeeRecord
            JOIN Student ON FeeRecord.student_id = Student.id
            WHERE FeeRecord.status != 'paid'
            GROUP BY Student.class;
        """)
        breakdown = {row["class"]: round(row["pending"], 2) for row in cursor.fetchall()}
        result = {"total_pending_fees": round(pending, 2), "class_breakdown": breakdown}
        
    conn.close()
    return result

def get_todays_collections():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # We will use the latest transaction date in our database since "today" in real-time might have no transactions
    # Find the maximum date of fee_in transactions
    cursor.execute("SELECT MAX(date) as max_date FROM TransactionRecord WHERE type = 'fee_in';")
    latest_date_row = cursor.fetchone()
    
    if latest_date_row and latest_date_row["max_date"]:
        latest_date = latest_date_row["max_date"]
        cursor.execute("""
            SELECT SUM(amount) as total, COUNT(*) as count
            FROM TransactionRecord
            WHERE type = 'fee_in' AND date = ?;
        """, (latest_date,))
        row = cursor.fetchone()
        total = row["total"] or 0.0
        count = row["count"] or 0
        
        # Details
        cursor.execute("""
            SELECT category, amount FROM TransactionRecord 
            WHERE type = 'fee_in' AND date = ?;
        """, (latest_date,))
        details = [dict(r) for r in cursor.fetchall()]
        
        result = {
            "date": latest_date,
            "total_collected": round(total, 2),
            "payment_count": count,
            "details": details
        }
    else:
        result = {"date": datetime.now().strftime("%Y-%m-%d"), "total_collected": 0.0, "payment_count": 0, "details": []}
        
    conn.close()
    return result

def get_outstanding_by_class():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT Student.class, SUM(amount_due) as total_due, SUM(amount_paid) as total_paid,
               SUM(amount_due - amount_paid) as outstanding
        FROM FeeRecord
        JOIN Student ON FeeRecord.student_id = Student.id
        GROUP BY Student.class;
    """)
    rows = cursor.fetchall()
    
    breakdown = []
    max_outstanding_class = None
    max_outstanding_amt = -1.0
    
    for r in rows:
        out = round(r["outstanding"], 2)
        breakdown.append({
            "class": r["class"],
            "total_due": round(r["total_due"], 2),
            "total_paid": round(r["total_paid"], 2),
            "outstanding": out
        })
        if out > max_outstanding_amt:
            max_outstanding_amt = out
            max_outstanding_class = r["class"]
            
    conn.close()
    return {
        "highest_outstanding_class": max_outstanding_class,
        "highest_outstanding_amount": max_outstanding_amt,
        "classes": breakdown
    }

def get_flagged_anomalies(period="all"):
    # period can be 'week', 'month', 'all'
    anoms = detect_anomalies()
    flagged = [a for a in anoms if a["is_anomaly"]]
    
    # Filter by date if period is week/month
    # Find latest expense date in the db
    if flagged and period in ["week", "month"]:
        dates = [datetime.strptime(a["date"], "%Y-%m-%d") for a in flagged]
        latest_date = max(dates)
        
        filtered = []
        for a in flagged:
            d = datetime.strptime(a["date"], "%Y-%m-%d")
            delta = latest_date - d
            if period == "week" and delta.days <= 7:
                filtered.append(a)
            elif period == "month" and delta.days <= 30:
                filtered.append(a)
        flagged = filtered
        
    return {
        "period": period,
        "anomaly_count": len(flagged),
        "anomalies": flagged
    }

def forecast_revenue_assistant(months_ahead=3):
    forecast = forecast_revenue(months_ahead)
    return {
        "months_ahead": months_ahead,
        "forecast": forecast
    }

# ==========================================
# 2. CLAUDE INTERACTION / MOCK AGENT
# ==========================================

CLAUDE_TOOLS = [
    {
        "name": "get_pending_fees",
        "description": "Get the total amount of outstanding/pending school fees. Can optionally filter by class.",
        "input_schema": {
            "type": "object",
            "properties": {
                "class_name": {
                    "type": "string",
                    "description": "The specific class name to filter by (e.g., 'Grade 8', 'Grade 9', etc.)"
                }
            }
        }
    },
    {
        "name": "get_todays_collections",
        "description": "Get the details and sum of fees collected today (or on the latest day of transaction updates).",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_outstanding_by_class",
        "description": "Gets outstanding balance details grouped by class, including identifying which class has the highest outstanding amount.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_flagged_anomalies",
        "description": "Get the list of unusual/anomalous expenses flagged by the machine learning engine (Isolation Forest).",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["week", "month", "all"],
                    "description": "The time frame to check (default: 'all')",
                    "default": "all"
                }
            }
        }
    },
    {
        "name": "forecast_revenue",
        "description": "Predict future revenue for the next few months based on time-series historical data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "months_ahead": {
                    "type": "integer",
                    "description": "How many months into the future to predict (default: 3)",
                    "default": 3
                }
            }
        }
    }
]

def run_mock_assistant(query):
    # Perform regex/keyword routing to mock a conversational assistant
    query_lower = query.lower()
    
    # 1. Today's collections
    if any(w in query_lower for w in ["today", "collection", "collect today", "collections today"]):
        data = get_todays_collections()
        detail_txt = "\n".join([f"- {d['category']}: ${d['amount']:.2f}" for d in data["details"]])
        answer = (
            f"### Today's Fee Collections\n\n"
            f"On **{data['date']}**, we collected a total of **${data['total_collected']:.2f}** "
            f"across **{data['payment_count']}** transaction(s).\n\n"
            f"**Breakdown:**\n{detail_txt if detail_txt else '- No collections recorded for this date.'}"
        )
        return answer, "get_todays_collections", data
        
    # 2. Highest outstanding class
    elif any(w in query_lower for w in ["highest outstanding", "highest pending", "which class has the highest"]):
        data = get_outstanding_by_class()
        table_rows = "\n".join([f"| {c['class']} | ${c['total_due']:.2f} | ${c['total_paid']:.2f} | ${c['outstanding']:.2f} |" for c in data["classes"]])
        answer = (
            f"### Class Outstanding Fee Breakdown\n\n"
            f"The class with the highest outstanding amount is **{data['highest_outstanding_class']}** "
            f"with **${data['highest_outstanding_amount']:.2f}** pending.\n\n"
            f"| Class | Total Due | Total Paid | Outstanding Balance |\n"
            f"| :--- | :--- | :--- | :--- |\n"
            f"{table_rows}"
        )
        return answer, "get_outstanding_by_class", data
        
    # 3. Forecast
    elif any(w in query_lower for w in ["forecast", "predict", "future", "next month"]):
        data = forecast_revenue_assistant(3)
        forecast_rows = "\n".join([f"- **{f['month']}**: ${f['forecast']:.2f}" for f in data["forecast"]])
        answer = (
            f"### Revenue Forecast Summary\n\n"
            f"Based on our time-series forecasting model (historical fee cycles), here is the prediction for the next {data['months_ahead']} months:\n\n"
            f"{forecast_rows}\n\n"
            f"*Note: Spikes correspond to typical beginning-of-term fee payment schedules in January, May, and September.*"
        )
        return answer, "forecast_revenue", data
        
    # 4. Anomalies
    elif any(w in query_lower for w in ["anomaly", "unusual", "suspicious", "flagged", "strange"]):
        period = "week" if "week" in query_lower else ("month" if "month" in query_lower else "all")
        data = get_flagged_anomalies(period)
        
        if data["anomaly_count"] == 0:
            answer = f"No unusual/anomalous expenses were detected in the specified period ({period})."
        else:
            anom_list = []
            for a in data["anomalies"]:
                anom_list.append(
                    f"- **${a['amount']:.2f}** on *{a['date']}* for *{a['category']}* (submitted by {a['submitted_by']}).\n"
                    f"  *Reasoning*: `{a['explanation']}`"
                )
            anom_txt = "\n".join(anom_list)
            answer = (
                f"### Flagged Anomalies ({period.capitalize()})\n\n"
                f"Our Isolation Forest anomaly model has flagged **{data['anomaly_count']}** unusual expense(s):\n\n"
                f"{anom_txt}"
            )
        return answer, "get_flagged_anomalies", data
        
    # 5. General pending fees
    elif any(w in query_lower for w in ["fee", "pending", "outstanding", "due"]):
        # Check if class specified
        class_match = None
        for c in ["Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]:
            if c.lower() in query_lower:
                class_match = c
                break
                
        data = get_pending_fees(class_match)
        if class_match:
            answer = f"The total outstanding fee balance for **{class_match}** is **${data['pending_fees']:.2f}**."
        else:
            bd_txt = "\n".join([f"- **{k}**: ${v:.2f}" for k, v in data["class_breakdown"].items()])
            answer = (
                f"### Total Pending Fees\n\n"
                f"The school's total outstanding fee balance across all classes is **${data['total_pending_fees']:.2f}**.\n\n"
                f"**Class Breakdown:**\n{bd_txt}"
            )
        return answer, "get_pending_fees", data
        
    # 6. Default response
    else:
        answer = (
            "Hello! I am the EduLedger AI Financial Assistant.\n\n"
            "I can query school financial database tables for you. Try asking one of the following:\n"
            "- \"How much fee is pending?\"\n"
            "- \"Which class has the highest outstanding amount?\"\n"
            "- \"Show today's collections.\"\n"
            "- \"Predict this month's revenue.\"\n"
            "- \"Any unusual expenses this week?\""
        )
        return answer, "none", {}

def run_gemini_query(query, api_key):
    import urllib.request
    import urllib.parse
    import json

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    gemini_tools = {
        "function_declarations": [
            {
                "name": "get_pending_fees",
                "description": "Get the total amount of outstanding/pending school fees. Can optionally filter by class.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "class_name": {
                            "type": "STRING",
                            "description": "The specific class name to filter by (e.g., 'Grade 8', 'Grade 9', etc.)"
                        }
                    }
                }
            },
            {
                "name": "get_todays_collections",
                "description": "Get the details and sum of fees collected today (or on the latest day of transaction updates).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "get_outstanding_by_class",
                "description": "Gets outstanding balance details grouped by class, including identifying which class has the highest outstanding amount.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "get_flagged_anomalies",
                "description": "Get the list of unusual/anomalous expenses flagged by the machine learning engine (Isolation Forest).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "period": {
                            "type": "STRING",
                            "description": "The time frame to check (week, month, all)"
                        }
                    }
                }
            },
            {
                "name": "forecast_revenue",
                "description": "Predict future revenue for the next few months based on time-series historical data.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "months_ahead": {
                            "type": "INTEGER",
                            "description": "How many months into the future to predict (default: 3)"
                        }
                    }
                }
            }
        ]
    }
    
    system_instruction = {
        "parts": [{
            "text": (
                "You are the EduLedger AI Financial Assistant. You are connected to a school database. "
                "You must ONLY query the database using the tools provided. Do not write SQL or guess values. "
                "Analyze the tool outputs and explain them in friendly, plain natural language. "
                "Format your final answers cleanly in Markdown."
            )
        }]
    }

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": query}]
            }
        ],
        "tools": [gemini_tools],
        "systemInstruction": system_instruction
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    with urllib.request.urlopen(req) as response:
        resp_data = json.loads(response.read().decode("utf-8"))
        
    candidates = resp_data.get("candidates", [])
    if not candidates:
        return {"response": "Sorry, I couldn't generate a response.", "mock": False, "tool_calls": []}
        
    first_candidate = candidates[0]
    content = first_candidate.get("content", {})
    parts = content.get("parts", [])
    
    tool_calls_executed = []
    
    function_call = None
    for part in parts:
        if "functionCall" in part:
            function_call = part["functionCall"]
            break
            
    if function_call:
        tool_name = function_call["name"]
        # Gemini args might be a dict or missing
        tool_args = function_call.get("args", {})
        
        print(f"Gemini invoking tool: {tool_name} with args {tool_args}")
        
        if tool_name == "get_pending_fees":
            result = get_pending_fees(tool_args.get("class_name"))
        elif tool_name == "get_todays_collections":
            result = get_todays_collections()
        elif tool_name == "get_outstanding_by_class":
            result = get_outstanding_by_class()
        elif tool_name == "get_flagged_anomalies":
            result = get_flagged_anomalies(tool_args.get("period", "all"))
        elif tool_name == "forecast_revenue":
            # Convert float/string arguments if any
            months = 3
            if "months_ahead" in tool_args:
                try:
                    months = int(tool_args["months_ahead"])
                except Exception:
                    pass
            result = forecast_revenue_assistant(months)
        else:
            result = {"error": f"Tool {tool_name} not found"}
            
        tool_calls_executed.append({
            "name": tool_name,
            "args": tool_args,
            "result": result
        })
        
        second_turn_contents = [
            {
                "role": "user",
                "parts": [{"text": query}]
            },
            {
                "role": "model",
                "parts": [
                    {
                        "functionCall": function_call
                    }
                ]
            },
            {
                "role": "user",
                "parts": [
                    {
                        "functionResponse": {
                            "name": tool_name,
                            "response": {"result": result}
                        }
                    }
                ]
            }
        ]
        
        second_payload = {
            "contents": second_turn_contents,
            "tools": [gemini_tools],
            "systemInstruction": system_instruction
        }
        
        req2 = urllib.request.Request(
            url,
            data=json.dumps(second_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req2) as response2:
            resp_data2 = json.loads(response2.read().decode("utf-8"))
            
        final_candidates = resp_data2.get("candidates", [])
        if final_candidates:
            final_text = final_candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return {
                "response": final_text,
                "mock": False,
                "tool_calls": tool_calls_executed
            }
            
    text_parts = [p.get("text", "") for p in parts if "text" in p]
    return {
        "response": "".join(text_parts),
        "mock": False,
        "tool_calls": []
    }

def run_assistant_query(query, api_key=None):
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        # Fallback to custom Mock Agent
        print("No API Key found. Running Mock Assistant.")
        ans, tool, tool_data = run_mock_assistant(query)
        return {
            "response": ans,
            "mock": True,
            "tool_calls": [{"name": tool, "args": {}, "result": tool_data}] if tool != "none" else []
        }
        
    if api_key.startswith("AIzaSy"):
        try:
            print("Running Gemini Assistant...")
            return run_gemini_query(query, api_key)
        except Exception as e:
            print(f"Error in Gemini Assistant API: {e}. Falling back to Mock.")
            ans, tool, tool_data = run_mock_assistant(query)
            return {
                "response": f"*(Gemini API Error: {e}. Displaying offline assistant result)*\n\n{ans}",
                "mock": True,
                "tool_calls": [{"name": tool, "args": {}, "result": tool_data}] if tool != "none" else []
            }

    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        # Start message with tools enabled
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0.0,
            system=(
                "You are the EduLedger AI Financial Assistant. You are connected to a school database. "
                "You must ONLY query the database using the tools provided. Do not write SQL or guess values. "
                "Analyze the tool outputs and explain them in friendly, plain natural language. "
                "Format your final answers cleanly in Markdown."
            ),
            messages=[
                {"role": "user", "content": query}
            ],
            tools=CLAUDE_TOOLS
        )
        
        tool_calls_executed = []
        
        # Check if Claude wants to call a tool
        if response.stop_reason == "tool_use":
            tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
            
            message_history = [
                {"role": "user", "content": query},
                {"role": "assistant", "content": response.content}
            ]
            
            for tool_block in tool_use_blocks:
                tool_name = tool_block.name
                tool_args = tool_block.input
                tool_id = tool_block.id
                
                print(f"Claude invoking tool: {tool_name} with args {tool_args}")
                
                # Execute tool locally
                if tool_name == "get_pending_fees":
                    result = get_pending_fees(tool_args.get("class_name"))
                elif tool_name == "get_todays_collections":
                    result = get_todays_collections()
                elif tool_name == "get_outstanding_by_class":
                    result = get_outstanding_by_class()
                elif tool_name == "get_flagged_anomalies":
                    result = get_flagged_anomalies(tool_args.get("period", "all"))
                elif tool_name == "forecast_revenue":
                    result = forecast_revenue_assistant(tool_args.get("months_ahead", 3))
                else:
                    result = {"error": f"Tool {tool_name} not found"}
                    
                tool_calls_executed.append({
                    "name": tool_name,
                    "args": tool_args,
                    "result": result
                })
                
                # Append tool response
                message_history.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": json.dumps(result)
                        }
                    ]
                })
                
            # Call Claude back with tool results
            final_response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.0,
                messages=message_history,
                tools=CLAUDE_TOOLS
            )
            
            return {
                "response": final_response.content[0].text,
                "mock": False,
                "tool_calls": tool_calls_executed
            }
        else:
            # Claude answered directly without tools
            return {
                "response": response.content[0].text,
                "mock": False,
                "tool_calls": []
            }
            
    except Exception as e:
        print(f"Error in Claude Assistant API: {e}. Falling back to Mock.")
        ans, tool, tool_data = run_mock_assistant(query)
        return {
            "response": f"*(Claude API Error: {e}. Displaying offline assistant result)*\n\n{ans}",
            "mock": True,
            "tool_calls": [{"name": tool, "args": {}, "result": tool_data}] if tool != "none" else []
        }

if __name__ == "__main__":
    # Test Query
    print(run_assistant_query("How much fee is pending?"))
    print(run_assistant_query("Any unusual expenses this week?"))
