"""
Wearable Integration API Endpoints.

Provides REST API for connecting and syncing wearable devices.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from backend.services.wearable_integration import (
    WearableService,
    WearableMetrics
)
from backend.api.deps import get_db

router = APIRouter(prefix="/api/v1/wearables", tags=["wearables"])

# Global wearable service instance
wearable_service = WearableService()


# Request/Response models
class FitbitAuthRequest(BaseModel):
    """Fitbit OAuth authorization."""
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None


class AppleHealthUploadRequest(BaseModel):
    """Apple Health data upload."""
    export_file_path: str  # Path to uploaded file


class GarminAuthRequest(BaseModel):
    """Garmin Connect credentials."""
    email: str
    password: str


class WearableMetricsResponse(BaseModel):
    """Wearable metrics response."""
    date: str
    platform: str
    steps: Optional[int] = None
    distance_km: Optional[float] = None
    calories_burned: Optional[int] = None
    active_minutes: Optional[int] = None
    heart_rate_avg: Optional[int] = None
    heart_rate_resting: Optional[int] = None
    hrv: Optional[float] = None
    sleep_hours: Optional[float] = None
    deep_sleep_minutes: Optional[int] = None
    rem_sleep_minutes: Optional[int] = None
    light_sleep_minutes: Optional[int] = None
    sleep_score: Optional[int] = None
    stress_score: Optional[int] = None
    body_battery: Optional[int] = None
    readiness_score: Optional[int] = None
    spo2: Optional[float] = None
    respiration_rate: Optional[float] = None
    skin_temperature: Optional[float] = None
    weight_kg: Optional[float] = None
    body_fat_percent: Optional[float] = None


# Endpoints
@router.post("/fitbit/connect")
async def connect_fitbit(
    auth_request: FitbitAuthRequest,
    user_id: str,  # In production, get from JWT token
    db: Session = Depends(get_db)
):
    """
    Connect user's Fitbit account.

    Requires Fitbit OAuth2 access token.

    Steps to get token:
    1. Register app at https://dev.fitbit.com/apps
    2. Implement OAuth2 flow (redirect to Fitbit authorization)
    3. Exchange authorization code for access token
    4. Send token to this endpoint
    """
    try:
        wearable_service.add_fitbit(user_id, auth_request.access_token)

        # In production: Store tokens securely in database
        # db.query(UserWearableConnection).filter(...).update(...)

        return {
            "success": True,
            "message": "Fitbit connected successfully",
            "platform": "fitbit",
            "user_id": user_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect Fitbit: {str(e)}"
        )


@router.post("/apple-health/upload")
async def upload_apple_health(
    upload_request: AppleHealthUploadRequest,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Upload Apple Health export data.

    User must export health data from iPhone Health app and upload the file.
    """
    try:
        wearable_service.add_apple_health(user_id, upload_request.export_file_path)

        return {
            "success": True,
            "message": "Apple Health data uploaded successfully",
            "platform": "apple_health",
            "user_id": user_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload Apple Health data: {str(e)}"
        )


@router.post("/garmin/connect")
async def connect_garmin(
    auth_request: GarminAuthRequest,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Connect user's Garmin account.

    Note: Uses Garmin Connect credentials.
    For production, use Garmin Health API with OAuth2.
    """
    try:
        wearable_service.add_garmin(
            user_id,
            auth_request.email,
            auth_request.password
        )

        return {
            "success": True,
            "message": "Garmin connected successfully",
            "platform": "garmin",
            "user_id": user_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect Garmin: {str(e)}"
        )


@router.get("/metrics/{platform}")
async def get_platform_metrics(
    platform: str,
    user_id: str,
    target_date: Optional[str] = None,  # Format: YYYY-MM-DD
    db: Session = Depends(get_db)
) -> WearableMetricsResponse:
    """
    Get metrics from specific wearable platform.

    Platforms: fitbit, apple, garmin
    """
    if platform not in ['fitbit', 'apple', 'garmin']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform: {platform}"
        )

    # Parse date
    if target_date:
        try:
            parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    else:
        parsed_date = date.today()

    # Get metrics
    metrics = wearable_service.get_metrics(user_id, platform, parsed_date)

    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No {platform} connection found for user {user_id}"
        )

    # Convert to response model
    response = WearableMetricsResponse(
        date=metrics.date,
        platform=platform,
        **{k: v for k, v in metrics.__dict__.items() if k != 'date'}
    )

    return response


@router.get("/metrics/merged")
async def get_merged_metrics(
    user_id: str,
    target_date: Optional[str] = None,
    db: Session = Depends(get_db)
) -> WearableMetricsResponse:
    """
    Get merged metrics from all connected wearable platforms.

    Combines data from all sources, prioritizing most accurate/recent values.
    """
    # Parse date
    if target_date:
        try:
            parsed_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    else:
        parsed_date = date.today()

    # Get merged metrics
    metrics = wearable_service.get_merged_metrics(user_id, parsed_date)

    response = WearableMetricsResponse(
        date=metrics.date,
        platform="merged",
        **{k: v for k, v in metrics.__dict__.items() if k != 'date'}
    )

    return response


@router.get("/metrics/history")
async def get_metrics_history(
    user_id: str,
    platform: str = "merged",
    days: int = 30,
    db: Session = Depends(get_db)
) -> List[WearableMetricsResponse]:
    """
    Get historical metrics for specified number of days.

    Args:
        platform: fitbit, apple, garmin, or merged
        days: Number of days to fetch (1-365)
    """
    if days < 1 or days > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Days must be between 1 and 365"
        )

    history = []

    for i in range(days):
        target_date = date.today() - timedelta(days=i)

        if platform == "merged":
            metrics = wearable_service.get_merged_metrics(user_id, target_date)
        else:
            metrics = wearable_service.get_metrics(user_id, platform, target_date)

        if metrics:
            response = WearableMetricsResponse(
                date=metrics.date,
                platform=platform,
                **{k: v for k, v in metrics.__dict__.items() if k != 'date'}
            )
            history.append(response)

    return history


@router.get("/connections")
async def get_connected_platforms(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get list of connected wearable platforms for user.
    """
    # Check which platforms are connected
    connected = []

    for platform in ['fitbit', 'apple', 'garmin']:
        integration_key = f"{user_id}_{platform}"
        if integration_key in wearable_service.integrations:
            connected.append({
                "platform": platform,
                "status": "connected",
                "last_sync": None  # TODO: Track last sync time
            })

    return {
        "user_id": user_id,
        "connected_platforms": connected,
        "total_connected": len(connected)
    }


@router.delete("/disconnect/{platform}")
async def disconnect_platform(
    platform: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Disconnect wearable platform.
    """
    integration_key = f"{user_id}_{platform}"

    if integration_key in wearable_service.integrations:
        del wearable_service.integrations[integration_key]

        # In production: Delete from database
        # db.query(UserWearableConnection).filter(...).delete()

        return {
            "success": True,
            "message": f"{platform} disconnected successfully"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No {platform} connection found"
        )


@router.get("/oauth/fitbit/initiate")
async def initiate_fitbit_oauth():
    """
    Get Fitbit OAuth2 authorization URL.

    Client should redirect user to this URL to authorize access.
    """
    # In production: Generate state token for CSRF protection
    client_id = os.getenv("FITBIT_CLIENT_ID", "YOUR_CLIENT_ID")
    redirect_uri = os.getenv("FITBIT_REDIRECT_URI", "http://localhost:8000/api/v1/wearables/oauth/fitbit/callback")

    auth_url = (
        f"https://www.fitbit.com/oauth2/authorize?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=activity%20heartrate%20sleep%20profile"
    )

    return {
        "authorization_url": auth_url,
        "instructions": "Redirect user to this URL to authorize Fitbit access"
    }


@router.get("/oauth/fitbit/callback")
async def fitbit_oauth_callback(
    code: str,
    state: Optional[str] = None
):
    """
    Fitbit OAuth2 callback endpoint.

    Exchanges authorization code for access token.
    """
    import base64

    client_id = os.getenv("FITBIT_CLIENT_ID")
    client_secret = os.getenv("FITBIT_CLIENT_SECRET")
    redirect_uri = os.getenv("FITBIT_REDIRECT_URI")

    # Exchange code for token
    auth_header = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()

    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }

    response = requests.post(
        "https://api.fitbit.com/oauth2/token",
        headers=headers,
        data=data
    )

    if response.status_code == 200:
        token_data = response.json()

        return {
            "success": True,
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "expires_in": token_data.get("expires_in"),
            "user_id": token_data.get("user_id")
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange code for token"
        )
