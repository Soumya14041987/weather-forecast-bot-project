#!/usr/bin/env python3
"""FastAPI Weather Bot with Beautiful Web UI - Production Grade"""

import os
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from strands import Agent, tool
from strands.models import BedrockModel

# Configuration
BEDROCK_MODEL = os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
MAX_CITY_LENGTH = 100
REQUEST_TIMEOUT = 10

# FastAPI Setup
app = FastAPI(
    title="Weather Forecast Bot",
    description="AI-powered weather forecast using AWS Strands Agents SDK",
    version="1.0.0"
)

# Request Model
class WeatherRequest(BaseModel):
    city: str = Field(..., min_length=1, max_length=MAX_CITY_LENGTH, description="City name")

# Tool Definition
@tool
def get_weather(city: str) -> dict:
    """Get weather forecast for a city."""
    try:
        # Geocode
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city[:MAX_CITY_LENGTH], "count": 1},
            timeout=REQUEST_TIMEOUT
        ).json()
        
        if "results" not in geo:
            return {"error": "City not found"}
        
        loc = geo["results"][0]
        
        # Weather
        weather = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": loc["latitude"],
                "longitude": loc["longitude"],
                "current": "temperature_2m,apparent_temperature",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
                "forecast_days": 7
            },
            timeout=REQUEST_TIMEOUT
        ).json()
        
        current = weather["current"]
        daily = weather["daily"]
        
        # Build forecast
        forecast = [
            {
                "date": daily["time"][i],
                "temp_max": round(daily["temperature_2m_max"][i], 1),
                "temp_min": round(daily["temperature_2m_min"][i], 1),
                "precipitation": round(daily["precipitation_sum"][i], 1),
                "precip_prob": int(daily["precipitation_probability_max"][i])
            }
            for i in range(7)
        ]
        
        return {
            "location": {"city": loc["name"], "country": loc["country"]},
            "current": {
                "temp": round(current["temperature_2m"], 1),
                "feels_like": round(current["apparent_temperature"], 1)
            },
            "forecast": forecast
        }
    except Exception as e:
        return {"error": str(e)[:100]}

# Global Agent Initialization (Warm Connection)
agent = Agent(
    name="WeatherBot",
    model=BedrockModel(model_id=BEDROCK_MODEL, region_name=AWS_REGION),
    tools=[get_weather]
)

# HTML UI
HTML_UI = """<!DOCTYPE html>
<html><head><title>Weather Forecast Bot</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px}
.container{max-width:800px;margin:0 auto}
.card{background:white;border-radius:20px;padding:30px;box-shadow:0 20px 60px rgba(0,0,0,0.3);margin-bottom:20px}
h1{color:#333;font-size:32px;margin-bottom:10px}
.subtitle{color:#666;margin-bottom:30px}
.search-box{display:flex;gap:10px;margin-bottom:20px}
input{flex:1;padding:15px;border:2px solid #e0e0e0;border-radius:10px;font-size:16px;transition:border 0.3s}
input:focus{outline:none;border-color:#667eea}
button{padding:15px 30px;background:#667eea;color:white;border:none;border-radius:10px;font-size:16px;cursor:pointer;transition:background 0.3s}
button:hover{background:#5568d3}
button:disabled{background:#ccc;cursor:not-allowed}
.loading{text-align:center;color:#666;padding:20px}
.error{background:#fee;color:#c33;padding:15px;border-radius:10px;border-left:4px solid #c33}
.weather-info{display:none}
.location{font-size:28px;color:#333;margin-bottom:20px}
.location-sub{color:#666;font-size:18px}
.current{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:30px;border-radius:15px;margin-bottom:20px;text-align:center}
.temp{font-size:64px;font-weight:bold;margin:10px 0}
.feels{font-size:18px;opacity:0.9}
.summary{background:#f8f9fa;padding:20px;border-radius:10px;margin-bottom:20px;line-height:1.6}
.insights{margin-bottom:20px}
.insight-item{background:#e3f2fd;padding:12px;margin:8px 0;border-radius:8px;border-left:4px solid #2196f3}
.recommendation{background:#fff3cd;padding:15px;border-radius:10px;border-left:4px solid #ffc107;margin-bottom:20px}
.forecast-title{font-size:20px;color:#333;margin:20px 0 15px 0;font-weight:600}
.forecast-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:15px}
.forecast-day{background:#f8f9fa;padding:15px;border-radius:10px;text-align:center;transition:transform 0.2s}
.forecast-day:hover{transform:translateY(-5px);box-shadow:0 5px 15px rgba(0,0,0,0.1)}
.day-date{font-weight:600;color:#333;margin-bottom:8px}
.day-temp{font-size:24px;color:#667eea;margin:5px 0}
.day-details{font-size:14px;color:#666;margin-top:8px}
.api-info{background:#e8f5e9;padding:15px;border-radius:10px;margin-top:20px;font-size:14px}
@media(max-width:600px){
.search-box{flex-direction:column}
.temp{font-size:48px}
.forecast-grid{grid-template-columns:1fr}
}
</style></head><body>
<div class="container">
<div class="card">
<h1>🌤️ Weather Forecast Bot</h1>
<p class="subtitle">Powered by AWS Strands Agents SDK + FastAPI</p>
<div class="search-box">
<input type="text" id="city" placeholder="Enter city name (e.g., Pune, Tokyo, London)"/>
<button id="btn" onclick="getWeather()">Get Forecast</button>
</div>
<div id="loading" class="loading" style="display:none">🔄 Loading forecast...</div>
<div id="error" class="error" style="display:none"></div>
<div id="weather" class="weather-info"></div>
<div class="api-info">
<strong>API Endpoint:</strong> POST /api/weather<br>
<strong>Docs:</strong> <a href="/docs" target="_blank">/docs</a> | <a href="/redoc" target="_blank">/redoc</a>
</div>
</div>
</div>
<script>
async function getWeather(){
const city=document.getElementById('city').value.trim();
const loading=document.getElementById('loading');
const error=document.getElementById('error');
const weather=document.getElementById('weather');
const btn=document.getElementById('btn');
if(!city){error.textContent='Please enter a city name';error.style.display='block';return;}
loading.style.display='block';error.style.display='none';weather.style.display='none';btn.disabled=true;
try{
const r=await fetch('/api/weather',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({city:city})});
const data=await r.json();
loading.style.display='none';btn.disabled=false;
if(data.error||r.status!==200){error.textContent=data.error||data.detail||'Error occurred';error.style.display='block';return;}
displayWeather(data);
}catch(e){loading.style.display='none';btn.disabled=false;error.textContent='Error: '+e.message;error.style.display='block';}
}
function displayWeather(data){
const weather=document.getElementById('weather');
const loc=data.location;
const curr=data.current;
const summary=data.summary||'Weather forecast available';
const insights=data.insights||[];
const recommendation=data.recommendation||'';
const forecast=data.forecast||[];
let html=`
<div class="location">${loc.city}, ${loc.country}</div>
<div class="current">
<div class="temp">${curr.temp}°C</div>
<div class="feels">Feels like ${curr.feels_like}°C</div>
</div>
<div class="summary"><strong>Summary:</strong> ${summary}</div>
`;
if(insights.length>0){
html+=`<div class="insights"><strong>Key Insights:</strong>`;
insights.forEach(i=>html+=`<div class="insight-item">💡 ${i}</div>`);
html+=`</div>`;
}
if(recommendation){
html+=`<div class="recommendation"><strong>Recommendation:</strong> ${recommendation}</div>`;
}
if(forecast.length>0){
html+=`<div class="forecast-title">7-Day Forecast</div><div class="forecast-grid">`;
forecast.forEach(day=>{
const date=new Date(day.date);
const dayName=date.toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric'});
html+=`
<div class="forecast-day">
<div class="day-date">${dayName}</div>
<div class="day-temp">${day.temp_max}°</div>
<div class="day-details">Low: ${day.temp_min}°C</div>
<div class="day-details">💧 ${day.precip_prob}%</div>
</div>`;
});
html+=`</div>`;
}
weather.innerHTML=html;
weather.style.display='block';
}
document.getElementById('city').addEventListener('keypress',e=>{if(e.key==='Enter')getWeather();});
</script></body></html>"""

# Routes
@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the web UI."""
    return HTML_UI

@app.post("/api/weather")
async def weather_endpoint(request: WeatherRequest):
    """Get weather forecast with AI analysis."""
    try:
        city = request.city.strip()
        
        # Get weather data
        weather_data = get_weather(city)
        if "error" in weather_data:
            raise HTTPException(status_code=400, detail=weather_data["error"])
        
        # Get AI analysis
        prompt = f"""Analyze weather for {weather_data['location']['city']}, {weather_data['location']['country']}:
Current: {weather_data['current']['temp']}°C (feels {weather_data['current']['feels_like']}°C)
7-day forecast: {weather_data['forecast']}

Provide: summary (2 sentences), condition (sunny/cloudy/rainy), insights (2-3 points), recommendation."""
        
        result = agent(prompt)
        ai_text = str(result)
        
        # Try to extract structured data from AI response
        try:
            if '{' in ai_text and '}' in ai_text:
                json_start = ai_text.find('{')
                json_end = ai_text.rfind('}') + 1
                ai_data = json.loads(ai_text[json_start:json_end])
                weather_data.update(ai_data)
        except:
            # Fallback
            weather_data['summary'] = f"Current temperature {weather_data['current']['temp']}°C with 7-day forecast available."
            weather_data['condition'] = 'clear'
            weather_data['insights'] = [
                f"High: {max(d['temp_max'] for d in weather_data['forecast'])}°C",
                f"Low: {min(d['temp_min'] for d in weather_data['forecast'])}°C"
            ]
            weather_data['recommendation'] = 'Check forecast for planning'
        
        return weather_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)[:100])

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "weather-bot"}

# Run with: uvicorn web-server-fastapi:app --host 0.0.0.0 --port 8080 --reload
