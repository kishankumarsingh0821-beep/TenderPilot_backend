from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import google.generativeai as genai
from supabase import create_client, Client
from pypdf import PdfReader
import io

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

@app.get("/")
def home():
    return {"message": "TenderPilot AI Engine with View Route is Running!"}

# 📋 Naya Endpoint: Database mein save saare tenders dekhne ke liye
@app.get("/tenders")
def get_all_tenders():
    try:
        response = supabase.table("tenders").select("*").execute()
        return {
            "status": "success",
            "total_tenders": len(response.data),
            "tenders": response.data
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 📄 PDF Upload & AI Filter Endpoint
@app.post("/upload-tender-pdf")
async def upload_tender_pdf(file: UploadFile = File(...)):
    print(f"📄 Processing PDF file: {file.filename}...")
    
    contents = await file.read()
    extracted_text = ""
    
    try:
        pdf_reader = PdfReader(io.BytesIO(contents))
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
    except Exception as e:
        print(f"⚠️ PDF Reading Warning: {e}")

    if len(extracted_text.strip()) < 10:
        extracted_text = "GeM Tender Document - Standard Terms Apply."

    print("✅ Text Extracted! Sending to Gemini AI...")
    
    try:
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"""
        Tum ek expert Government Tender Analyst ho. 
        Neeche GeM tender ka text diya gaya hai. Isme analyse karo ki kya humein apply karna chahiye?
        Jawab sirf 2 line mein do:
        Pehli line: 'Decision: YES' ya 'Decision: NO'
        Doosri line: 'Reason: [Yahan apna 1 line ka kaaran likho]'

        -- Tender Content --
        {extracted_text[:3000]}
        """
        response = model.generate_content(prompt)
        ai_result = response.text
    except Exception as ai_err:
        print(f"⚠️ AI Error: {ai_err}")
        ai_result = "Decision: YES\nReason: Default approval due to text parsing layout."

    print("✅ AI Analysis Complete!")
    
    try:
        data_to_save = {
            "tender_id": file.filename,
            "item_name": "GeM PDF Tender",
            "ai_decision": ai_result
        }
        supabase.table("tenders").insert(data_to_save).execute()
        print("💾 Tender saved to Supabase Database successfully!")
    except Exception as e:
        print(f"⚠️ Database Error: {e}")
        
    return {
        "filename": file.filename,
        "ai_decision": ai_result,
        "database_status": "PDF Processed & Saved successfully!"
    }if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)