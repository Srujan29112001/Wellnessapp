"""
EEG Analysis Endpoints - UPDATED WITH FULL IMPLEMENTATION
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import tempfile
import os

from backend.database.postgres import get_db
from backend.services.eeg_service import EEGService

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
    # Initialize EEG service
    eeg_service = EEGService()

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        # Analyze EEG file
        results = eeg_service.analyze_eeg_file(temp_path, user_id)

        # Store analysis in database
        stored_ids = await eeg_service.store_analysis(db, results)

        return EEGAnalysisResponse(
            id=stored_ids['analysis_id'],
            user_id=results['user_id'],
            timestamp=datetime.fromisoformat(results['timestamp']),
            stress=results['stress'],
            focus=results['focus'],
            relaxation=results['relaxation'],
            drowsiness=results['drowsiness'],
            dominant_band=results['dominant_band'],
            mental_state=results['mental_state'],
            recommendations=results['recommendations']
        )

    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@router.get("/analysis", response_model=List[EEGAnalysisResponse])
async def get_eeg_analyses(
    db: AsyncSession = Depends(get_db),
    user_id: str = "demo_user",
    limit: int = 10
):
    """
    Get recent EEG analysis results
    """
    from backend.models.postgres_models import EEGAnalysis
    from sqlalchemy import select

    stmt = select(EEGAnalysis).where(
        EEGAnalysis.user_id == user_id
    ).order_by(EEGAnalysis.timestamp.desc()).limit(limit)

    result = await db.execute(stmt)
    analyses = list(result.scalars().all())

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
            recommendations=[]  # Could fetch from service
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
    from backend.models.postgres_models import EEGAnalysis
    from sqlalchemy import select, and_

    stmt = select(EEGAnalysis).where(
        and_(
            EEGAnalysis.id == analysis_id,
            EEGAnalysis.user_id == user_id
        )
    )

    result = await db.execute(stmt)
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

    Expected format: {"channels": [[...], [...], ...], "sample_rate": 256}
    """
    import numpy as np
    from backend.services.eeg_service import EEGService

    eeg_service = EEGService()

    # Convert to numpy array
    channels = np.array(data.get('channels', []))
    sample_rate = data.get('sample_rate', 256)

    if channels.size == 0:
        raise HTTPException(status_code=400, detail="No EEG data provided")

    # Analyze
    raw_data = channels
    results = eeg_service.analyze_eeg_data(raw_data, user_id)

    # Store
    stored_ids = await eeg_service.store_analysis(db, results, raw_data)

    return {
        "status": "success",
        "analysis_id": stored_ids['analysis_id'],
        "mental_state": results['mental_state'],
        "stress": results['stress'],
        "focus": results['focus']
    }
