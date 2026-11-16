from fastapi import FastAPI, UploadFile, File
import os
from dotenv import load_dotenv
import google.generativeai as genai
import pypdf
import io

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

@app.get("/")
def home():
    return {"message": "TenderPilot AI Engine is Running!"}

@app.post("/upload-tender-pdf")
async def upload_tender_pdf(file: UploadFile = File(...)):
    try:
        print(f"📄 Processing PDF File: {file.filename}")
        contents = await file.read()
        
        # PDF se text extract karna
        pdf_reader = pypdf.PdfReader(io.BytesIO(contents))
        extracted_text = ""
        for page in pdf_reader.pages:
            extracted_text += page.extract_text() or ""
            
        if not extracted_text.strip():
            return {
                "filename": file.filename,
                "error": "PDF text is empty or it's a scanned image PDF. Please use a text-based PDF.",
                "status": "Failed"
            }
            
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
        return {
            "filename": file.filename,
            "ai_decision": response.text,
            "status": "Success"
        }
        
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
        return {
            "filename": file.filename,
            "error": str(e),
            "status": "Failed"
        }