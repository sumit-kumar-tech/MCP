from typing import Any
import httpx
from typing import Any
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

@mcp.tool()
async def add(a: float, b: float) -> str:
    """Add two numbers together.
    
    Args:
        a: First number
        b: Second number
    """
    result = a + b
    return f"{a} + {b} = {result}"

@mcp.tool()
async def subtract(a: float, b: float) -> str:
    """Subtract second number from first number.
    
    Args:
        a: First number (minuend)
        b: Second number (subtrahend)
    """
    result = a - b
    return f"{a} - {b} = {result}"

@mcp.tool()
async def multiply(a: float, b: float) -> str:
    """Multiply two numbers together.
    
    Args:
        a: First number
        b: Second number
    """
    result = a * b
    return f"{a} × {b} = {result}"

@mcp.tool()
async def divide(a: float, b: float) -> str:
    """Divide first number by second number.
    
    Args:
        a: First number (dividend)
        b: Second number (divisor)
    """
    if b == 0:
        return "Error: Cannot divide by zero!"
    
    result = a / b
    return f"{a} ÷ {b} = {result}"

@mcp.tool()
async def calculate(expression: str) -> str:
    """Calculate a simple mathematical expression with +, -, *, / operations.
    
    Args:
        expression: Mathematical expression as a string (e.g., "5 + 3", "10 * 2 - 5")
    """
    try:
        # Remove whitespace and validate the expression contains only allowed characters
        clean_expr = expression.replace(" ", "")
        allowed_chars = set("0123456789+-*/.()") 
        
        if not all(c in allowed_chars for c in clean_expr):
            return "Error: Expression contains invalid characters. Only numbers and +, -, *, /, (), . are allowed."
        
        # Evaluate the expression safely
        result = eval(clean_expr)
        return f"{expression} = {result}"
        
    except ZeroDivisionError:
        return "Error: Division by zero in expression!"
    except Exception as e:
        return f"Error: Invalid mathematical expression - {str(e)}"

@mcp.tool()
async def percentage(number: float, percent: float) -> str:
    """Calculate percentage of a number.
    
    Args:
        number: The base number
        percent: The percentage to calculate (e.g., 25 for 25%)
    """
    result = (number * percent) / 100
    return f"{percent}% of {number} = {result}"

@mcp.tool()
async def power(base: float, exponent: float) -> str:
    """Calculate base raised to the power of exponent.
    
    Args:
        base: The base number
        exponent: The exponent/power
    """
    try:
        result = base ** exponent
        return f"{base}^{exponent} = {result}"
    except Exception as e:
        return f"Error: Cannot calculate power - {str(e)}"

@mcp.tool()
async def square_root(number: float) -> str:
    """Calculate the square root of a number.
    
    Args:
        number: The number to find square root of
    """
    if number < 0:
        return "Error: Cannot calculate square root of negative number!"
    
    result = number ** 0.5
    return f"√{number} = {result}"

@mcp.tool()
async def solve_steps(expression: str) -> str:
    """Show step-by-step solution for simple arithmetic expressions.
    
    Args:
        expression: Mathematical expression (e.g., "5 + 3 * 2")
    """
    try:
        clean_expr = expression.replace(" ", "")
        allowed_chars = set("0123456789+-*/.()") 
        
        if not all(c in allowed_chars for c in clean_expr):
            return "Error: Expression contains invalid characters."
        
        # For simple demonstration, we'll show the final result
        # In a more complex implementation, you could parse and show each step
        result = eval(clean_expr)
        
        steps = f"""
Step-by-step solution for: {expression}

Following order of operations (PEMDAS/BODMAS):
1. Parentheses/Brackets first
2. Exponents/Orders 
3. Multiplication and Division (left to right)
4. Addition and Subtraction (left to right)

Final result: {expression} = {result}
        """
        return steps.strip()
        
    except Exception as e:
        return f"Error: Cannot solve expression - {str(e)}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
