import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Enable CORS so frontend index.html can talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini API configuration using new google-genai client
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

@app.get("/")
def home():
    return {"message": "TenderPilot AI Engine is Running!"}

@app.post("/upload-tender-pdf")
async def upload_tender_pdf(file: UploadFile = File(...)):
    try:
        print(f"📄 Processing PDF File: {file.filename}")
        contents = await file.read()
        
        # Call Gemini AI to analyze the PDF content
        response = client.models.generate_content(
            model='gemini-2.5-flash', # Aap gemini-1.5-flash bhi use kar sakte hain
            contents=[
                'Analyze this tender document and extract key details like title, closing date, and estimated budget in JSON format:',
                contents
            ]
        )
        
        return {
            "filename": file.filename,
            "status": "Success",
            "analysis": response.text
        }
    except Exception as e:
        return {"error": str(e)}