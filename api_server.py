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

  #once you save the above code, you should run
  #uvicorn api_server:app --reload in below terminal
  #Now Test Your POST /transfer Endpoint in Chrome http://localhost:8000/docs
  #Swagger will open & you see POST /transfer, click on it
  #Click try it out in the json {"sender": "Pravin","usd_amount": 100,"pin": 9999}
  #Try the same json with currect PIN 1234
  #you will see Server responses
   
 

