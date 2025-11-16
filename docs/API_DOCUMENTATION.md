# Wellness AI - API Documentation

**Version:** 1.0.0
**Base URL:** `http://localhost:8000/api/v1`
**Authentication:** Bearer JWT Token

---

## Table of Contents

1. [Authentication](#authentication)
2. [Health Metrics](#health-metrics)
3. [EEG Analysis](#eeg-analysis)
4. [Life Optimization](#life-optimization)
5. [Nutrition](#nutrition)
6. [Supplements](#supplements)
7. [AI Coach](#ai-coach)
8. [Recommendations](#recommendations)
9. [Error Handling](#error-handling)

---

## Authentication

All API endpoints (except `/auth/login` and `/auth/register`) require authentication using JWT Bearer tokens.

### Register New User

**Endpoint:** `POST /auth/register`
**Authentication:** None required

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "name": "John Doe",
  "age": 30
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Status Codes:**
- `200`: Success
- `400`: Email already registered
- `422`: Validation error (password < 8 chars, invalid email, etc.)

---

### Login

**Endpoint:** `POST /auth/login`
**Authentication:** None required

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Demo Credentials:**
```json
{
  "email": "demo@wellnessai.com",
  "password": "demo123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Status Codes:**
- `200`: Success
- `401`: Incorrect email or password

---

### Refresh Token

**Endpoint:** `POST /auth/refresh`
**Authentication:** None required

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### Get Current User

**Endpoint:** `GET /auth/me`
**Authentication:** Required

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe"
}
```

---

### Logout

**Endpoint:** `POST /auth/logout`
**Authentication:** Required

**Response:**
```json
{
  "message": "Successfully logged out",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Health Metrics

### Log Health Metrics

**Endpoint:** `POST /health`
**Authentication:** Required

**Request Body:**
```json
{
  "date": "2025-11-16",
  "steps": 8500,
  "calories_burned": 2200,
  "distance_km": 6.5,
  "active_minutes": 45,
  "heart_rate_avg": 75,
  "heart_rate_max": 140,
  "heart_rate_min": 55,
  "sleep_hours": 7.5,
  "sleep_quality_score": 0.85,
  "weight_kg": 70.5,
  "body_fat_percentage": 18.5,
  "stress_level": 0.4,
  "focus_level": 0.75,
  "mood_score": 0.8,
  "notes": "Felt energetic today"
}
```

**Response:**
```json
{
  "id": "metric_123",
  "user_id": "user_456",
  "date": "2025-11-16",
  "steps": 8500,
  ...
  "created_at": "2025-11-16T10:30:00Z"
}
```

**Status Codes:**
- `200`: Success
- `401`: Unauthorized
- `422`: Validation error

---

### Get Health Metrics

**Endpoint:** `GET /health`
**Authentication:** Required

**Query Parameters:**
- `date` (optional): Filter by specific date (YYYY-MM-DD)
- `start_date` (optional): Start of date range
- `end_date` (optional): End of date range

**Example:**
```
GET /health?start_date=2025-11-01&end_date=2025-11-16
```

**Response:**
```json
[
  {
    "id": "metric_123",
    "date": "2025-11-16",
    "steps": 8500,
    "sleep_hours": 7.5,
    ...
  },
  {
    "id": "metric_124",
    "date": "2025-11-15",
    "steps": 7200,
    ...
  }
]
```

---

## EEG Analysis

### Upload EEG Data

**Endpoint:** `POST /eeg/upload`
**Authentication:** Required
**Content-Type:** `multipart/form-data`

**Form Data:**
- `file`: CSV file with EEG data
- `channels` (optional): Number of EEG channels (default: 14)
- `sampling_rate` (optional): Sampling rate in Hz (default: 250)

**CSV Format:**
```csv
timestamp,channel_1,channel_2,channel_3,...
0.000,0.1,0.2,0.3,...
0.004,0.2,0.3,0.4,...
```

**Example (cURL):**
```bash
curl -X POST "http://localhost:8000/api/v1/eeg/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@eeg_data.csv"
```

**Response:**
```json
{
  "analysis_id": "eeg_789",
  "user_id": "user_456",
  "timestamp": "2025-11-16T14:30:00Z",
  "mental_states": {
    "stress": 0.65,
    "focus": 0.45,
    "relaxation": 0.25,
    "drowsiness": 0.15
  },
  "band_powers": {
    "delta": 15.2,
    "theta": 22.1,
    "alpha": 35.6,
    "beta": 18.9,
    "gamma": 8.2
  },
  "recommendations": [
    "High stress detected. Consider a 5-minute breathing exercise.",
    "Beta wave activity suggests mental alertness but may benefit from breaks."
  ]
}
```

---

## Life Optimization

### Create User Profile

**Endpoint:** `POST /life-optimization/profile`
**Authentication:** Required

**Request Body:**
```json
{
  "physical_profile": {
    "age": 30,
    "gender": "male",
    "height_cm": 175,
    "weight_kg": 75,
    "activity_level": "moderate_active"
  },
  "health_profile": {
    "conditions": [],
    "allergies": ["peanuts"],
    "nutrient_deficiencies": ["vitamin_d"]
  },
  "dietary_preferences": {
    "diet_type": "vegetarian",
    "cuisine_preferences": ["indian", "italian", "mediterranean"],
    "disliked_foods": ["mushrooms"],
    "budget_per_week": 100.0,
    "budget_currency": "USD",
    "cooking_skill": "intermediate",
    "cooking_time_available": 45
  },
  "lifestyle_profile": {
    "region": "San Francisco, CA, USA",
    "country_code": "US",
    "timezone": "America/Los_Angeles",
    "occupation": "Software Engineer",
    "work_schedule_type": "remote",
    "typical_work_hours": "9:00-17:00"
  },
  "wellness_goals": {
    "primary_goal": "physical_strength",
    "secondary_goals": ["mental_strength", "flexibility"],
    "timeline": "3_months",
    "urgency": "balanced"
  },
  "personality_profile": {
    "big_five": {
      "openness": 0.75,
      "conscientiousness": 0.65,
      "extraversion": 0.50,
      "agreeableness": 0.80,
      "neuroticism": 0.35
    },
    "chronotype": "early_bird",
    "dosha_type": "vata_pitta",
    "dosha_percentages": {
      "vata": 45,
      "pitta": 40,
      "kapha": 15
    }
  }
}
```

**Response:**
```json
{
  "profile_id": "profile_123",
  "message": "Profile created successfully"
}
```

---

### Generate Meal Plan

**Endpoint:** `POST /life-optimization/meal-plan/generate`
**Authentication:** Required

**Request Body:**
```json
{
  "start_date": "2025-11-16",
  "days": 7
}
```

**Response:**
```json
{
  "meal_plan_id": "plan_456",
  "user_id": "user_123",
  "start_date": "2025-11-16",
  "end_date": "2025-11-22",
  "daily_plans": [
    {
      "date": "2025-11-16",
      "meals": [
        {
          "time": "07:30",
          "type": "breakfast",
          "name": "Oatmeal with Berries",
          "description": "Steel-cut oats with mixed berries and almond butter",
          "ingredients": [
            {
              "name": "Steel-cut oats",
              "quantity": 60,
              "unit": "g",
              "reason": "Complex carbs for sustained energy"
            },
            {
              "name": "Mixed berries",
              "quantity": 100,
              "unit": "g",
              "reason": "Antioxidants and vitamins"
            }
          ],
          "cooking_instructions": [
            "Boil water in a pot",
            "Add oats and reduce heat to simmer",
            "Cook for 20 minutes, stirring occasionally",
            "Top with berries and almond butter"
          ],
          "nutrition": {
            "calories": 420,
            "protein_g": 12,
            "carbs_g": 65,
            "fat_g": 14,
            "fiber_g": 10
          },
          "prep_time_minutes": 25,
          "cost_usd": 3.50,
          "dosha_balance": {
            "vata": 0.3,
            "pitta": 0.5,
            "kapha": 0.2
          }
        }
      ],
      "daily_totals": {
        "calories": 2100,
        "protein_g": 95,
        "carbs_g": 260,
        "fat_g": 70,
        "cost_usd": 18.50
      },
      "meets_goals": true,
      "within_budget": true
    }
  ],
  "weekly_summary": {
    "total_cost_usd": 125.00,
    "avg_calories_per_day": 2100,
    "avg_protein_per_day": 95
  }
}
```

---

### Generate Shopping List

**Endpoint:** `POST /life-optimization/shopping-list/generate`
**Authentication:** Required

**Request Body:**
```json
{
  "start_date": "2025-11-16",
  "end_date": "2025-11-22"
}
```

**Response:**
```json
{
  "shopping_list_id": "list_789",
  "start_date": "2025-11-16",
  "end_date": "2025-11-22",
  "total_items": 28,
  "total_cost": 87.50,
  "currency": "USD",
  "formatted_total_cost": "$87.50",
  "items_by_category": {
    "produce": [
      {
        "name": "Spinach",
        "total_quantity": 450,
        "unit": "g",
        "estimated_cost": 3.50,
        "notes": "Used in 3 meals - Rich in iron"
      }
    ],
    "grains": [...],
    "proteins": [...],
    "dairy": [...],
    "spices": [...],
    "oils": [...]
  },
  "store_recommendations": [
    {
      "store_name": "Whole Foods Market",
      "estimated_total": 92.00,
      "availability": "high"
    },
    {
      "store_name": "Trader Joe's",
      "estimated_total": 75.00,
      "availability": "medium"
    }
  ]
}
```

---

### Export Meal Plan as PDF

**Endpoint:** `GET /life-optimization/pdf/meal-plan/date/{date}`
**Authentication:** Required

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/life-optimization/pdf/meal-plan/date/2025-11-16" \
  -H "Authorization: Bearer <token>" \
  --output meal_plan.pdf
```

**Response:** PDF file download

---

### Export Shopping List as PDF

**Endpoint:** `GET /life-optimization/pdf/shopping-list/current`
**Authentication:** Required

**Response:** PDF file download with checkboxes for each item

---

### Get Food Database

**Endpoint:** `GET /life-optimization/food-database`
**Authentication:** Required

**Query Parameters:**
- `category` (optional): Filter by category (produce, grains, proteins, etc.)
- `diet_type` (optional): Filter by diet type (vegan, vegetarian, etc.)

**Response:**
```json
[
  {
    "name": "Brown Rice",
    "category": "grains",
    "nutrition": {
      "calories_per_100g": 112,
      "protein_g": 2.6,
      "carbs_g": 23.5,
      "fat_g": 0.9,
      "fiber_g": 1.8
    },
    "regional_pricing": {
      "US": 1.99,
      "India": 0.75,
      "UK": 2.50
    },
    "dietary_flags": ["vegan", "vegetarian", "gluten_free"],
    "ayurvedic_properties": {
      "dosha_effects": {
        "vata": "neutral",
        "pitta": "cooling",
        "kapha": "increases"
      }
    }
  }
]
```

---

## Supplements

### Get Supplements Database

**Endpoint:** `GET /supplements`
**Authentication:** Required

**Response:**
```json
[
  {
    "name": "Ashwagandha",
    "category": "adaptogen",
    "benefits": [
      "Reduces stress and anxiety",
      "Improves sleep quality",
      "Lowers cortisol levels"
    ],
    "dosage": {
      "typical": "300-500mg",
      "range": "250-600mg",
      "timing": "Twice daily with meals"
    },
    "contraindications": [
      "Pregnancy",
      "Thyroid disorders"
    ],
    "side_effects": [
      "Mild drowsiness",
      "Stomach upset (rare)"
    ],
    "scientific_evidence": {
      "quality": "strong",
      "pubmed_references": [
        "PMID: 23439798",
        "PMID: 31517876"
      ]
    },
    "ayurvedic_properties": {
      "rasa": "bitter, astringent",
      "virya": "heating",
      "vipaka": "sweet",
      "dosha_effects": {
        "vata": "balances",
        "pitta": "increases slightly",
        "kapha": "neutral"
      }
    }
  }
]
```

---

### Search Supplements

**Endpoint:** `GET /supplements/search`
**Authentication:** Required

**Query Parameters:**
- `query`: Search term (e.g., "stress", "sleep", "energy")

**Example:**
```
GET /supplements/search?query=stress
```

**Response:** Array of supplements matching the search criteria

---

## AI Coach

### Chat with Wellness Coach

**Endpoint:** `POST /coach/chat`
**Authentication:** Required

**Request Body:**
```json
{
  "message": "I'm feeling stressed and have trouble sleeping. What can you recommend?",
  "include_context": true
}
```

**Response:**
```json
{
  "response": "Based on your recent EEG analysis showing elevated stress levels and your sleep quality score of 0.6, I recommend:\n\n1. **Breathing Exercise**: Try box breathing (4-4-4-4) for 5 minutes before bed\n2. **Supplements**: Consider Ashwagandha (300mg) and Magnesium (200mg) in the evening\n3. **Schedule Adjustment**: I notice your bedtime varies. Aim for 10:30 PM consistently\n4. **Diet**: Avoid caffeine after 2 PM. Your meal plan includes calming chamomile tea\n\nWould you like me to guide you through the breathing exercise now?",
  "recommendations": [
    {
      "type": "breathing_exercise",
      "name": "Box Breathing",
      "duration_minutes": 5
    },
    {
      "type": "supplement",
      "name": "Ashwagandha",
      "dosage": "300mg evening"
    }
  ],
  "context_used": {
    "recent_eeg": true,
    "sleep_data": true,
    "meal_plan": true
  }
}
```

---

## Error Handling

### Standard Error Response Format

```json
{
  "detail": "Error message description",
  "status_code": 400
}
```

### Common Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Request successful |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid request data |
| `401` | Unauthorized | Invalid or missing authentication token |
| `403` | Forbidden | Authenticated but not authorized |
| `404` | Not Found | Resource not found |
| `422` | Unprocessable Entity | Validation error |
| `500` | Internal Server Error | Server error |

---

## Rate Limiting

- **Default**: 100 requests per minute per user
- **EEG Upload**: 10 requests per hour per user
- **AI Coach**: 30 requests per hour per user

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1700143200
```

---

## Postman Collection

Download the complete Postman collection: [Wellness_AI.postman_collection.json](./Wellness_AI.postman_collection.json)

**Import Steps:**
1. Open Postman
2. Click "Import" → "Choose Files"
3. Select the collection file
4. Set environment variable `BASE_URL` to `http://localhost:8000`
5. After login, set `ACCESS_TOKEN` variable from response

---

## WebSocket Endpoints (Real-time)

### EEG Live Stream

**Endpoint:** `ws://localhost:8000/ws/eeg/stream`
**Authentication:** Token in query parameter

**Connect:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/eeg/stream?token=<access_token>');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Mental state:', data.mental_states);
};
```

**Message Format:**
```json
{
  "timestamp": "2025-11-16T14:30:05Z",
  "mental_states": {
    "stress": 0.65,
    "focus": 0.45
  },
  "band_powers": {
    "alpha": 35.6,
    "beta": 18.9
  }
}
```

---

## SDK Examples

### Python SDK

```python
import requests

class WellnessAI:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None

    def login(self, email, password):
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        self.token = response.json()["access_token"]
        return self.token

    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def log_health_metrics(self, **metrics):
        return requests.post(
            f"{self.base_url}/api/v1/health",
            json=metrics,
            headers=self.get_headers()
        ).json()

# Usage
client = WellnessAI()
client.login("demo@wellnessai.com", "demo123")
client.log_health_metrics(
    date="2025-11-16",
    steps=8500,
    sleep_hours=7.5
)
```

---

## Support

- **Documentation**: https://docs.wellnessai.com
- **GitHub Issues**: https://github.com/your-org/wellness-ai/issues
- **Email**: support@wellnessai.com

**API Version:** 1.0.0
**Last Updated:** November 16, 2025
