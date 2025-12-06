from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.weather import DailyWeather
from app.core.config import settings
from datetime import date
import httpx
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Hangzhou coordinates
LAT = 30.2936
LON = 120.1614

@router.get("/today")
async def get_todays_weather(db: Session = Depends(get_db)):
    """
    Get today's weather for Hangzhou.
    Checks DB first. If missing, fetches from OpenMeteo and caches it.
    """
    today = date.today()
    
    # 1. Check DB
    record = db.query(DailyWeather).filter(DailyWeather.date == today).first()
    if record:
        return {
            "source": "cache",
            "weather_code": record.weather_code,
            "temp_min": record.temp_min,
            "temp_max": record.temp_max,
            "city": record.city
        }
    
    # 2. Fetch from OpenMeteo
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=Asia%2FShanghai&forecast_days=1"
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            data = resp.json()
            
        daily = data.get("daily", {})
        
        weather_code = daily.get("weather_code", [0])[0]
        temp_max = daily.get("temperature_2m_max", [0])[0]
        temp_min = daily.get("temperature_2m_min", [0])[0]
        
        # 3. Save to DB
        new_record = DailyWeather(
            date=today,
            city="Hangzhou",
            weather_code=weather_code,
            temp_min=temp_min,
            temp_max=temp_max,
            raw_data=data
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        
        return {
            "source": "api",
            "weather_code": new_record.weather_code,
            "temp_min": new_record.temp_min,
            "temp_max": new_record.temp_max,
            "city": new_record.city
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch weather: {e}")
        # Fallback if API fails
        return {
            "source": "fallback",
            "weather_code": 0, # Clear sky default
            "temp_min": 20,
            "temp_max": 25,
            "city": "Hangzhou"
        }
