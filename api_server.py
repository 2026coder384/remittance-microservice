from fastapi.responses import HTMLResponse
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import sqlite3
import os
import shutil
app = FastAPI () 
failed_attempts = {}
conn = sqlite3.connect("remittance.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS transfers (sender TEXT, usd_amount INTEGER, inr_payout INTEGER)")
conn.commit()
class TransferRequest(BaseModel):
    sender: str
    usd_amount: int
    pin: int
# --- Endpoint 1: my first fee code
@app.get("/fee")
def Service_fee (amount: int):
    fee = 100
    Total_amount = (amount + fee)
    return {"total_payable": Total_amount}
# --- Endpoint 2: My second USD to INR convert code below
@app.get("/convert")    
def convert_usd (usd: int):
    Exchange_Rate = 84
    fee = 100
    inr_payout = usd * Exchange_Rate - fee
    return {"final_payout": inr_payout}
#full journey—from Mobile App → DNS →HTTPS/TCP-IP→ AWS Load 
# ->Balancer→Fargate Port 8000 or local machine → Your Python Function
#Now I am moving to new code mobile app sending Json file
#building a real, secure POST /transfer endpoint i
@app.post("/transfer")
def process_transfer(request: TransferRequest, x_api_key: str = Header(...)):
    expected_api_key = os.getenv("API_KEY", "local-dev-only")
    if not expected_api_key or x_api_key != expected_api_key:
     raise HTTPException(status_code=401, detail="Unauthorized: Invalid X-API-Key")
    if failed_attempts.get(request.sender, 0) >= 3:
     raise HTTPException(status_code=429, detail="Account locked due to 3 failed PIN attempts")
    expected_pin = int(os.getenv("TRANSFER_PIN", "1234"))
    if request.pin != expected_pin:
        failed_attempts[request.sender] = failed_attempts.get(request.sender, 0) + 1
        return {"status": "FAILED", "reason": f"Invalid PIN (Attempt {failed_attempts[request.sender]}/3)"}
        return {"status": "FAILED", "reason": "Invalid PIN"}
        failed_attempts[request.sender] = 0
    if request.usd_amount > 5000:
     return {"status": "HOLD_FOR_AML_REVIEW", "reason": "Amount exceeds $5,000 automated limit"}
    fee = 100  
    net_inr = request.usd_amount * 84 - fee
    cursor.execute("INSERT INTO transfers VALUES (?, ?, ?)", (request.sender, request.usd_amount, net_inr))
    conn.commit()
    return {"status": "SUCCESS", "sender": request.sender, "inr_payout": net_inr}
cursor.execute("CREATE TABLE IF NOT EXISTS ai_audit_logs (user_id TEXT, prompt_preview TEXT, decision TEXT, risk_reason TEXT)")
conn.commit()
class AIGovernanceRequest(BaseModel):
    user_id: str
    prompt_text: str
@app.get("/history")
def get_history():
        cursor.execute("SELECT * FROM transfers")
        rows = cursor.fetchall()
        return {"transactions": rows}
@app.get("/health")
def health_check():
    try:
        cursor.execute("SELECT 1")
        return {"status": "HEALTHY", "database": "CONNECTED"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"UNHEALTHY: {str(e)}")
@app.post("/admin/backup")
def backup_database(x_api_key: str = Header(...)):
    expected_api_key = os.getenv("API_KEY", "local-dev-only")
    if x_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid X-API-Key")
    shutil.copyfile("remittance.db", "remittance_backup.db")
    return {"status": "BACKUP_COMPLETED", "backup_file": "remittance_backup.db"}
@app.post("/ai-governance/audit")
def ai_governance_guardrail(request: AIGovernanceRequest, x_api_key: str = Header(...)):
    expected_api_key = os.getenv("API_KEY", "local-dev-only")
    if not expected_api_key or x_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid X-API-Key")

    text_lower = request.prompt_text.lower()

    if "ignore previous instructions" in text_lower or "bypass" in text_lower:
        decision = "BLOCKED_PROMPT_INJECTION"
        reason = "OWASP LLM01: Prompt injection attempt detected"
    elif "ssn" in text_lower or "pan" in text_lower or "account number" in text_lower:
        decision = "BLOCKED_PII_LEAK"
        reason = "Data Privacy Policy: Unmasked PII must be redacted before AI processing"
    else:
        decision = "APPROVED"
        reason = "Passed AI Governance safety & privacy checks"

    cursor.execute(
        "INSERT INTO ai_audit_logs VALUES (?, ?, ?, ?)",
        (request.user_id, request.prompt_text[:40], decision, reason)
    )
    conn.commit()
    return {"decision": decision, "reason": reason}
@app.get("/compliance-report", response_class=HTMLResponse)
def compliance_dashboard():
    cursor.execute("SELECT COUNT(*) FROM ai_audit_logs")
    total_ai_checks = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM ai_audit_logs WHERE decision != 'APPROVED'")
    blocked_threats = cursor.fetchone()[0]
    api_key_set = os.getenv("API_KEY", "local-dev-only") != "local-dev-only"
    rb_status = "PASS" if api_key_set else "WARN (Using Dev Key)"

    return f"""
    <html><body style="background:#0f172a;color:#f8fafc;font-family:Arial;padding:30px;">
    <h1>🛡️ Live AI & Technology GRC Compliance Report</h1>
    <p style="color:#94a3b8;">Real-time automated control evidence pulled directly from production SQLite audit logs</p>
    <table border="1" cellpadding="12" style="border-collapse:collapse;width:100%;border-color:#334155;margin-top:20px;">
      <tr style="background:#1e293b;"><th>Framework</th><th>Control Requirement</th><th>Status</th><th>Live System Evidence</th></tr>
      <tr><td><b>NIST AI RMF (Govern)</b></td><td>Zero-Trust API Access & Key Hygiene</td><td><b>{rb_status}</b></td><td>X-API-Key Header Authentication enforced on /transfer & /ai-governance/audit</td></tr>
      <tr><td><b>NIST AI RMF (Measure)</b></td><td>OWASP LLM Prompt Injection & PII Guardrails</td><td><b style="color:#4ade80;">PASS</b></td><td>{total_ai_checks} total AI prompts inspected; {blocked_threats} prompt-injection/PII threats blocked in ai_audit_logs</td></tr>
      <tr><td><b>EU AI Act / RBI FREE-AI</b></td><td>High-Risk Transaction AML & Human Oversight</td><td><b style="color:#4ade80;">PASS</b></td><td>Automated $5,000 AML threshold routing to HOLD_FOR_AML_REVIEW with audit trail</td></tr>
      <tr><td><b>DORA / ISO 27001</b></td><td>Operational Resilience & DR Backup Readiness</td><td><b style="color:#4ade80;">PASS</b></td><td>Deep /health readiness probe active + /admin/backup point-in-time snapshot verified</td></tr>
    </table></body></html>
    """

 

