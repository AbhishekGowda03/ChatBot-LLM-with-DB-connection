from fastapi import FastAPI
from pydantic import BaseModel
from db import db_query
from llm import ask_llm
import re

app = FastAPI()

class ChatRequest(BaseModel):
    employee_code: str
    message: str

@app.post("/chat")
def chat(req: ChatRequest):

    msg = req.message.lower()
    code = req.employee_code

    db_context = ""
    if any(greet in msg for greet in ["hi", "hello", "hey"]):
        return {"response": "Hello! How can I help you today?"}

    if any(bye in msg for bye in ["bye", "goodbye", "see you"]):
        return {"response": "Goodbye! Take care!"}

    if any(thanks in msg for thanks in ["thank", "thanks"]):
        return {"response": "You’re welcome! Happy to assist 😊"}

    # employee personal info
    if "my details" in msg:
        data = db_query(f"""
            SELECT employee_code, name, department, email, joining_date
            FROM employees
            WHERE employee_code='{code}'
        """)
        db_context = f"Your info: {data}"

    # employee leave history
    elif "my leave" in msg or "my leaves" in msg:
        data = db_query(f"""
            SELECT l.leave_type, l.start_date, l.end_date, l.status
            FROM leaves l
            JOIN employees e ON e.id = l.employee_id
            WHERE e.employee_code='{code}'
        """)
        db_context = f"Your leave history: {data}"

    elif "apply" in msg and "leave" in msg:
        # extract leave type
        leave_types = ["sick", "annual", "casual", "medical"]

        leave_type = None
        for lt in leave_types:
            if lt in msg:
                leave_type = lt.capitalize() + " Leave"
                break

        # extract dates
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', req.message)

        if len(dates) == 2:
            start_date = dates[0]
            end_date = dates[1]
        else:
            return {"response": "Please provide start and end date in format YYYY-MM-DD."}

        # get employee_id
        emp = db_query(f"SELECT id FROM employees WHERE employee_code='{req.employee_code}'")

        if not emp:
            return {"response": "Employee not found."}

        emp_id = emp[0][0]

        # insert the leave request
        db_query(f"""
            INSERT INTO leaves (employee_id, leave_type, start_date, end_date, status)
            VALUES ({emp_id}, '{leave_type}', '{start_date}', '{end_date}', 'Pending')
        """)

        return {
            "response": f"Your {leave_type} request from {start_date} to {end_date} has been submitted for approval."}

    elif ("upcoming" in msg or "future" in msg or "planned" in msg) and "leave" in msg:
        # find employee id
        emp = db_query(f"SELECT id FROM employees WHERE employee_code='{req.employee_code}'")
        if not emp:
            return {"response": "Employee not found."}

        emp_id = emp[0][0]

        # get future leaves
        data = db_query(f"""
            SELECT leave_type, start_date, end_date, status
            FROM leaves
            WHERE employee_id={emp_id}
            AND start_date > CURRENT_DATE
            ORDER BY start_date ASC
        """)

        if not data:
            return {"response": "You have no upcoming leaves."}

        # format for LLM
        db_context = f"Upcoming leaves: {data}"

    elif ("leave balance" in msg) or ("remaining leaves" in msg) or ("how many leaves" in msg):
        # get employee id & default balance
        emp = db_query(f"SELECT id, annual_leave_balance FROM employees WHERE employee_code='{req.employee_code}'")
        if not emp:
            return {"response": "Employee not found."}

        emp_id = emp[0][0]
        total_allowed = emp[0][1]

        # count approved leave days
        leave_used_data = db_query(f"""
            SELECT COALESCE(SUM(end_date - start_date + 1),0)
            FROM leaves
            WHERE employee_id={emp_id} AND status='Approved'
        """)
        leave_used = leave_used_data[0][0]

        remaining = total_allowed - leave_used

        return {"response": f"You have {remaining} out of {total_allowed} annual leave days remaining."}

    else:
        return {"response": "You can ask: 'my details' | 'my leave'"}

    prompt = f"""
You are an employee assistant.
User asked: {req.message}
Data: {db_context}
Respond politely, briefly, and accurately.
"""
    reply = ask_llm(prompt)
    return {"response": reply}
