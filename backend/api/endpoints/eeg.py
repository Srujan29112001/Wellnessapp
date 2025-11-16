"""
EEG Analysis Endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import pandas as pd
import io
import numpy as np

from backend.database.postgres import get_db
from backend.database.mongo import get_mongo_db
from backend.models.postgres_models import EEGAnalysis, User, MentalState
from ml.eeg_analysis.processor import EEGProcessor
from ml.eeg_analysis.classifier import EEGMentalStateClassifier

router = APIRouter()


# Schemas
class EEGAnalysisResponse(BaseModel):
    id: str
    user_id: str
    timestamp: datetime
    stress: float  # 0-1
    focus: float
    relaxation: float
    drowsiness: float
    dominant_band: str  # delta, theta, alpha, beta
    mental_state: str
    recommendations: List[str]


class EEGBandPowers(BaseModel):
    delta: float
    theta: float
    alpha: float
    beta: float
    gamma: Optional[float] = None


# Initialize EEG processor and classifier
eeg_processor = EEGProcessor(sample_rate=256, num_channels=14)
eeg_classifier = EEGMentalStateClassifier()


@router.post("/upload", response_model=EEGAnalysisResponse)
async def upload_eeg_data(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: str = "demo_user"
):
    """
    Upload and analyze EEG data file (CSV format expected)

    Expected CSV format:
    - Columns: channel1, channel2, ..., channel14
    - Sampling rate: 256 Hz
    """
    # Ensure user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(id=user_id, email=f"{user_id}@demo.com", name="Demo User")
        db.add(user)
        await db.flush()

    try:
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))

        # Convert to numpy array (assuming columns are channels)
        eeg_data = df.values.T  # Shape: (channels, samples)

        if eeg_data.shape[0] > eeg_processor.num_channels:
            eeg_data = eeg_data[:eeg_processor.num_channels, :]

        # Preprocess EEG data
        preprocessed = eeg_processor.preprocess(eeg_data)

        # Extract features
        features = eeg_processor.extract_features(preprocessed)

        # Classify mental state
        classification = eeg_classifier.predict(features)

        # Determine dominant mental state
        states = {
            'stress': classification['stress'],
            'focus': classification['focus'],
            'relaxation': classification['relaxation'],
            'drowsiness': classification['drowsiness']
        }
        dominant_state = max(states, key=states.get)

        # Map to enum
        state_map = {
            'stress': MentalState.STRESSED,
            'focus': MentalState.FOCUSED,
            'relaxation': MentalState.RELAXED,
            'drowsiness': MentalState.DROWSY
        }

        # Store in PostgreSQL
        # Extract band powers from results (they're returned as a dict)
        band_powers = results.get('band_powers', {})

        eeg_analysis = EEGAnalysis(
            user_id=user_id,
            timestamp=datetime.now(),
            mental_state=state_map.get(dominant_state, MentalState.STRESSED),
            stress_level=classification['stress'],
            focus_level=classification['focus'],
            relaxation_level=classification['relaxation'],
            drowsiness_level=classification['drowsiness'],
            delta_power=float(band_powers.get('delta', 0.0)),
            theta_power=float(band_powers.get('theta', 0.0)),
            alpha_power=float(band_powers.get('alpha', 0.0)),
            beta_power=float(band_powers.get('beta', 0.0)),
            gamma_power=float(band_powers.get('gamma', 0.0)),
            dominant_band=results.get('dominant_band', 'beta'),
            duration_seconds=eeg_data.shape[1] / eeg_processor.sample_rate,
            channels_used=eeg_data.shape[0],
            sample_rate=eeg_processor.sample_rate
        )

        db.add(eeg_analysis)
        await db.commit()
        await db.refresh(eeg_analysis)

        # Store raw data in MongoDB (async)
        mongo_db = get_mongo_db()
        if mongo_db:
            mongo_doc = {
                'user_id': user_id,
                'timestamp': datetime.now(),
                'channels': eeg_data.tolist(),
                'channel_names': [f'CH{i+1}' for i in range(eeg_data.shape[0])],
                'sample_rate': eeg_processor.sample_rate,
                'duration_seconds': eeg_data.shape[1] / eeg_processor.sample_rate,
                'analysis_id': eeg_analysis.id,
                'created_at': datetime.now()
            }
            await mongo_db.eeg_raw_data.insert_one(mongo_doc)

        return EEGAnalysisResponse(
            id=eeg_analysis.id,
            user_id=eeg_analysis.user_id,
            timestamp=eeg_analysis.timestamp,
            stress=eeg_analysis.stress_level,
            focus=eeg_analysis.focus_level,
            relaxation=eeg_analysis.relaxation_level,
            drowsiness=eeg_analysis.drowsiness_level,
            dominant_band=eeg_analysis.dominant_band,
            mental_state=eeg_analysis.mental_state.value,
            recommendations=classification.get('recommendations', [])
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing EEG data: {str(e)}")


@router.get("/analysis", response_model=List[EEGAnalysisResponse])
async def get_eeg_analyses(
    db: AsyncSession = Depends(get_db),
    user_id: str = "demo_user",
    limit: int = 10
):
    """
    Get recent EEG analysis results
    """
    query = select(EEGAnalysis).where(
        EEGAnalysis.user_id == user_id
    ).order_by(desc(EEGAnalysis.timestamp)).limit(limit)

    result = await db.execute(query)
    analyses = result.scalars().all()

    return [
        EEGAnalysisResponse(
            id=a.id,
            user_id=a.user_id,
            timestamp=a.timestamp,
            stress=a.stress_level,
            focus=a.focus_level,
            relaxation=a.relaxation_level,
            drowsiness=a.drowsiness_level,
            dominant_band=a.dominant_band,
            mental_state=a.mental_state.value,
            recommendations=[]  # Could fetch from recommendations table
        )
        for a in analyses
    ]


@router.get("/band-powers/{analysis_id}", response_model=EEGBandPowers)
async def get_band_powers(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = "demo_user"
):
    """
    Get detailed band power breakdown for specific analysis
    """
    result = await db.execute(
        select(EEGAnalysis).where(
            EEGAnalysis.id == analysis_id,
            EEGAnalysis.user_id == user_id
        )
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return EEGBandPowers(
        delta=analysis.delta_power,
        theta=analysis.theta_power,
        alpha=analysis.alpha_power,
        beta=analysis.beta_power,
        gamma=analysis.gamma_power
    )


@router.post("/realtime")
async def analyze_realtime_eeg(
    data: dict,
    db: AsyncSession = Depends(get_db),
    user_id: str = "demo_user"
):
    """
    Analyze real-time EEG data stream

    Expected format: {"channels": [[...], [...], ...], "timestamp": "..."}
    """
    try:
        channels = data.get('channels')
        if not channels:
            raise HTTPException(status_code=400, detail="No channel data provided")

        eeg_data = np.array(channels)

        # Quick analysis (simplified for real-time)
        preprocessed = eeg_processor.preprocess(eeg_data)
        features = eeg_processor.extract_features(preprocessed)
        classification = eeg_classifier.predict(features)

        return {
            "status": "processed",
            "results": {
                "stress": classification['stress'],
                "focus": classification['focus'],
                "relaxation": classification['relaxation'],
                "drowsiness": classification['drowsiness']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing real-time data: {str(e)}")
