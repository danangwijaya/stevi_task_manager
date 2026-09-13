import time
import urllib.request
import urllib.parse
import json
import logging
import os
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

# Default Credentials provided by user
ARCGIS_USERNAME = os.getenv("ARCGIS_USERNAME", "ekoregion_indonesia")
ARCGIS_PASSWORD = os.getenv("ARCGIS_PASSWORD", "9ol*IK7uj^YH")

_cached_token_data = {
    "token": None,
    "expires": 0,
    "username": ARCGIS_USERNAME
}

class CredentialsRequest(BaseModel):
    username: str
    password: str

def generate_arcgis_token(username: str, password: str, expiration_minutes: int = 21600) -> dict:
    url = "https://www.arcgis.com/sharing/rest/generateToken"
    payload = {
        "username": username,
        "password": password,
        "referer": "https://www.arcgis.com",
        "expiration": str(expiration_minutes),
        "f": "json"
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if "error" in res_data:
                raise HTTPException(status_code=400, detail=res_data["error"].get("message", "ArcGIS authentication failed"))
            return res_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting to ArcGIS generateToken: {e}")
        raise HTTPException(status_code=502, detail=f"Gagal menghubungi server otentikasi ArcGIS: {str(e)}")

@router.get("/token")
def get_arcgis_token() -> Any:
    """
    Returns valid ArcGIS token with automatic caching and refresh.
    """
    now_ms = int(time.time() * 1000)
    # If cached token is valid for at least 1 more hour (3600000 ms)
    if _cached_token_data["token"] and _cached_token_data["expires"] - now_ms > 3600000:
        return {
            "token": _cached_token_data["token"],
            "expires": _cached_token_data["expires"],
            "cached": True
        }
    
    # Generate fresh token
    res = generate_arcgis_token(ARCGIS_USERNAME, ARCGIS_PASSWORD)
    _cached_token_data["token"] = res["token"]
    _cached_token_data["expires"] = res["expires"]
    _cached_token_data["username"] = ARCGIS_USERNAME
    
    return {
        "token": res["token"],
        "expires": res["expires"],
        "cached": False
    }

@router.post("/credentials")
def update_arcgis_credentials(creds: CredentialsRequest) -> Any:
    global ARCGIS_USERNAME, ARCGIS_PASSWORD
    res = generate_arcgis_token(creds.username, creds.password)
    ARCGIS_USERNAME = creds.username
    ARCGIS_PASSWORD = creds.password
    _cached_token_data["token"] = res["token"]
    _cached_token_data["expires"] = res["expires"]
    _cached_token_data["username"] = creds.username
    return {
        "message": "Kredensial ArcGIS berhasil diperbarui & diverifikasi!",
        "token": res["token"],
        "expires": res["expires"]
    }
