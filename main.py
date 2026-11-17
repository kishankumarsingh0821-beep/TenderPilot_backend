import os
from fastapi import FastAPI, UploadFile, File
from dotenv import load_dotenv
from google import genai  # <-- Naya SDK import

load_dotenv()

# Gemini API configuration using new google-genai client
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)  # <-- Naya client initialization jo AQ... tokens ko support karta hai

app = FastAPI()

@app.get("/")
def home():
    return {"message": "TenderPilot AI Engine is Running!"}

@app.post("/upload-tender-pdf")
async def upload_tender_pdf(file: UploadFile = File(...)):
    try:
        print(f"📄 Processing PDF File: {file.filename}")
        contents = await file.read()
        
        # Model call karne ke liye naya syntax:
        # response = client.models.generate_content(
        #     model='gemini-1.5-flash',
        #     contents=['Analyze this tender document:', contents]
        # )
        
        return {"filename": file.filename, "status": "Success"}
    except Exception as e:
        return {"error": str(e)}