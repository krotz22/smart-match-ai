
from fastapi import FastAPI
from pymongo import MongoClient
from match import smart_match, format_jd_for_llm, format_resume_for_llm
from parser import parse_resume_with_llm_binary
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
client = MongoClient("mongodb://localhost:27017")
db = client["ai-recruiter"]
resume_collection = db["resumes"]
job_collection = db["jobs"]
shortlist_collection = db["shortlists"]

@app.post("/match/{job_code}")
def match_job(job_code: str):
    job = job_collection.find_one({"jobCode": job_code})
    if not job:
        return {"error": "Job not found"}

    jd_text = format_jd_for_llm(job)
    resumes = list(resume_collection.find({"jobCode": job_code}))

    results = []
    for res in resumes:
        binary_data = res.get("fileData")
        resume_data = parse_resume_with_llm_binary(binary_data)
        resume_text = format_resume_for_llm(resume_data)

        match = smart_match(jd_text, resume_text, threshold=60)

        entry = {
            "candidateName": resume_data.get("Full Name", "N/A"),
            "jobCode": job_code,
            "score": match.get("match_score", 0),
            "matchedSkills": match.get("matched_skills", []),
            "missingSkills": match.get("missing_skills", []),
            "summary": match.get("summary", "Could not parse result."),
            "shortlist": match.get("shortlist", False),
            "dateShortlisted": datetime.utcnow()
        }

        inserted = shortlist_collection.insert_one(entry)
        entry["_id"] = str(inserted.inserted_id)
        results.append(entry)

    return jsonable_encoder({"results": results})

@app.get("/shortlist/{job_code}")
def get_shortlist(job_code: str):
    data = list(shortlist_collection.find({"jobCode": job_code}))
    for item in data:
        item["_id"] = str(item["_id"])
    return jsonable_encoder(data)