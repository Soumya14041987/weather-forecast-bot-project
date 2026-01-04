Breaking Down the Weather Forecast Lambda Function

Let me walk you through the heart of our weather app - the weather-forecast.py file. I'll explain everything in plain English, even if you're not a Python expert.

The Big Picture

Think of this file as a smart assistant that:
1. Finds where a city is located
2. Fetches weather data for that location
3. Uses AI to analyze and explain the weather
4. Sends beautiful, formatted results back to your browser

Let's break it down step by step.

---

Part 1: The Setup (Imports)

```python
import json
import requests
import boto3
```

What's happening here?
- json helps us work with data in JSON format (like a universal language for web apps)
- requests lets us talk to external weather APIs
- boto3 is AWS's Python toolkit (our bridge to Amazon Bedrock)

Think of it like gathering your tools before starting a project.

---

Part 2: Finding the City (Geocoding)

```python
def get_coordinates(city_name: str) -> dict:
    """Converts a city name into latitude and longitude coordinates."""
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}..."
    response = requests.get(url).json()
    
    if "results" in response:
        res = response["results"][0]
        return {
            "lat": res["latitude"], 
            "lon": res["longitude"], 
            "name": res["name"], 
            "country": res["country"]
        }
    return {"error": "City not found"}
```

What's happening here?
- You type "London" and we need to know WHERE London is
- We ask a free geocoding API: "Hey, where's London?"
- API responds: "51.5074°N, 0.1278°W in United Kingdom"
- We save this info to fetch weather data

Real-world analogy: Like asking Google Maps for coordinates before planning a trip.

---

Part 3: Getting Weather Data

```python
def get_weather_forecast(lat: float, lon: float) -> dict:
    """Fetches real-time weather data and 10-day forecast."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}..."
    return requests.get(url).json()
```

What's happening here?
- We use the coordinates from Step 2
- We ask Open-Meteo API: "What's the weather like here for the next 10 days?"
- We get back max/min temperatures, precipitation amounts, snowfall data, wind speeds, and "feels like" temperatures

Real-world analogy: Like checking multiple weather channels and combining all their data.

---

Part 4: The AI Magic (Amazon Bedrock)

This is where it gets interesting. We have raw weather data, but we want human-friendly insights.

```python
def analyze_weather(city: str) -> dict:
    coords = get_coordinates(city)
    weather = get_weather_forecast(coords["lat"], coords["lon"])
    
    temps_max = daily.get('temperature_2m_max', [])
    temps_min = daily.get('temperature_2m_min', [])
    precipitation = daily.get('precipitation_sum', [])
```

What's happening here?
1. We gather all the weather numbers
2. We organize them into a neat package
3. We prepare to send them to our AI assistant

The AI Prompt

```python
prompt = f"""Analyze this 10-day weather forecast for {coords['name']}, {coords['country']}:

Current: {current_temp}°C (feels like {feels_like}°C)
Temperature Max (°C): {temps_max[:10]}
Temperature Min (°C): {temps_min[:10]}
Precipitation (mm): {precipitation[:10]}

Create a weather analysis. Respond with ONLY a valid JSON object:
{{
    "summary": "Engaging 2-sentence weather overview",
    "current_condition": "sunny/cloudy/rainy/snowy",
    "insights": ["Insight 1", "Insight 2", "Insight 3"],
    "recommendation": "Activity suggestion"
}}"""
```

What's happening here?
- We're talking to Amazon Bedrock's Nova Lite AI model
- We give it all the weather numbers
- We ask it to explain this weather in a friendly way
- We tell it exactly what format we want back

Real-world analogy: Like asking a meteorologist friend to explain the weather forecast in simple terms.

Calling Amazon Bedrock

```python
response = client.invoke_model(
    modelId='us.amazon.nova-lite-v1:0',
    body=json.dumps({
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"temperature": 0.5, "maxTokens": 1000}
    })
)
```

What's happening here?
- modelId tells which AI model to use (Nova Lite is fast and cheap)
- temperature: 0.5 controls how creative the AI should be (0.5 is balanced)
- maxTokens: 1000 sets the maximum length of response

The AI responds with something like:
```json
{
  "summary": "Pleasant weather expected with mild temperatures and clear skies",
  "current_condition": "sunny",
  "insights": [
    "Maximum temperatures are decreasing steadily",
    "Nighttime temperatures are falling significantly",
    "There is no precipitation expected"
  ],
  "recommendation": "Perfect weather for outdoor activities!"
}
```

---

Part 5: Weather Alerts (Smart Detection)

```python
if day_data["snowfall"] > 5:
    alerts.append(f"Heavy snowfall expected {day_name} ({day_data['snowfall']}mm)")
elif day_data["rain"] > 20:
    alerts.append(f"Heavy rain expected {day_name} ({day_data['rain']}mm)")
elif day_data["windspeed"] > 50:
    alerts.append(f"Strong winds {day_name} (up to {day_data['windspeed']} km/h)")
```

What's happening here?
- We automatically scan the next 3 days
- If we detect dangerous weather, we create alerts
- Examples: "Heavy snowfall expected tomorrow (15mm)" or "Heavy rain expected in 2 days (25mm)" or "Strong winds today (up to 60 km/h)"

Real-world analogy: Like having a weather watchdog that warns you about storms.

---

Part 6: The Lambda Handler (AWS Gateway)

```python
def lambda_handler(event, context):
    """AWS Lambda handler function for Lambda Function URL."""
    
    if http_method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        }
    
    body = json.loads(event.get('body', '{}'))
    city = body.get('city', '').strip()
    
    forecast = analyze_weather(city)
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(forecast)
    }
```

What's happening here?
- This is the entry point where AWS Lambda starts
- When someone types a city in the browser:
  1. Browser sends: {"city": "London"}
  2. Lambda receives it
  3. We call analyze_weather("London")
  4. We send back the full weather report
  5. Browser displays it beautifully

Real-world analogy: Like a receptionist who receives requests and coordinates with different departments.

---

The Complete Flow (Putting It All Together)

User types "Tokyo" in browser
         ↓
Lambda receives: {"city": "Tokyo"}
         ↓
get_coordinates("Tokyo")
         ↓
Returns: {lat: 35.6762, lon: 139.6503}
         ↓
get_weather_forecast(35.6762, 139.6503)
         ↓
Returns: {temps: [15,16,14...], rain: [0,5,10...]}
         ↓
analyze_weather() sends data to Bedrock AI
         ↓
AI analyzes and returns friendly insights
         ↓
We package everything into JSON
         ↓
Browser receives beautiful weather report
         ↓
User sees: "Tokyo will be sunny with temps around 15°C"

---

Key Takeaways

Why this architecture works:

1. Separation of Concerns
   - Each function does ONE thing well
   - Easy to test and debug

2. Error Handling
   - If city not found, show friendly error message
   - If AI fails, fall back to raw data
   - If API is down, handle gracefully

3. Cost Efficiency
   - Only runs when someone requests weather
   - No servers running 24/7
   - Pay only for what you use

4. Scalability
   - Can handle 1 user or 1 million users
   - AWS Lambda scales automatically
   - No infrastructure management

---

Behind the Scenes: What Makes This Special?

Traditional Approach:
Server running 24/7 → Database → Weather API → Manual formatting
Cost: $50-100/month

Our Serverless + AI Approach:
Lambda (on-demand) → AI Analysis → Direct API calls
Cost: $4-5/month

The difference?
- 90% cost reduction
- Automatic scaling
- AI-powered insights
- Zero server maintenance

---

What You Can Learn From This

1. Serverless is powerful - No servers to manage, infinite scale
2. AI makes apps smarter - Raw data becomes human insights
3. Free APIs exist - Open-Meteo is completely free
4. Simple code can do complex things - About 200 lines of Python
5. AWS services integrate beautifully - Lambda + Bedrock + S3

---

Try It Yourself

The complete code is on GitHub. You can:
- Deploy it in 30 minutes
- Customize the AI prompts
- Add more weather features
- Learn AWS serverless architecture

Total cost to run: Less than a cup of coffee per month.

---

Code Statistics

- Total Lines: About 200 lines of Python
- Functions: 3 main functions + 1 Lambda handler
- External APIs: 2 (Geocoding + Weather)
- AWS Services: 2 (Lambda + Bedrock)
- Dependencies: 2 (boto3 + requests)
- Complexity: Low to Medium
- Maintainability: High

---

Next Steps

Want to enhance this project? Here are some ideas:

1. Add Caching - Store weather data for 1 hour to reduce API calls
2. Add More AI Features - Weather comparisons, travel recommendations
3. Add User Accounts - Save favorite cities
4. Add Notifications - Email or SMS alerts for severe weather
5. Add Historical Data - Compare with past years
6. Add Maps - Visual weather maps using Leaflet.js
7. Add Multi-language - Support for different languages

---

Contributing

Found this helpful? Here's how you can contribute:

- Star the repository
- Report bugs or issues
- Suggest new features
- Improve documentation
- Submit pull requests

---

Additional Resources

Learn More About:
- AWS Lambda Documentation
- Amazon Bedrock Documentation
- Open-Meteo API Documentation
- Python Requests Library
- Boto3 Documentation

---

Questions?

Feel free to:
- Open an issue on GitHub
- Comment on the Medium article
- Reach out on Twitter or LinkedIn
- Join the AWS Community Builders program

---

Built with care using AWS Serverless Technologies

Last updated: January 2026
