AWS Strands Weather Forecast Bot - Complete EC2 Deployment Guide

This guide walks you through creating and running the weather-forecast.py application directly on your Ubuntu EC2 instance using AWS Strands Agents SDK.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PART 1: INITIAL EC2 SETUP

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Launch Your EC2 Instance

Launch an Ubuntu EC2 instance with these specifications:

→ AMI: Ubuntu 22.04 LTS (or 20.04 LTS)
→ Instance Type: t2.medium or larger (recommended for Bedrock operations)
→ Storage: 20 GB minimum
→ Security Group: Allow SSH (port 22) from your IP

Important: Attach an IAM role with these permissions:
→ bedrock:InvokeModel
→ logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents

Step 2: Connect to Your Instance

```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

Step 3: Upload and Run the Setup Script

From your local machine:
```bash
scp -i your-key.pem ec2-setup.sh ubuntu@your-ec2-ip:~/
```

On the EC2 instance:
```bash
chmod +x ec2-setup.sh
./ec2-setup.sh
```

Wait for the setup to complete (approximately 5-10 minutes).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PART 2: CONFIGURE AWS CREDENTIALS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Option A: Using IAM Role (Recommended for EC2)

If you attached an IAM role to your EC2 instance, credentials are automatic.
Verify with:
```bash
aws sts get-caller-identity
```

Option B: Using AWS Configure

```bash
aws configure
```

Enter when prompted:
→ AWS Access Key ID: your-access-key
→ AWS Secret Access Key: your-secret-key
→ Default region name: us-east-1
→ Default output format: json

Verify Bedrock access:
```bash
aws bedrock list-foundation-models --region us-east-1
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PART 3: CREATE THE WEATHER FORECAST APPLICATION

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Navigate to the Application Directory

```bash
cd /opt/aws-strands-agent
source venv/bin/activate
```

You should see (venv) in your prompt.

Step 2: Create the Weather Forecast Bot File

Create the main application file:

```bash
nano weather-forecast.py
```

Or use vi if you prefer:
```bash
vi weather-forecast.py
```

Step 3: Copy the Application Code

Paste the following complete application code into the file:

```python
import json
import requests
from strands_agents import Agent, tool
from strands_agents.models import BedrockModel

@tool
def get_coordinates(city_name: str) -> dict:
    """Converts a city name into latitude and longitude coordinates.
    
    Args:
        city_name: The name of the city to geocode
        
    Returns:
        Dictionary with lat, lon, name, and country or error message
    """
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
    response = requests.get(url).json()
    if "results" in response:
        res = response["results"][0]
        return {"lat": res["latitude"], "lon": res["longitude"], "name": res["name"], "country": res["country"]}
    return {"error": "City not found"}

@tool
def get_weather_forecast(lat: float, lon: float) -> dict:
    """Fetches real-time weather data and 10-day forecast for given coordinates.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        
    Returns:
        Dictionary with weather forecast data
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,precipitation_probability_max,snowfall_sum,rain_sum,showers_sum,windspeed_10m_max&current=temperature_2m,apparent_temperature,precipitation,rain,snowfall&timezone=auto&forecast_days=14"
    return requests.get(url).json()

# Initialize Bedrock model for Strands Agent
bedrock_model = BedrockModel(
    model_id='us.amazon.nova-lite-v1:0',
    region_name='us-east-1'
)

# Create Strands Agent with tools
weather_agent = Agent(
    name="WeatherForecastAgent",
    model=bedrock_model,
    tools=[get_coordinates, get_weather_forecast],
    instructions="""You are a weather forecast assistant that provides detailed weather analysis.
    Use the available tools to get coordinates and weather data, then provide insightful analysis."""
)

def analyze_weather(city: str) -> dict:
    """Main weather analysis function using Strands Agent and Bedrock - returns structured data."""
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
        
        # Create prompt for AI analysis using Strands Agent
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
        
        # Use Strands Agent to generate response
        agent_response = weather_agent.run(prompt)
        ai_response = agent_response.content.strip()
        
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

if __name__ == "__main__":
    """Run locally for testing."""
    city = input("Which city would you like to check? ")
    response = analyze_weather(city)
    print("\n--- WEATHER FORECAST ---\n")
    print(json.dumps(response, indent=2))
```

Step 4: Save the File

If using nano:
→ Press Ctrl + X
→ Press Y to confirm
→ Press Enter to save

If using vi:
→ Press Esc
→ Type :wq
→ Press Enter

Step 5: Verify the File

```bash
ls -lh weather-forecast.py
cat weather-forecast.py | head -20
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PART 4: RUN THE WEATHER FORECAST BOT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Ensure Virtual Environment is Active

```bash
cd /opt/aws-strands-agent
source venv/bin/activate
```

Step 2: Run the Application

```bash
python weather-forecast.py
```

Step 3: Test with a City

When prompted, enter a city name:
```
Which city would you like to check? San Francisco
```

Expected Output:
```json
--- WEATHER FORECAST ---

{
  "location": {
    "city": "San Francisco",
    "country": "United States",
    "lat": 37.7749,
    "lon": -122.4194
  },
  "current": {
    "temp": 18.5,
    "feels_like": 17.2,
    "temp_max": 21.0,
    "temp_min": 15.0
  },
  "summary": "Pleasant weather with mild temperatures...",
  "current_condition": "partly-cloudy",
  "insights": [
    "Peak temperature reaching 23.5°C this week",
    "Coolest day will be around 12.0°C",
    "Total precipitation expected: 5.2mm"
  ],
  "recommendation": "Perfect weather for outdoor activities!",
  "forecast": [...],
  "alerts": []
}
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PART 5: CREATE A MULTI-CITY TEST SCRIPT (OPTIONAL)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Create a test script to demo multiple cities:

```bash
nano test_multiple_cities.py
```

Paste this code:

```python
#!/usr/bin/env python3
"""Test weather forecast bot with multiple cities"""

from weather_forecast import analyze_weather
import json

def main():
    cities = ["San Francisco", "Tokyo", "London", "Paris", "New York"]
    
    print("=" * 70)
    print("AWS Strands Weather Forecast Bot - Multi-City Demo")
    print("=" * 70)
    print()
    
    for city in cities:
        print(f"\n{'─' * 70}")
        print(f"Fetching forecast for: {city}")
        print('─' * 70)
        
        try:
            result = analyze_weather(city)
            
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"\nLocation: {result['location']['city']}, {result['location']['country']}")
                print(f"Current: {result['current']['temp']}°C (feels like {result['current']['feels_like']}°C)")
                print(f"Summary: {result['summary']}")
                print(f"Condition: {result['current_condition']}")
                
                if result.get('insights'):
                    print("\nInsights:")
                    for idx, insight in enumerate(result['insights'], 1):
                        print(f"  {idx}. {insight}")
                
                if result.get('recommendation'):
                    print(f"\nRecommendation: {result['recommendation']}")
                
                if result.get('alerts'):
                    print("\nAlerts:")
                    for alert in result['alerts']:
                        print(f"  ⚠ {alert}")
        
        except Exception as e:
            print(f"Error: {str(e)}")
    
    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
```

Save and run:
```bash
chmod +x test_multiple_cities.py
python test_multiple_cities.py
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PART 6: TROUBLESHOOTING

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issue 1: ModuleNotFoundError: No module named 'strands_agents'

Solution:
```bash
source /opt/aws-strands-agent/venv/bin/activate
pip install strands-agents strands-agents-tools
```

Verify installation:
```bash
pip list | grep strands
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issue 2: AccessDeniedException from Bedrock

Solution A - Check IAM Role:
```bash
aws sts get-caller-identity
```

Solution B - Verify Bedrock Access:
```bash
aws bedrock list-foundation-models --region us-east-1 | grep nova
```

Solution C - Request Model Access:
→ Go to AWS Console
→ Navigate to Bedrock service
→ Click "Model access" in left menu
→ Request access to "Nova Lite" model

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issue 3: City not found error

Solution:
Try with more specific city names:
→ "Springfield, USA" instead of "Springfield"
→ "Paris, France" instead of just "Paris"
→ Use major city names for better results

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issue 4: Timeout or slow response

Solution:
→ Bedrock calls can take 2-5 seconds
→ This is normal for AI model inference
→ Consider implementing caching for production use

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issue 5: JSON parsing errors

Solution:
The application has fallback logic built-in. If you see "debug_error" in output:
→ The AI response wasn't valid JSON
→ Fallback data is provided automatically
→ This is expected occasionally with AI models

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PART 7: VERIFY STRANDS AGENT IS WORKING

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Test the Strands Agent components individually:

Test 1 - Verify Tools:
```bash
python -c "
from weather_forecast import get_coordinates
result = get_coordinates('Tokyo')
print(result)
"
```

Expected output:
```
{'lat': 35.6895, 'lon': 139.6917, 'name': 'Tokyo', 'country': 'Japan'}
```

Test 2 - Verify Weather API:
```bash
python -c "
from weather_forecast import get_weather_forecast
result = get_weather_forecast(35.6895, 139.6917)
print('Current temp:', result['current']['temperature_2m'])
"
```

Test 3 - Verify Bedrock Model:
```bash
python -c "
from strands_agents.models import BedrockModel
model = BedrockModel(model_id='us.amazon.nova-lite-v1:0', region_name='us-east-1')
print('Bedrock model initialized:', model.model_id)
"
```

Test 4 - Full Integration Test:
```bash
python -c "
from weather_forecast import analyze_weather
result = analyze_weather('London')
print('City:', result.get('location', {}).get('city'))
print('Temp:', result.get('current', {}).get('temp'))
print('Summary:', result.get('summary', 'N/A')[:100])
"
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PART 8: MONITORING AND LOGS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Enable detailed logging (optional):

Create a logging configuration:
```bash
nano weather_forecast_with_logging.py
```

Add at the top of your file:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/aws-strands-agent/weather_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

Then add logging statements in your functions:
```python
logger.info(f"Fetching coordinates for city: {city}")
logger.info(f"Calling Bedrock model: {bedrock_model.model_id}")
logger.info(f"Weather analysis complete for {city}")
```

View logs:
```bash
tail -f /opt/aws-strands-agent/weather_bot.log
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PART 9: NEXT STEPS FOR PRODUCTION

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Package for AWS Lambda

```bash
cd /opt/aws-strands-agent
mkdir lambda-package
pip install -t lambda-package/ boto3 requests strands-agents strands-agents-tools
cp weather-forecast.py lambda-package/
cd lambda-package
zip -r ../weather-bot-lambda.zip .
```

Download to local machine:
```bash
scp -i your-key.pem ubuntu@your-ec2-ip:/opt/aws-strands-agent/weather-bot-lambda.zip .
```

2. Set Up API Gateway

→ Create Lambda function with the zip file
→ Add Lambda Function URL or API Gateway
→ Configure CORS for web access
→ Set timeout to 60 seconds

3. Add Caching

Implement Redis or DynamoDB caching to reduce API calls and costs.

4. Implement Rate Limiting

Use API Gateway rate limiting or Lambda concurrency limits.

5. Set Up Monitoring

→ Enable CloudWatch Logs
→ Create CloudWatch Alarms for errors
→ Set up X-Ray tracing for performance monitoring

6. Security Enhancements

→ Use VPC endpoints for Bedrock
→ Implement API key authentication
→ Enable AWS WAF for DDoS protection
→ Rotate credentials regularly

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUMMARY

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You have successfully:

✓ Set up Ubuntu EC2 instance with AWS Strands Agents SDK
✓ Created the weather-forecast.py application directly on EC2
✓ Configured AWS credentials and Bedrock access
✓ Tested the weather forecast bot with real cities
✓ Verified all Strands Agent components are working
✓ Learned troubleshooting techniques
✓ Prepared for production deployment

Your weather forecast bot is now running on EC2 using:
→ AWS Strands Agents SDK for agent orchestration
→ AWS Bedrock Nova Lite for AI-powered insights
→ Open-Meteo API for real-time weather data
→ Custom tools decorated with @tool for agent use

For questions or issues, refer to:
→ AWS Strands Agents Documentation: https://strandsagents.com/
→ AWS Bedrock Documentation: https://docs.aws.amazon.com/bedrock/
→ SETUP_INSTRUCTIONS.txt in /opt/aws-strands-agent/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Happy coding with AWS Strands Agents!

Last Updated: January 9, 2026
