from fastapi import FastAPI
from pydantic import BaseModel
from db import db_query
from llm import ask_llm

app = FastAPI()

class ChatRequest(BaseModel):
    employee_code: str
    message: str

@app.post("/chat")
def chat(req: ChatRequest):

    msg = req.message.lower()
    code = req.employee_code

    db_context = ""

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
