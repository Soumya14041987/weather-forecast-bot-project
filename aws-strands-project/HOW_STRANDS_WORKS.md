How AWS Strands Agents Understand Which Tools to Use

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

THE MAGIC: FUNCTION CALLING & TOOL DESCRIPTIONS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AWS Strands uses a technique called "Function Calling" (also known as "Tool Use") where the AI model (like Claude or Nova) automatically decides which tools to call based on:

1. Tool Name
2. Tool Description (docstring)
3. Function Parameters
4. User's Prompt

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXAMPLE: HOW IT WORKS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: You Define Tools with @tool Decorator

```python
from strands_agents import Agent, tool

@tool
def get_weather(city: str) -> dict:
    """Get weather forecast for a city."""
    # Implementation here
    return {"temp": 25, "condition": "sunny"}

@tool
def calculate(expression: str) -> float:
    """Calculate a mathematical expression."""
    return eval(expression)

@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    return "Search results..."
```

Step 2: Register Tools with Agent

```python
agent = Agent(
    name="MyAgent",
    model=BedrockModel(model_id="us.amazon.nova-lite-v1:0"),
    tools=[get_weather, calculate, search_web]  # ← Register all tools
)
```

Step 3: Strands Sends Tool Metadata to AI Model

Behind the scenes, Strands converts your tools into this format:

```json
{
  "tools": [
    {
      "name": "get_weather",
      "description": "Get weather forecast for a city.",
      "parameters": {
        "city": {
          "type": "string",
          "description": "City name"
        }
      }
    },
    {
      "name": "calculate",
      "description": "Calculate a mathematical expression.",
      "parameters": {
        "expression": {
          "type": "string",
          "description": "Math expression"
        }
      }
    },
    {
      "name": "search_web",
      "description": "Search the web for information.",
      "parameters": {
        "query": {
          "type": "string",
          "description": "Search query"
        }
      }
    }
  ]
}
```

Step 4: User Asks a Question

```python
result = agent("What's the weather in Tokyo?")
```

Step 5: AI Model Analyzes the Prompt

The AI model (Nova/Claude) thinks:
→ User wants weather information
→ I have a tool called "get_weather"
→ Description says: "Get weather forecast for a city"
→ This matches the user's intent!
→ I need to call: get_weather(city="Tokyo")

Step 6: Strands Executes the Tool

```python
# Strands automatically calls:
result = get_weather("Tokyo")
# Returns: {"temp": 18, "condition": "cloudy"}
```

Step 7: AI Model Uses Tool Result

The AI model receives the tool result and generates a response:
"The weather in Tokyo is currently 18°C with cloudy conditions."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REAL EXAMPLE FROM YOUR WEATHER APP

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your Code:

```python
@tool
def get_weather(city: str) -> dict:
    """Get weather forecast for a city."""
    # Geocoding and weather API calls
    return weather_data

agent = Agent(
    name="WeatherBot",
    model=BedrockModel(model_id="us.amazon.nova-lite-v1:0"),
    tools=[get_weather]  # ← Only one tool registered
)

# User prompt
result = agent("Get weather for Pune and provide a summary")
```

What Happens:

1. User asks: "Get weather for Pune and provide a summary"

2. AI Model thinks:
   → User wants weather for "Pune"
   → I have tool: get_weather(city: str)
   → Description: "Get weather forecast for a city"
   → Perfect match! I'll call: get_weather("Pune")

3. Strands executes: get_weather("Pune")

4. Tool returns:
   ```json
   {
     "location": {"city": "Pune", "country": "India"},
     "current": {"temp": 15.8, "feels_like": 15.0},
     "forecast": [...]
   }
   ```

5. AI Model receives the data and generates:
   "The weather in Pune, India is currently 15.8°C with a feel of 15.0°C..."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KEY FACTORS FOR TOOL SELECTION

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The AI model decides which tool to use based on:

1. Tool Name
   → Descriptive names help: get_weather, calculate, search_web
   → Bad names: func1, do_stuff, helper

2. Docstring (Description)
   → Clear description of what the tool does
   → Example: "Get weather forecast for a city."

3. Parameter Names & Types
   → city: str → AI knows to extract city name
   → expression: str → AI knows to extract math expression

4. User's Prompt
   → "weather in Tokyo" → Matches get_weather tool
   → "calculate 5 + 3" → Matches calculate tool
   → "search for Python tutorials" → Matches search_web tool

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MULTIPLE TOOL CALLS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The AI can call multiple tools in sequence:

Example:

```python
@tool
def get_coordinates(city: str) -> dict:
    """Get latitude and longitude for a city."""
    return {"lat": 18.5, "lon": 73.8}

@tool
def get_weather_by_coords(lat: float, lon: float) -> dict:
    """Get weather for specific coordinates."""
    return {"temp": 25, "condition": "sunny"}

agent = Agent(
    name="WeatherBot",
    model=BedrockModel(model_id="us.amazon.nova-lite-v1:0"),
    tools=[get_coordinates, get_weather_by_coords]
)

result = agent("What's the weather in Pune?")
```

What Happens:

1. AI thinks: "I need coordinates first"
2. Calls: get_coordinates("Pune") → {"lat": 18.5, "lon": 73.8}
3. AI thinks: "Now I can get weather"
4. Calls: get_weather_by_coords(18.5, 73.8) → {"temp": 25, ...}
5. AI generates response with both results

This is called "Tool Chaining" or "Multi-Step Reasoning"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BEST PRACTICES FOR TOOL DESIGN

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Clear Tool Names
   ✅ Good: get_weather, calculate_distance, search_database
   ❌ Bad: func1, helper, do_thing

2. Descriptive Docstrings
   ✅ Good: "Get weather forecast for a city including temperature and conditions."
   ❌ Bad: "Gets weather" or no docstring

3. Meaningful Parameters
   ✅ Good: city: str, start_date: str, max_results: int
   ❌ Bad: x: str, data: dict, stuff: any

4. Return Structured Data
   ✅ Good: Return dict with clear keys
   ❌ Bad: Return unstructured strings

5. Single Responsibility
   ✅ Good: One tool does one thing well
   ❌ Bad: One tool tries to do everything

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXAMPLE: GOOD VS BAD TOOL DESIGN

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Bad Tool Design:

```python
@tool
def func(x):
    """Does stuff."""
    return "result"
```

Problems:
→ Unclear name: "func"
→ Vague description: "Does stuff"
→ No type hints
→ AI won't know when to use this

✅ Good Tool Design:

```python
@tool
def get_weather_forecast(city: str) -> dict:
    """
    Get 7-day weather forecast for a specified city.
    
    Args:
        city: Name of the city (e.g., "Tokyo", "London")
    
    Returns:
        Dictionary with temperature, conditions, and forecast
    """
    # Implementation
    return {
        "city": city,
        "temp": 25,
        "forecast": [...]
    }
```

Benefits:
→ Clear name: "get_weather_forecast"
→ Detailed description
→ Type hints: city: str -> dict
→ AI knows exactly when to use this

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOW TO TEST TOOL SELECTION

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You can test if the AI is selecting the right tools:

```python
# Create agent with multiple tools
agent = Agent(
    name="TestAgent",
    model=BedrockModel(model_id="us.amazon.nova-lite-v1:0"),
    tools=[get_weather, calculate, search_web]
)

# Test different prompts
test_prompts = [
    "What's the weather in Paris?",      # Should use: get_weather
    "Calculate 15 * 23",                 # Should use: calculate
    "Search for Python tutorials",       # Should use: search_web
]

for prompt in test_prompts:
    print(f"\nPrompt: {prompt}")
    result = agent(prompt)
    print(f"Result: {result}")
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEBUGGING: SEE WHICH TOOLS ARE CALLED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Enable logging to see tool calls:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('strands_agents')

# Now when you run the agent, you'll see:
# INFO: Calling tool: get_weather with args: {"city": "Tokyo"}
# INFO: Tool result: {"temp": 18, "condition": "cloudy"}
```

Or check the AgentResult object:

```python
result = agent("Weather in Tokyo")

# Access traces to see tool calls
print(result.metrics.get_summary())
# Shows which tools were called and how long they took
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUMMARY

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

How Strands Knows Which Tool to Use:

1. You define tools with @tool decorator
2. You register tools with Agent(tools=[...])
3. Strands sends tool metadata to AI model
4. AI model analyzes user prompt
5. AI model matches prompt to tool description
6. AI model decides which tool(s) to call
7. Strands executes the tool(s)
8. AI model uses results to generate response

The AI model (Nova/Claude) is trained to understand:
→ Tool names
→ Tool descriptions
→ Parameter types
→ User intent

This is why good tool design (clear names, descriptions, parameters) is crucial!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The magic is in the AI model's ability to understand natural language and match it to available tools automatically!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
