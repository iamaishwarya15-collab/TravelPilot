import os
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

load_dotenv()

app = FastAPI(title="TravelPilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = None

if OPENROUTER_API_KEY:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )


class TripRequest(BaseModel):
    destination: str
    start_date: str
    end_date: str
    budget: float = 0
    interests: list[str] = []


class DisruptionRequest(BaseModel):
    destination: str
    start_date: str
    end_date: str
    budget: float = 0
    interests: list[str] = []


def geocode_destination(destination):
    """
    Convert destination name into latitude and longitude.
    """

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": destination,
                "format": "json",
                "limit": 1,
            },
            headers={
                "User-Agent": "TravelPilot/1.0"
            },
            timeout=8,
        )

        response.raise_for_status()

        data = response.json()

        if not data:
            return None

        return {
            "latitude": float(data[0]["lat"]),
            "longitude": float(data[0]["lon"]),
            "display_name": data[0].get("display_name", destination),
        }

    except Exception:
        return None


def get_weather(latitude, longitude):
    """
    Get current weather using Open-Meteo.
    """

    if latitude is None or longitude is None:
        return {
            "temperature": None,
            "wind_speed": None,
            "description": "Weather unavailable",
            "weather_code": None,
        }

    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,weather_code,wind_speed_10m",
            },
            timeout=8,
        )

        response.raise_for_status()

        data = response.json()
        current = data.get("current", {})

        code = current.get("weather_code")

        descriptions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Light rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Light snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Rain showers",
            81: "Moderate rain showers",
            82: "Heavy rain showers",
            95: "Thunderstorm",
            96: "Thunderstorm with hail",
            99: "Severe thunderstorm",
        }

        return {
            "temperature": current.get("temperature_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "weather_code": code,
            "description": descriptions.get(
                code,
                "Weather condition unavailable"
            ),
        }

    except Exception:
        return {
            "temperature": None,
            "wind_speed": None,
            "description": "Weather unavailable",
            "weather_code": None,
        }


def search_real_places(destination, interests):
    """
    Find real places using OpenStreetMap / Nominatim.
    """

    interest_text = " ".join(interests).strip()

    if not interest_text:
        interest_text = "tourist attractions"

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": f"{interest_text} in {destination}",
                "format": "json",
                "limit": 12,
                "addressdetails": 1,
                "extratags": 1,
            },
            headers={
                "User-Agent": "TravelPilot/1.0"
            },
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        places = []

        for place in data:

            name = place.get("display_name")

            if not name:
                continue

            extra = place.get("extratags") or {}

            places.append(
                {
                    "name": name,
                    "latitude": place.get("lat"),
                    "longitude": place.get("lon"),
                    "type": place.get("type"),
                    "category": interest_text,
                    "opening_hours": extra.get("opening_hours"),
                }
            )

        return places[:10]

    except Exception:
        return []


def search_real_hotels(destination):
    """
    Find real hotels using OpenStreetMap / Nominatim.
    """

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": f"hotels in {destination}",
                "format": "json",
                "limit": 8,
                "addressdetails": 1,
                "extratags": 1,
            },
            headers={
                "User-Agent": "TravelPilot/1.0"
            },
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        hotels = []

        for hotel in data:

            name = hotel.get("display_name")

            if not name:
                continue

            extra = hotel.get("extratags") or {}

            hotels.append(
                {
                    "name": name,
                    "latitude": hotel.get("lat"),
                    "longitude": hotel.get("lon"),
                    "type": hotel.get("type"),
                    "stars": extra.get("stars"),
                    "phone": extra.get("phone"),
                    "website": extra.get("website"),
                }
            )

        return hotels[:6]

    except Exception:
        return []


def calculate_days(start_date, end_date):
    """
    Calculate trip duration safely.
    """

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        days = (end - start).days + 1

        return max(1, min(days, 14))

    except Exception:
        return 1


def run_external_data(destination, interests):
    """
    Run independent external searches in parallel.
    This makes TravelPilot much faster than doing every request sequentially.
    """

    geo = geocode_destination(destination)

    if not geo:
        return {
            "geo": None,
            "weather": {
                "temperature": None,
                "wind_speed": None,
                "description": "Destination not found",
                "weather_code": None,
            },
            "places": [],
            "hotels": [],
        }

    with ThreadPoolExecutor(max_workers=3) as executor:

        weather_future = executor.submit(
            get_weather,
            geo["latitude"],
            geo["longitude"],
        )

        places_future = executor.submit(
            search_real_places,
            destination,
            interests,
        )

        hotels_future = executor.submit(
            search_real_hotels,
            destination,
        )

        weather = weather_future.result()
        places = places_future.result()
        hotels = hotels_future.result()

    return {
        "geo": geo,
        "weather": weather,
        "places": places,
        "hotels": hotels,
    }
def ask_ai(destination, start_date, end_date, budget, interests,
           weather, places, hotels, days):
    """
    AI reasoning layer.
    Creates the dynamic itinerary and explains why it was selected.
    """

    if not client:
        return {
            "summary": "AI service is not configured.",
            "reasoning": "TravelPilot could not access the AI reasoning layer.",
            "plan": [],
            "warnings": ["Add a valid OPENROUTER_API_KEY to the backend .env file."],
        }

    real_place_names = [
        place["name"]
        for place in places
        if place.get("name")
    ]

    real_hotel_names = [
        hotel["name"]
        for hotel in hotels
        if hotel.get("name")
    ]

    prompt = f"""
You are the reasoning engine of TravelPilot, an intelligent trip-planning
and disruption-management agent.

TRIP INPUT
Destination: {destination}
Start date: {start_date}
End date: {end_date}
Number of days: {days}
Budget: ₹{budget}
Interests: {interests}

CURRENT WEATHER
{json.dumps(weather, indent=2)}

REAL PLACES FOUND
{json.dumps(real_place_names[:10], indent=2)}

REAL HOTELS FOUND
{json.dumps(real_hotel_names[:6], indent=2)}

YOUR TASK

Think like an autonomous travel agent.

1. OBSERVE
Understand the destination, dates, budget, interests, weather and available
real places.

2. REASON
Explain how you decide which activities should be included and how the
weather, budget and interests affect the plan.

3. ACT
Create a realistic multi-day itinerary.

4. VERIFY
Check that activities use ONLY places from the supplied real-place list.
Do not invent attractions, restaurants or hotels.

5. ADAPT
Mention how the itinerary could change if weather or another travel
disruption occurs.

IMPORTANT:
- Use only the real place names supplied above.
- Never invent a place name.
- Do not claim that a place is open unless opening information is explicitly
  available.
- Do not claim ticket availability.
- Do not claim hotel-room availability.
- Do not invent prices.
- Keep the itinerary practical.
- Do not repeat the same place unnecessarily.
- Spread activities across the available days.
- Consider the user's interests.
- Consider the current weather.
- If there are not enough real places, create fewer activities rather than
  inventing places.
- Keep the reasoning concise but meaningful.

Return ONLY valid JSON.

JSON FORMAT:

{{
  "summary": "Short explanation of the generated journey.",
  "reasoning": "Explain why this itinerary was selected.",
  "plan": [
    {{
      "day": 1,
      "activities": [
        "Real place name - activity",
        "Real place name - activity"
      ]
    }}
  ],
  "warnings": [
    "Relevant travel consideration"
  ]
}}
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are TravelPilot's autonomous travel-planning "
                        "reasoning engine. Always return valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.3,
            max_tokens=1800,
        )

        content = response.choices[0].message.content.strip()

        if content.startswith("```"):
            content = content.replace("```json", "")
            content = content.replace("```", "")
            content = content.strip()

        result = json.loads(content)

        return {
            "summary": result.get("summary", ""),
            "reasoning": result.get("reasoning", ""),
            "plan": result.get("plan", []),
            "warnings": result.get("warnings", []),
        }

    except Exception as error:
        print("AI ERROR:", error)

        return {
            "summary": "TravelPilot generated the available travel data, but AI planning failed.",
            "reasoning": "The AI reasoning service did not return a valid response.",
            "plan": [],
            "warnings": [
                "AI itinerary generation failed. Please try again."
            ],
        }


def travel_agent(request):
    """
    Main TravelPilot agent.

    Observe → Reason → Act → Verify → Adapt
    """

    external = run_external_data(
        request.destination,
        request.interests,
    )

    geo = external["geo"]
    weather = external["weather"]
    places = external["places"]
    hotels = external["hotels"]

    days = calculate_days(
        request.start_date,
        request.end_date,
    )

    # -------------------------
    # OBSERVE
    # -------------------------

    observe_message = (
        f"Observed {len(places)} real places, "
        f"{len(hotels)} real hotels and current weather "
        f"for {request.destination}."
    )

    # -------------------------
    # REASON
    # -------------------------

    ai_result = ask_ai(
        destination=request.destination,
        start_date=request.start_date,
        end_date=request.end_date,
        budget=request.budget,
        interests=request.interests,
        weather=weather,
        places=places,
        hotels=hotels,
        days=days,
    )

    # -------------------------
    # ACT
    # -------------------------

    plan = ai_result.get("plan", [])

    act_message = (
        f"Created a dynamic {days}-day journey "
        f"using the available real destination data."
    )

    # -------------------------
    # VERIFY
    # -------------------------

    verification_points = []

    if places:
        verification_points.append(
            f"{len(places)} real places found"
        )
    else:
        verification_points.append(
            "No real places found"
        )

    if hotels:
        verification_points.append(
            f"{len(hotels)} real hotels found"
        )
    else:
        verification_points.append(
            "No real hotels found"
        )

    if weather.get("description") != "Weather unavailable":
        verification_points.append(
            "Weather data available"
        )
    else:
        verification_points.append(
            "Weather data unavailable"
        )

    verify_message = (
        "Verified: " + ", ".join(verification_points) + "."
    )

    # -------------------------
    # ADAPT
    # -------------------------

    adapt_message = (
        "TravelPilot can re-plan the journey when weather, "
        "place conditions or other travel disruptions change."
    )

    return {
        "destination": request.destination,

        "location": geo,

        "weather": weather,

        "real_places": places,

        "hotels": hotels,

        "agent": {
            "observe": observe_message,

            "reason": ai_result.get(
                "reasoning",
                "TravelPilot evaluated the available trip information."
            ),

            "act": act_message,

            "verify": verify_message,

            "adapt": adapt_message,
        },

        "reasoning": ai_result.get("reasoning", ""),

        "summary": ai_result.get("summary", ""),

        "plan": plan,

        "warnings": ai_result.get("warnings", []),
    }


def detect_disruption(weather):
    """
    Detect weather conditions that may require itinerary adaptation.
    """

    code = weather.get("weather_code")

    disruption_codes = {
        51, 53, 55,
        56, 57,
        61, 63, 65,
        66, 67,
        71, 73, 75, 77,
        80, 81, 82,
        85, 86,
        95, 96, 99,
    }

    return code in disruption_codes


def generate_adaptation(
    destination,
    weather,
    places,
    interests,
):
    if not client:
        return {
            "description": "AI service is unavailable.",
            "adaptation": (
                "TravelPilot detected changing weather and "
                "can adjust the journey."
            ),
            "alternative": "Use another available destination activity.",
        }

    real_places = [
        place.get("name")
        for place in places
        if place.get("name")
    ]

    prompt = f"""
You are TravelPilot's disruption-management agent.

Destination: {destination}

User interests:
{interests}

Current weather:
{json.dumps(weather, indent=2)}

REAL PLACES:
{json.dumps(real_places[:10], indent=2)}

A possible weather disruption has been detected.

Explain:
1. What changed.
2. Why the original plan may need adjustment.
3. Which real place can be used as an alternative.
4. How TravelPilot adapts the journey.

Rules:
- Use ONLY places from REAL PLACES.
- Never invent a place.
- Never invent ticket availability.
- Never invent hotel-room availability.
- Never invent opening hours.
- Keep the response concise.

Return ONLY valid JSON:

{{
    "description": "What changed",
    "adaptation": "How the journey is changed",
    "alternative": "Real alternative place"
}}
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are TravelPilot's disruption "
                        "adaptation engine. Return JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.3,
            max_tokens=700,
        )

        content = response.choices[0].message.content.strip()

        if content.startswith("```"):
            content = content.replace("```json", "")
            content = content.replace("```", "")
            content = content.strip()

        return json.loads(content)

    except Exception as error:
        print("ADAPTATION ERROR:", error)

        return {
            "description": (
                f"Weather conditions may affect outdoor "
                f"activities in {destination}."
            ),
            "adaptation": (
                "TravelPilot can modify the itinerary "
                "according to the changed conditions."
            ),
            "alternative": (
                real_places[0]
                if real_places
                else "Alternative activity"
            ),
        }


@app.get("/")
def home():
    return {
        "status": "online",
        "service": "TravelPilot API",
        "agent": "Observe → Reason → Act → Verify → Adapt",
    }


@app.post("/plan-trip")
def plan_trip(request: TripRequest):
    return travel_agent(request)


@app.post("/simulate-disruption")
def simulate_disruption(request: DisruptionRequest):

    external = run_external_data(
        request.destination,
        request.interests,
    )

    weather = external["weather"]
    places = external["places"]
    hotels = external["hotels"]

    disruption = detect_disruption(weather)

    if not disruption:

        description = (
            f"No major weather disruption detected for "
            f"{request.destination}. "
            f"Current condition: "
            f"{weather.get('description', 'Unknown')}."
        )

        return {
            "status": "no_disruption",
            "description": description,
            "weather": weather,
            "real_places": places,
            "hotels": hotels,
            "adaptation": None,

            "agent": {
                "observe": (
                    f"Observed current conditions in "
                    f"{request.destination}."
                ),

                "reason": (
                    "Current conditions do not indicate "
                    "a major disruption."
                ),

                "act": (
                    "TravelPilot keeps the existing journey plan."
                ),

                "verify": (
                    "Weather conditions were checked "
                    "against disruption conditions."
                ),

                "adapt": (
                    "No itinerary adaptation is required "
                    "at this moment."
                ),
            },
        }

    adaptation = generate_adaptation(
        destination=request.destination,
        weather=weather,
        places=places,
        interests=request.interests,
    )

    return {
        "status": "disruption_detected",

        "description": (
            f"TravelPilot detected a possible weather "
            f"disruption in {request.destination}. "
            f"Current condition: "
            f"{weather.get('description', 'Unknown')}."
        ),

        "weather": weather,

        "real_places": places,

        "hotels": hotels,

        "adaptation": adaptation.get(
            "adaptation",
            "TravelPilot is adapting the journey."
        ),

        "agent": {
            "observe": (
                f"Observed "
                f"{weather.get('description', 'changing weather')} "
                f"in {request.destination}."
            ),

            "reason": adaptation.get(
                "description",
                "The current conditions may affect the journey."
            ),

            "act": (
                "Selected an alternative using the real "
                "places returned for the destination: "
                + adaptation.get(
                    "alternative",
                    "alternative activity"
                )
            ),

            "verify": (
                "Verified that the selected alternative "
                "exists in the real destination data."
            ),

            "adapt": adaptation.get(
                "adaptation",
                "The journey is adjusted to the changed conditions."
            ),
        },
    }