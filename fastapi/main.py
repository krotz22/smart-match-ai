from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os
from dotenv import load_dotenv
from pymongo.server_api import ServerApi
# Import your modules
from match import smart_match, format_jd_for_llm, format_resume_for_llm
from parser import parse_resume_with_llm_binary

load_dotenv()

app = FastAPI(title="AI Recruiter API", version="1.0.0")

# Environment validation
MONGO_URL = os.getenv("MONGO_URL")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Validate required environment variables
if not MONGO_URL:
    print("❌ ERROR: MONGO_URL environment variable is not set!")
    raise ValueError("MONGO_URL environment variable is required")

if not MISTRAL_API_KEY:
    print("❌ ERROR: MISTRAL_API_KEY environment variable is not set!")
    raise ValueError("MISTRAL_API_KEY environment variable is required")

print("✅ Environment variables validated successfully")
print(f"✅ MONGO_URL configured: {MONGO_URL[:20]}...")
print(f"✅ MISTRAL_API_KEY configured: {'*' * len(MISTRAL_API_KEY) if MISTRAL_API_KEY else 'NOT SET'}")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
client = MongoClient(MONGO_URL)
db = client["test"]
resume_collection = db["resumes"]
job_collection = db["jobs"]
shortlist_collection = db["shortlists"]
print(f"✅ MongoDB connected to database: {db.name}")

def serialize_doc(doc):
    """Convert MongoDB document to JSON serializable format"""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

def serialize_docs(docs):
    """Convert list of MongoDB documents to JSON serializable format"""
    return [serialize_doc(doc) for doc in docs]

@app.get("/")
async def root():
    return {"message": "AI Recruiter API is running"}

@app.post("/match/{job_code}")
async def match_job(job_code: str):
    """Match candidates with a specific job"""
    try:
        # Find job by job code
        job = job_collection.find_one({"jobCode": job_code})
        print(job)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Format job description
        jd_text = format_jd_for_llm(job)
        
        # Get all resumes for this job
        resumes = list(resume_collection.find({"jobCode": job_code}))
        
        if not resumes:
            return {"results": [], "message": "No resumes found for this job"}

        results = []
        
        for resume_doc in resumes:
            try:
                # Get binary data
                binary_data = resume_doc.get("fileData")
                if not binary_data:
                    print(f"❌ No file data found for resume {resume_doc.get('_id')}")
                    continue
                
                print(f"🔄 Processing resume {resume_doc.get('_id')}...")
                
                # Parse resume
                resume_data = parse_resume_with_llm_binary(binary_data)
                print(f"✅ Resume parsed successfully: {resume_data.get('Full Name', 'N/A')}")
                
                resume_text = format_resume_for_llm(resume_data)

                # Perform matching
                print(f"🔄 Performing smart match...")
                match = smart_match(jd_text, resume_text, threshold=60)
                print(f"✅ Match completed with score: {match.get('match_score', 0)}")

                # Create shortlist entry
                entry = {
                    "candidateName": resume_data.get("Full Name", "N/A"),
                    "email": resume_data.get("Contact Information", {}).get("email", "N/A") if isinstance(resume_data.get("Contact Information"), dict) else "N/A",
                    "resumeId": str(resume_doc["_id"]),
                    "jobCode": job_code,
                    "score": match.get("match_score", 0),
                    "matchedSkills": match.get("matched_skills", []),
                    "missingSkills": match.get("missing_skills", []),
                    "summary": match.get("summary", "Could not generate summary."),
                    "shortlist": match.get("shortlist", False),
                    "dateShortlisted": datetime.utcnow()
                }

                # Insert into shortlist collection
                inserted = shortlist_collection.insert_one(entry)
                entry["_id"] = str(inserted.inserted_id)
                
                results.append(entry)
                
            except Exception as e:
                print(f"❌ Error processing resume {resume_doc.get('_id')}: {e}")
                print(f"❌ Error type: {type(e).__name__}")
                # Create a default entry for failed resumes to help with debugging
                failed_entry = {
                    "candidateName": "Processing Failed",
                    "email": "N/A",
                    "resumeId": str(resume_doc["_id"]),
                    "jobCode": job_code,
                    "score": 0,
                    "matchedSkills": [],
                    "missingSkills": [],
                    "summary": f"Processing failed: {str(e)}",
                    "shortlist": False,
                    "dateShortlisted": datetime.utcnow()
                }
                
                # Insert failed entry for debugging
                inserted = shortlist_collection.insert_one(failed_entry)
                failed_entry["_id"] = str(inserted.inserted_id)
                results.append(failed_entry)
                continue

        return jsonable_encoder({"results": results, "total": len(results)})
        
    except Exception as e:
        print(f"Error in match_job: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/shortlist/{job_code}")
async def get_shortlist(job_code: str):
    """Get shortlisted candidates for a job"""
    try:
        # Get shortlisted candidates
        data = list(shortlist_collection.find({"jobCode": job_code}))
        
        # Serialize documents
        serialized_data = serialize_docs(data)
        
        return jsonable_encoder({
            "shortlist": serialized_data,
            "total": len(serialized_data)
        })
        
    except Exception as e:
        print(f"Error in get_shortlist: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/jobs")
async def get_jobs():
    """Get all jobs"""
    try:
        jobs = list(job_collection.find())
        return jsonable_encoder({"jobs": serialize_docs(jobs)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/resumes/{job_code}")
async def get_resumes(job_code: str):
    """Get all resumes for a job"""
    try:
        resumes = list(resume_collection.find({"jobCode": job_code}, {"fileData": 0}))  # Exclude binary data
        return jsonable_encoder({"resumes": serialize_docs(resumes)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
print("Searching for job code ML2024 in jobs collection...")
job = job_collection.find_one({"jobCode": "ML2024"})
print("Found job:", job)
jobs = list(job_collection.find())
print("All jobs in jobs collection:", jobs)
print("Connected to DB:", db.name)
print("Sample job document:", job_collection.find_one())
print(client.list_database_names())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
