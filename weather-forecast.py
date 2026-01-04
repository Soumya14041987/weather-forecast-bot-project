import json
import requests
import boto3

client = boto3.client('bedrock-runtime', region_name='us-east-1')

def get_coordinates(city_name: str) -> dict:
    """Converts a city name into latitude and longitude coordinates."""
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
    response = requests.get(url).json()
    if "results" in response:
        res = response["results"][0]
        return {"lat": res["latitude"], "lon": res["longitude"], "name": res["name"], "country": res["country"]}
    return {"error": "City not found"}

def get_weather_forecast(lat: float, lon: float) -> dict:
    """Fetches real-time weather data and 10-day forecast for given coordinates."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,precipitation_probability_max,snowfall_sum,rain_sum,showers_sum,windspeed_10m_max&current=temperature_2m,apparent_temperature,precipitation,rain,snowfall&timezone=auto&forecast_days=14"
    return requests.get(url).json()

def analyze_weather(city: str) -> dict:
    """Main weather analysis function using Bedrock - returns structured data."""
    try:
        coords = get_coordinates(city)
        if "error" in coords:
            return {"error": coords["error"]}
        
        weather = get_weather_forecast(coords["lat"], coords["lon"])
        
        # Extract current weather
        current = weather.get('current', {})
        current_temp = current.get('temperature_2m', 0)
        feels_like = current.get('apparent_temperature', current_temp)
        current_precip = current.get('precipitation', 0)
        current_rain = current.get('rain', 0)
        current_snow = current.get('snowfall', 0)
        
        # Extract daily forecast data
        daily = weather.get('daily', {})
        temps_max = daily.get('temperature_2m_max', [])
        temps_min = daily.get('temperature_2m_min', [])
        feels_like_max = daily.get('apparent_temperature_max', [])
        feels_like_min = daily.get('apparent_temperature_min', [])
        precipitation = daily.get('precipitation_sum', [])
        precipitation_prob = daily.get('precipitation_probability_max', [])
        snowfall = daily.get('snowfall_sum', [])
        rain = daily.get('rain_sum', [])
        windspeed = daily.get('windspeed_10m_max', [])
        times = daily.get('time', [])
        
        # Get current/today's weather
        current_temp_max = temps_max[0] if temps_max else current_temp
        current_temp_min = temps_min[0] if temps_min else current_temp
        current_feels_max = feels_like_max[0] if feels_like_max else feels_like
        current_feels_min = feels_like_min[0] if feels_like_min else feels_like
        
        # Build 10-day forecast with detailed info
        forecast_days = []
        alerts = []
        
        for i in range(min(10, len(times))):
            day_data = {
                "date": times[i],
                "temp_max": round(temps_max[i], 1) if i < len(temps_max) else 0,
                "temp_min": round(temps_min[i], 1) if i < len(temps_min) else 0,
                "feels_like_max": round(feels_like_max[i], 1) if i < len(feels_like_max) else 0,
                "feels_like_min": round(feels_like_min[i], 1) if i < len(feels_like_min) else 0,
                "precipitation": round(precipitation[i], 1) if i < len(precipitation) else 0,
                "precipitation_prob": round(precipitation_prob[i], 0) if i < len(precipitation_prob) else 0,
                "snowfall": round(snowfall[i], 1) if i < len(snowfall) else 0,
                "rain": round(rain[i], 1) if i < len(rain) else 0,
                "windspeed": round(windspeed[i], 1) if i < len(windspeed) else 0
            }
            forecast_days.append(day_data)
            
            # Generate alerts for next 3 days
            if i < 3:
                day_name = "today" if i == 0 else ("tomorrow" if i == 1 else "in 2 days")
                
                if day_data["snowfall"] > 5:
                    alerts.append(f"Heavy snowfall expected {day_name} ({day_data['snowfall']}mm)")
                elif day_data["snowfall"] > 0:
                    alerts.append(f"Light snow possible {day_name}")
                
                if day_data["rain"] > 20:
                    alerts.append(f"Heavy rain expected {day_name} ({day_data['rain']}mm)")
                elif day_data["rain"] > 10:
                    alerts.append(f"Moderate rain likely {day_name}")
                
                if day_data["windspeed"] > 50:
                    alerts.append(f"Strong winds {day_name} (up to {day_data['windspeed']} km/h)")
                
                if day_data["precipitation_prob"] > 80:
                    alerts.append(f"Very high chance of precipitation {day_name} ({day_data['precipitation_prob']}%)")
        
        # Create prompt for AI analysis
        prompt = f"""Analyze this 10-day weather forecast for {coords['name']}, {coords['country']}:

Current: {current_temp}°C (feels like {feels_like}°C)
Temperature Max (°C): {temps_max[:10]}
Temperature Min (°C): {temps_min[:10]}
Precipitation (mm): {precipitation[:10]}
Snow (mm): {snowfall[:10]}

Create a weather analysis. Respond with ONLY a valid JSON object:
{{
    "summary": "Engaging 2-sentence weather overview with personality",
    "current_condition": "sunny/partly-cloudy/cloudy/rainy/stormy/snowy",
    "insights": [
        "First interesting weather insight in natural conversational language",
        "Second key observation about temperature or conditions",
        "Third notable pattern or upcoming change"
    ],
    "recommendation": "Fun, casual activity suggestion based on weather"
}}"""
        
        response = client.invoke_model(
            modelId='us.amazon.nova-lite-v1:0',
            body=json.dumps({
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {"temperature": 0.5, "maxTokens": 1000}
            })
        )
        
        result = json.loads(response['body'].read())
        ai_response = result['output']['message']['content'][0]['text'].strip()
        
        # Try to extract JSON from response
        try:
            # Remove markdown code blocks if present
            if '```json' in ai_response:
                ai_response = ai_response.split('```json')[1].split('```')[0].strip()
            elif '```' in ai_response:
                ai_response = ai_response.split('```')[1].split('```')[0].strip()
            
            weather_data = json.loads(ai_response)
            
            # Ensure all required fields exist
            weather_data.setdefault('summary', 'Weather forecast available for the next 10 days')
            weather_data.setdefault('current_condition', 'clear')
            weather_data.setdefault('insights', [])
            weather_data.setdefault('recommendation', '')
            
            # Add location and forecast data
            weather_data['location'] = {
                "city": coords['name'],
                "country": coords['country'],
                "lat": coords['lat'],
                "lon": coords['lon']
            }
            weather_data['current'] = {
                "temp": round(current_temp, 1),
                "feels_like": round(feels_like, 1),
                "temp_max": round(current_temp_max, 1),
                "temp_min": round(current_temp_min, 1),
                "feels_like_max": round(current_feels_max, 1),
                "feels_like_min": round(current_feels_min, 1),
                "precipitation": round(current_precip, 1),
                "rain": round(current_rain, 1),
                "snow": round(current_snow, 1)
            }
            weather_data['forecast'] = forecast_days
            weather_data['alerts'] = alerts
            
            return weather_data
            
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            # Fallback with actual weather data
            condition = "clear"
            if sum(snowfall[:3]) > 5:
                condition = "snowy"
            elif sum(rain[:3]) > 20:
                condition = "rainy"
            elif sum(precipitation[:3]) > 10:
                condition = "cloudy"
            
            return {
                "location": {
                    "city": coords['name'],
                    "country": coords['country'],
                    "lat": coords['lat'],
                    "lon": coords['lon']
                },
                "current": {
                    "temp": round(current_temp, 1),
                    "feels_like": round(feels_like, 1),
                    "temp_max": round(current_temp_max, 1),
                    "temp_min": round(current_temp_min, 1),
                    "feels_like_max": round(current_feels_max, 1),
                    "feels_like_min": round(current_feels_min, 1),
                    "precipitation": round(current_precip, 1),
                    "rain": round(current_rain, 1),
                    "snow": round(current_snow, 1)
                },
                "summary": f"Expect temperatures around {round(current_temp, 1)}°C (feels like {round(feels_like, 1)}°C) with {condition} conditions.",
                "current_condition": condition,
                "insights": [
                    f"Peak temperature reaching {round(max(temps_max[:7]), 1)}°C this week",
                    f"Coolest day will be around {round(min(temps_min[:7]), 1)}°C",
                    f"Total precipitation expected: {round(sum(precipitation[:7]), 1)}mm"
                ],
                "recommendation": "Check the detailed forecast to plan your week ahead",
                "forecast": forecast_days,
                "alerts": alerts,
                "debug_error": str(e)
            }
            
    except Exception as e:
        return {"error": f"Analysis error: {str(e)}"}

# --- Lambda Handler (for AWS Lambda) ---

def lambda_handler(event, context):
    """AWS Lambda handler function for Lambda Function URL."""
    
    # Log the incoming event for debugging
    print(f"Received event: {json.dumps(event)}")
    
    # Handle OPTIONS preflight for CORS
    request_context = event.get('requestContext', {})
    http_method = request_context.get('http', {}).get('method', '')
    
    if http_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': ''
        }
    
    try:
        # Lambda Function URL sends body as string
        body_str = event.get('body', '{}')
        
        # Handle base64 encoded body (if any)
        if event.get('isBase64Encoded', False):
            import base64
            body_str = base64.b64decode(body_str).decode('utf-8')
        
        print(f"Body string: {body_str}")
        
        # Parse the body
        try:
            body = json.loads(body_str) if body_str else {}
        except json.JSONDecodeError:
            body = {}
        
        city = body.get('city', '').strip()
        
        print(f"Processing city: '{city}'")
        
        if not city:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'City name is required'})
            }
        
        forecast = analyze_weather(city)
        
        print(f"Forecast result keys: {list(forecast.keys())}")
        
        # Handle error case
        if "error" in forecast:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(forecast)
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(forecast)
        }
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'Server error: {str(e)}'})
        }

# --- Local CLI Mode (for testing) ---

if __name__ == "__main__":
    """Run locally for testing."""
    city = input("Which city would you like to check? ")
    response = analyze_weather(city)
    print("\n--- WEATHER FORECAST ---\n")
    print(response)
