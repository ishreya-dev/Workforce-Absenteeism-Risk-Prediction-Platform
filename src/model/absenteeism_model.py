"""
Productionized scoring module for the Absenteeism Risk model.

Wraps the trained logistic regression and its scaler into a single
reusable class with a fit/transform-style interface. This is the
single source of truth for scoring logic — both the FastAPI service
and the Kafka consumer import and call this class rather than
duplicating preprocessing/prediction code.
"""

import pickle
import pandas as pd
import numpy as np

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from preprocessing.feature_config import FEATURE_COLUMNS


class AbsenteeismModel:
    """
    Loads a trained logistic regression model and its fitted StandardScaler,
    and scores new records that are already shaped like the BigQuery
    `absenteeism_cleaned` view (i.e. feature engineering already applied
    upstream in SQL).
    """

    def __init__(self, model_path: str, scaler_path: str):
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)
        self.feature_columns = FEATURE_COLUMNS

    def _validate_and_order(self, data: pd.DataFrame) -> pd.DataFrame:
        """Ensures incoming data has all required columns, in the correct order."""
        missing = set(self.feature_columns) - set(data.columns)
        if missing:
            raise ValueError(f"Missing required feature columns: {missing}")
        return data[self.feature_columns].astype(float)

    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """Returns binary predictions (0/1) for excessive_absenteeism."""
        X = self._validate_and_order(data)
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def predict_proba(self, data: pd.DataFrame) -> np.ndarray:
        """Returns predicted probability of excessive_absenteeism (class 1)."""
        X = self._validate_and_order(data)
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)[:, 1]

    def predict_single(self, record: dict) -> dict:
        """
        Convenience method for scoring a single record passed as a dict
        (e.g. from a FastAPI request body or a Kafka message payload).
        Returns a dict with both the binary prediction and the probability.
        """
        df = pd.DataFrame([record])
        prediction = int(self.predict(df)[0])
        probability = float(self.predict_proba(df)[0])
        return {
            "excessive_absenteeism_risk": prediction,
            "risk_probability": round(probability, 4)
        }