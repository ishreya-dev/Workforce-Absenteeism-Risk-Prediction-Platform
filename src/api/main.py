"""
FastAPI scoring service for the Absenteeism Risk model.
Loads the trained AbsenteeismModel once at startup and exposes
a single /predict endpoint for scoring new records.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from model.absenteeism_model import AbsenteeismModel

app = FastAPI(
    title="Absenteeism Risk Scoring API",
    description="Predicts excessive absenteeism risk from workforce attendance features.",
    version="1.0.0"
)

# Resolve paths relative to this file, so it works regardless of where uvicorn is launched from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE_DIR, "models", "model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "models", "scaler.pkl")

scorer = AbsenteeismModel(model_path=MODEL_PATH, scaler_path=SCALER_PATH)


class AbsenteeismFeatures(BaseModel):
    reason_1: float
    reason_2: float
    reason_3: float
    reason_4: float
    month_value: float
    day_of_week: float
    transportation_expense: float
    distance_to_work: float
    age: float
    daily_work_load_average: float
    body_mass_index: float
    education_binary: float
    children: float
    pets: float


@app.get("/")
def root():
    return {"status": "ok", "service": "absenteeism-risk-scoring-api"}


@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": scorer.model is not None}


@app.post("/predict")
def predict(features: AbsenteeismFeatures):
    try:
        result = scorer.predict_single(features.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))