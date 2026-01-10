import json
import os
import sys
import requests
from strands import Agent, tool
from strands.models import BedrockModel

# Configuration
BEDROCK_MODEL = os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
MAX_CITY_LENGTH = 100
REQUEST_TIMEOUT = 10

@tool
def get_weather(city: str) -> dict:
    """Get weather forecast for a city."""
    try:
        # Geocode city
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_resp = requests.get(
            geo_url, 
            params={"name": city[:MAX_CITY_LENGTH], "count": 1}, 
            timeout=REQUEST_TIMEOUT
        ).json()
        
        if "results" not in geo_resp:
            return {"error": "City not found"}
        
        loc = geo_resp["results"][0]
        
        # Get weather
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "current": "temperature_2m,apparent_temperature",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
            "forecast_days": 7
        }
        weather_resp = requests.get(weather_url, params=weather_params, timeout=REQUEST_TIMEOUT).json()
        
        current = weather_resp["current"]
        daily = weather_resp["daily"]
        
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
            "location": {
                "city": loc["name"],
                "country": loc["country"]
            },
            "current": {
                "temp": round(current["temperature_2m"], 1),
                "feels_like": round(current["apparent_temperature"], 1)
            },
            "forecast": forecast
        }
    except Exception as e:
        return {"error": str(e)[:100]}

# Initialize agent (global for EC2 - keeps connection warm)
print("Initializing AWS Strands Weather Bot...")
agent = Agent(
    name="WeatherBot",
    model=BedrockModel(model_id=BEDROCK_MODEL, region_name=AWS_REGION),
    tools=[get_weather]
)
print("✓ Agent initialized successfully\n")

def get_forecast(city: str) -> dict:
    """Get weather forecast with AI analysis."""
    try:
        # Get weather data
        weather_data = get_weather(city)
        if "error" in weather_data:
            return weather_data
        
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
    except Exception as e:
        return {"error": str(e)[:100]}

def display_forecast(data: dict):
    """Display forecast in a readable format."""
    if "error" in data:
        print(f"\n❌ Error: {data['error']}\n")
        return
    
    loc = data['location']
    curr = data['current']
    
    print("\n" + "="*60)
    print(f"📍 {loc['city']}, {loc['country']}")
    print("="*60)
    
    print(f"\n🌡️  Current Temperature: {curr['temp']}°C")
    print(f"   Feels like: {curr['feels_like']}°C")
    
    if 'summary' in data:
        print(f"\n📝 Summary:")
        print(f"   {data['summary']}")
    
    if 'insights' in data and data['insights']:
        print(f"\n💡 Key Insights:")
        for insight in data['insights']:
            print(f"   • {insight}")
    
    if 'recommendation' in data:
        print(f"\n🎯 Recommendation:")
        print(f"   {data['recommendation']}")
    
    if 'forecast' in data:
        print(f"\n📅 7-Day Forecast:")
        print("-"*60)
        for day in data['forecast']:
            print(f"   {day['date']}: {day['temp_max']}°C / {day['temp_min']}°C  💧 {day['precip_prob']}%")
    
    print("\n" + "="*60 + "\n")

def interactive_mode():
    """Run in interactive mode."""
    print("AWS Strands Weather Forecast Bot")
    print("="*60)
    print("Type 'quit' or 'exit' to stop\n")
    
    while True:
        try:
            city = input("Enter city name: ").strip()
            
            if city.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye! 👋\n")
                break
            
            if not city:
                print("❌ Please enter a city name\n")
                continue
            
            print(f"\n🔄 Fetching forecast for {city}...")
            result = get_forecast(city)
            display_forecast(result)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")

def single_query_mode(city: str):
    """Run a single query and exit."""
    print(f"🔄 Fetching forecast for {city}...")
    result = get_forecast(city)
    display_forecast(result)

# Main execution
if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Single query mode: python weather-forecast-bot.py "Tokyo"
        city = " ".join(sys.argv[1:])
        single_query_mode(city)
    else:
        # Interactive mode
        interactive_mode()
