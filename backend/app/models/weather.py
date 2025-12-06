from datetime import date
from sqlalchemy import Column, Integer, String, Date, Float, JSON
from app.db.base import Base

class DailyWeather(Base):
    __tablename__ = "daily_weather"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)  # One record per day
    city = Column(String, default="Hangzhou")
    weather_code = Column(Integer, nullable=False) # WMO code
    temp_min = Column(Float)
    temp_max = Column(Float)
    raw_data = Column(JSON) # Store full API response just in case
