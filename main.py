from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import google.generativeai as genai
from supabase import create_client, Client
import pypdf
import io

# 1. एनवायरनमेंट वेरिएबल्स लोड करना
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Supabase का कनेक्शन सेटअप
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

class TenderData(BaseModel):
    tender_id: str
    item_name: str
    tender_value: str
    eligibility_criteria: str
    our_company_profile: str

@app.get("/")
def home():
    return {"message": "TenderPilot AI Engine with PDF & Supabase is Running!"}

# 2. JSON Data Filter + Database Storage Endpoint
@app.post("/filter-tender")
def filter_tender(tender: TenderData):
    print(f"🚀 Analyzing Tender: {tender.tender_id}...")
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""
    Tum ek expert Government Tender Analyst ho. 
    Neeche ek GeM tender ki details aur hamari company ki profile di gayi hai.
    Tumhe analyse karke batana hai ki kya humein is tender mein apply karna chahiye ya nahi? 
    Jawab sirf 2 line mein do:
    Pehli line: 'Decision: YES' ya 'Decision: NO'
    Doosri line: 'Reason: [Yahan apna 1 line ka kaaran likho]'

    -- Tender Details --
    Tender ID: {tender.tender_id}
    Item: {tender.item_name}
    Value: {tender.tender_value}
    Eligibility Requirement: {tender.eligibility_criteria}
    
    -- Our Company Profile --
    {tender.our_company_profile}
    """
    
    response = model.generate_content(prompt)
    ai_result = response.text
    print("✅ AI Analysis Complete!")
    
    # डेटा को Supabase डेटाबेस में सेव करना
    try:
        data_to_save = {
            "tender_id": tender.tender_id,
            "item_name": tender.item_name,
            "ai_decision": ai_result
        }
        supabase.table("tenders").insert(data_to_save).execute()
        print("💾 Tender saved to Supabase Database successfully!")
    except Exception as e:
        print(f"⚠️ Database Error: {e}")
    
    return {
        "tender_id": tender.tender_id,
        "ai_decision": ai_result,
        "database_status": "Saved successfully!"
    }

# 3. PDF Upload & AI Analysis Endpoint
@app.post("/upload-tender-pdf")
async def upload_tender_pdf(file: UploadFile = File(...)):
    print(f"📄 Processing PDF File: {file.filename}")
    
    # PDF se text extract karna
    contents = await file.read()
    pdf_reader = pypdf.PdfReader(io.BytesIO(contents))
    extracted_text = ""
    for page in pdf_reader.pages:
        extracted_text += page.extract_text() or ""
        
    # Gemini AI se PDF text analyze karvana
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    Tum ek expert Government Tender Analyst ho. 
    Neeche ek GeM tender document ka extracted text diya gaya hai.
    Ise padh kar batao ki kya humein is tender mein apply karna chahiye ya nahi?
    Jawab sirf 2 line mein do:
    Pehli line: 'Decision: YES' ya 'Decision: NO'
    Doosri line: 'Reason: [Yahan apna 1 line ka kaaran likho]'

    -- Tender Document Text --
    {extracted_text[:4000]}
    """
    
    response = model.generate_content(prompt)
    ai_result = response.text
    
    # Supabase mein save karna
    try:
        data_to_save = {
            "tender_id": file.filename,
            "item_name": "PDF Tender Document",
            "ai_decision": ai_result
        }
        supabase.table("tenders").insert(data_to_save).execute()
        print("💾 PDF Tender saved to Supabase successfully!")
    except Exception as e:
        print(f"⚠️ Database Error: {e}")
        
    return {
        "filename": file.filename,
        "ai_decision": ai_result,
        "database_status": "PDF Processed & Saved successfully!"
    }