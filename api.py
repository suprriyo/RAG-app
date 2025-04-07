from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sentence_transformers import SentenceTransformer, util
import json

app = FastAPI(title="SHL Assessment Recommender API")

# CORS setup (optional, allows access from frontend apps like Streamlit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load data
with open("assessments.json", "r", encoding="utf-8") as f:
    assessments = json.load(f)

# Prepare corpus and embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")
corpus = [a["name"] + " " + a.get("test_type", "") for a in assessments]
corpus_embeddings = model.encode(corpus, convert_to_tensor=True)

@app.get("/recommend")
async def recommend(q: str = Query(..., description="Job description or query text")):
    query_embedding = model.encode(q, convert_to_tensor=True)
    scores = util.cos_sim(query_embedding, corpus_embeddings)[0]

    top_k = scores.argsort(descending=True)[:10]
    results = [assessments[i] for i in top_k]

    return JSONResponse(content=results)
