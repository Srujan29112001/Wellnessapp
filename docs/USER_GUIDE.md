# Wellness AI - User Guide

**Version:** 1.0.0
**Platform:** Web Application (Streamlit)

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard](#dashboard)
3. [Life Optimization](#life-optimization)
4. [My Plan](#my-plan)
5. [EEG Analysis](#eeg-analysis)
6. [AI Coach](#ai-coach)
7. [Health Metrics](#health-metrics)
8. [Nutrition](#nutrition)
9. [Supplements](#supplements)
10. [Settings](#settings)
11. [Tips & Best Practices](#tips--best-practices)
12. [Troubleshooting](#troubleshooting)

---

## Getting Started

### 1. First-Time Login

When you first access the Wellness AI application, you'll see the login screen.

**Options:**

**A. Demo Account** (Quick Start)
- Click the "Demo" button
- Credentials: `demo@wellnessai.com` / `demo123`
- Pre-populated with sample data for exploration

**B. Create New Account**
1. Click the "Register" tab
2. Fill in:
   - Full Name
   - Email address
   - Password (minimum 8 characters)
   - Confirm Password
   - Age (optional)
3. Click "Create Account"
4. You'll be logged in automatically

**C. Existing Account**
1. Enter your email and password
2. Click "Login"

![Login Screen](./images/login_screen.png)

---

### 2. Navigation

The application uses a **sidebar menu** on the left to navigate between pages:

- 🏠 **Dashboard** - Overview of your wellness metrics
- 🌟 **Life Optimization** - Create your personalized profile
- 📅 **My Plan** - View and manage your daily meal plans & schedules
- 🧠 **EEG Analysis** - Upload and analyze brainwave data
- 💬 **AI Coach** - Chat with your wellness AI assistant
- 📊 **Health Metrics** - Track fitness and vitals
- 🥗 **Nutrition** - Log meals and track nutrition
- 💊 **Supplements** - Browse supplement database and track intake
- ⚙️ **Settings** - Manage your profile and preferences

**User Info:**
- Your name and email are displayed at the bottom of the sidebar
- Click "🚪 Logout" to sign out

---

## Dashboard

The **Dashboard** is your wellness command center, showing a high-level overview of your health.

### Sections:

#### 1. Wellness Summary
- **Overall Wellness Score** (0-100): Combines physical, mental, emotional, spiritual, and nutritional dimensions
- **Color-coded indicators**:
  - Green (80-100): Excellent
  - Yellow (60-79): Good
  - Orange (40-59): Needs Attention
  - Red (<40): Requires Focus

#### 2. Today's Metrics
- Steps taken
- Calories burned
- Sleep hours
- Current stress level (from EEG or self-reported)
- Mood score

#### 3. Stress Trends (7-Day Chart)
- Line graph showing stress levels over the past week
- Helps identify patterns (e.g., stress spikes on Mondays)

#### 4. Personalized Recommendations
- AI-generated suggestions based on your data
- Examples:
  - "Your sleep quality has decreased. Consider going to bed 30 minutes earlier."
  - "Great job! You've hit your step goal for 5 days in a row."
  - "High stress detected. Try a 5-minute breathing exercise."

**💡 Tip:** Check the dashboard every morning to start your day with awareness of your wellness state.

---

## Life Optimization

This is where you create your comprehensive wellness profile for personalized recommendations.

### The 9-Step Assessment

Click **"Start Assessment"** to begin the guided wizard:

#### Step 1: Basic Information
- Birth date
- Gender
- Current location (for regional food pricing and availability)

#### Step 2: Physical Profile
- Height & Weight → Calculates BMI automatically
- Activity Level:
  - Sedentary (desk job, little exercise)
  - Light Active (1-3 days/week exercise)
  - Moderate Active (3-5 days/week)
  - Very Active (6-7 days/week)
  - Extremely Active (athlete or physical job)

#### Step 3: Health History
- Medical conditions (diabetes, hypertension, etc.)
- Allergies (food allergies and intolerances)
- Current medications
- Nutrient deficiencies (if known from blood tests)
- Digestive issues
- Family medical history

**⚠️ Note:** This information is used solely for personalized recommendations. Always consult a healthcare professional before making medical decisions.

#### Step 4: Dietary Preferences
- **Diet Type:**
  - Vegan
  - Vegetarian
  - Pescatarian
  - Non-Vegetarian
  - Keto
  - Paleo

- **Cuisine Preferences:** Select your favorites (Indian, Italian, Mexican, Chinese, Mediterranean, etc.)
- **Budget:** Weekly food budget in your local currency
- **Cooking Skill:** Beginner / Intermediate / Advanced
- **Cooking Time:** Minutes available per meal (15, 30, 45, 60+)
- **Meal Prep Preference:** Daily cooking, batch cooking, or mix

#### Step 5: Wellness Goals
- **Primary Goal:**
  - Physical Strength (speed, flexibility, strength)
  - Mental Strength (focus, memory, cognitive performance)
  - Spiritual Strength (meditation, inner peace)
  - Weight Loss
  - Muscle Gain
  - Endurance
  - Longevity

- **Secondary Goals:** Select up to 3 additional goals
- **Timeline:** 1 month, 3 months, 6 months, or 1 year
- **Urgency:** Gradual, Balanced, or Aggressive

#### Step 6: Personality Assessment (Big Five Test)
- 44 questions measuring OCEAN traits:
  - **Openness** - Creativity, curiosity, openness to new experiences
  - **Conscientiousness** - Organization, discipline, planning
  - **Extraversion** - Social energy, outgoingness
  - **Agreeableness** - Compassion, cooperation, trust
  - **Neuroticism** - Emotional stability, stress response

- Rate each statement on a 1-5 scale (Strongly Disagree to Strongly Agree)
- Takes ~5-10 minutes
- Used to personalize meal preferences and exercise recommendations

#### Step 7: Chronotype & Sleep
- **Chronotype:**
  - Early Bird (morning person, best focus 9-11 AM)
  - Night Owl (evening person, best focus 3-8 PM)
  - Intermediate (flexible)

- **Sleep Preferences:**
  - Ideal sleep duration (hours)
  - Preferred bedtime
  - Preferred wake time
  - Current sleep quality (1-10)
  - Sleep issues (insomnia, sleep apnea, etc.)

#### Step 8: Dosha Assessment (Ayurvedic)
- 15-20 questions about physical and mental characteristics
- Determines your Ayurvedic constitution:
  - **Vata** (air/space) - Quick, creative, changeable
  - **Pitta** (fire/water) - Intense, focused, driven
  - **Kapha** (earth/water) - Stable, calm, grounded
  - Combinations (e.g., Vata-Pitta)

- Results show percentage breakdown (e.g., 45% Vata, 40% Pitta, 15% Kapha)

#### Step 9: Spiritual Wellness (Optional)
- Spiritual orientation (Yogic, Buddhist, Hindu, Secular, etc.)
- Meditation experience (Beginner, Intermediate, Advanced)
- Daily practice minutes
- Preferred meditation styles (Mindfulness, Loving-Kindness, Transcendental, etc.)
- Chakra work interest
- Astrological system preference (Vedic, Western, Chinese, None)
- Spiritual goals (reduce stress, inner peace, develop intuition, etc.)

**Final Step:** Review your profile and click **"Generate My Plan"**

---

## My Plan

After completing the Life Optimization assessment, access your personalized plans here.

### Daily Meal Plan

**Features:**
- **Breakfast, Lunch, Dinner, Snacks** - All optimized for your goals
- **For Each Meal:**
  - Name & Description
  - Ingredients with quantities (e.g., "200g spinach - Rich in iron")
  - Step-by-step cooking instructions
  - Prep time
  - Nutrition breakdown (calories, protein, carbs, fat, fiber)
  - Cost estimate
  - Ayurvedic dosha balance
  - Timing reason (e.g., "Lunch at 12:30 PM - Pitta dosha strongest, optimal digestion")

- **Daily Summary:**
  - Total calories
  - Total macros (protein, carbs, fat)
  - Total cost
  - "✓ Meets Goals" / "✓ Within Budget" indicators

**Actions:**
- **📄 Export as PDF** - Download meal plan with all details
- **🔄 Regenerate Plan** - Get a new meal plan for variety
- **📝 Customize** - Swap individual meals (coming soon)

### Daily Schedule

**Features:**
- **Optimized Timeline:**
  - Wake time (based on chronotype)
  - Morning routine (meditation, exercise)
  - Work blocks (aligned with your energy peaks)
  - Meal times (Ayurvedic timing)
  - Breaks (breathing exercises, walks)
  - Evening wind-down
  - Bedtime (for optimal sleep)

- **For Each Activity:**
  - Time & Duration
  - Activity name
  - Reason/Rationale (e.g., "Morning meditation - Vata dosha period, ideal for spiritual practices")

- **Energy Forecast:**
  - Morning: High/Peak/Moderate
  - Afternoon: Moderate/Low
  - Evening: Low/Moderate

**Actions:**
- **📄 Export as PDF** - Print your schedule
- **🔄 Regenerate** - Adjust for different days
- **⏰ Sync to Calendar** (coming soon)

### Shopping List

**Features:**
- **Grouped by Category:**
  - Produce (vegetables, fruits)
  - Grains (rice, oats, quinoa)
  - Proteins (tofu, legumes, eggs, meat)
  - Dairy (milk, cheese, yogurt)
  - Spices & Condiments
  - Oils & Fats
  - Nuts & Seeds
  - Beverages

- **For Each Item:**
  - Total quantity needed (aggregated from all meals)
  - Unit (g, ml, pieces)
  - Estimated cost
  - Notes (e.g., "Used in 3 meals - Good source of omega-3")

- **Store Recommendations:**
  - Best stores in your area
  - Estimated total cost at each store
  - Availability rating

**Actions:**
- **📄 Export as PDF** - Printable checklist with checkboxes
- **📱 Email List** - Send to your email
- **🛒 Order Online** (integration coming soon)

**💡 Tip:** Generate your shopping list on Sunday for the week ahead!

---

## EEG Analysis

Analyze your brainwave data to understand mental states (stress, focus, relaxation, drowsiness).

### How to Use:

#### 1. Prepare EEG Data

**Supported Formats:**
- CSV file with columns: `timestamp, channel_1, channel_2, ..., channel_N`
- Sampling rate: 125-500 Hz (default: 250 Hz)
- Duration: At least 30 seconds
- Channels: 1-64 channels (default: 14)

**Example CSV:**
```csv
timestamp,channel_1,channel_2,channel_3,channel_4
0.000,0.1,0.2,0.3,0.4
0.004,0.2,0.3,0.4,0.5
0.008,0.3,0.4,0.5,0.6
```

**Devices Compatible:**
- Muse headband (export to CSV)
- OpenBCI
- Emotiv EPOC
- Any EEG device that exports CSV

#### 2. Upload & Analyze

1. Click **"Upload EEG Data"**
2. Select your CSV file
3. Click **"Analyze"**
4. Wait 10-30 seconds for processing

#### 3. View Results

**Mental State Probabilities:**
- **Stress:** 0-1 scale (0 = very relaxed, 1 = very stressed)
- **Focus:** 0-1 scale (0 = distracted, 1 = highly focused)
- **Relaxation:** 0-1 scale
- **Drowsiness:** 0-1 scale

**Brainwave Band Powers:**
- **Delta (0.5-4 Hz):** Deep sleep, unconscious
- **Theta (4-8 Hz):** Drowsiness, meditation
- **Alpha (8-13 Hz):** Relaxation, calm alertness
- **Beta (13-30 Hz):** Active thinking, focus (high beta = stress)
- **Gamma (30-50 Hz):** High-level cognitive processing

**Visualizations:**
- Line chart of band powers
- Pie chart of mental state distribution
- Time-series plot of dominant state over session

**Personalized Recommendations:**
- Based on detected states
- E.g., "High beta detected. Try box breathing to reduce stress."

#### 4. History

- View past EEG analyses
- Compare mental states over time
- Track improvement in stress management

**💡 Tip:** Analyze your EEG at the same time each day (e.g., 2 PM) to track patterns and effectiveness of interventions.

---

## AI Coach

Chat with your personalized wellness AI assistant.

### Features:

#### Context-Aware Conversations
The AI Coach knows:
- Your recent EEG analyses
- Sleep quality & patterns
- Meal plans & adherence
- Health metrics (steps, weight, vitals)
- Your goals & preferences
- Dosha type & personality profile

#### Example Conversations:

**You:** "I'm feeling stressed and have trouble sleeping."

**Coach:** "I've reviewed your recent data and noticed:
- Your EEG from yesterday showed 0.72 stress level
- Sleep quality has been 0.55 (below your 0.75 average)
- You've been going to bed past midnight (vs. your ideal 10:30 PM)

Here's my personalized plan:

1. **Breathing Exercise:** Box breathing for 5 minutes before bed
   - Inhale 4 counts → Hold 4 → Exhale 4 → Hold 4

2. **Supplements:**
   - Ashwagandha 300mg (reduces cortisol, improves sleep)
   - Magnesium 200mg (relaxes muscles, calms nervous system)

3. **Schedule Adjustment:**
   - Set a 10:00 PM bedtime alarm
   - Wind-down routine: dim lights, avoid screens

4. **Diet:**
   - Avoid caffeine after 2 PM
   - Add chamomile tea to your evening routine (I've updated your meal plan)

Would you like me to guide you through the breathing exercise now?"

---

**You:** "What should I eat for breakfast to boost energy?"

**Coach:** "Based on your Vata-Pitta dosha and 'Physical Strength' goal, I recommend:

**Energizing Breakfast:**
- Steel-cut oats (slow-release carbs)
- Banana & berries (quick energy, antioxidants)
- Almond butter (healthy fats, protein)
- Cinnamon (balances Vata)
- Warm milk or almond milk (grounding for Vata)

**Why it works:**
- Oats are warm & grounding (good for Vata)
- Natural sugars provide immediate energy
- Complex carbs sustain energy for 3-4 hours
- 15g protein supports muscle recovery

This meal is already in your plan for tomorrow at 7:30 AM!

Want me to suggest quick 15-minute alternatives?"

---

#### Guided Sessions

Request guided practices:
- **Breathing Exercises:** Box breathing, 4-7-8, alternate nostril
- **Meditation:** Mindfulness, loving-kindness, body scan
- **Yoga Flows:** Sun salutations, gentle stretching
- **Progressive Muscle Relaxation**

**Example:**
**You:** "Guide me through a 5-minute meditation."

**Coach:** (Provides step-by-step script with timing)

---

#### Ask Anything

- Supplement interactions
- Food questions ("Is turmeric good for inflammation?")
- Ayurvedic concepts ("What does 'balancing Pitta' mean?")
- Workout advice
- Stress management techniques

**💡 Tip:** The more you use the AI Coach, the better it understands your patterns and preferences.

---

## Health Metrics

Track your daily fitness and vitals.

### Log Metrics

**Fitness:**
- Steps
- Calories burned
- Distance (km)
- Active minutes
- Exercise type & duration

**Vitals:**
- Heart rate (avg, max, min)
- Blood pressure (systolic/diastolic)
- Weight
- Body fat percentage

**Sleep:**
- Hours slept
- Sleep quality score (0-1)

**Mental/Emotional:**
- Stress level (0-1)
- Focus level (0-1)
- Mood score (0-1)

**How to Log:**
1. Navigate to **Health Metrics** page
2. Click **"Log Today's Metrics"**
3. Fill in available data (not all fields required)
4. Click **"Save"**

### View Trends

**Visualizations:**
- **Line Charts:** See trends over 7, 30, or 90 days
- **Bar Charts:** Compare weekly averages
- **Heatmaps:** Identify patterns (e.g., low sleep on weekends)

**Insights:**
- "Your step count is 25% higher this week!"
- "Stress levels are decreasing - great job!"
- "Sleep quality correlates with 8+ hours of sleep"

**💡 Tip:** Sync with wearables (Fitbit, Apple Watch) for automatic tracking (see Settings).

---

## Nutrition

Log your meals and track nutrition.

### Log a Meal

1. Click **"Log Meal"**
2. Select:
   - Date
   - Meal type (breakfast, lunch, dinner, snack)
   - Food items (type or search)
3. Option 1: **Upload Photo**
   - Take a photo of your meal
   - AI recognizes food items
   - Estimates nutrition
4. Option 2: **Manual Entry**
   - Enter food items and quantities
   - Nutrition calculated from database
5. Click **"Save"**

### View Nutrition Summary

**Daily Breakdown:**
- Total calories
- Macros (protein, carbs, fat)
- Micros (vitamins, minerals)
- Fiber, sugar, sodium

**Progress Bars:**
- % of daily goal for each nutrient
- Color-coded (green = on track, red = over/under)

**Weekly Analysis:**
- Average calories per day
- Macro ratio (e.g., 30% protein, 40% carbs, 30% fat)
- Adherence to meal plan (%)

**💡 Tip:** Log meals immediately after eating for accuracy!

---

## Supplements

Browse the supplement database and track your intake.

### Supplement Database

**Browse by Category:**
- Adaptogens (Ashwagandha, Rhodiola)
- Vitamins (D3, B12, C)
- Minerals (Magnesium, Zinc, Iron)
- Omega-3 Fatty Acids
- Nootropics (L-Theanine, Lion's Mane)
- Ayurvedic Herbs (Brahmi, Triphala, Turmeric)

**For Each Supplement:**
- Benefits & mechanisms of action
- Recommended dosage
- Timing (morning, evening, with meals)
- Contraindications & drug interactions
- Side effects
- Scientific evidence (PubMed links)
- Ayurvedic properties (rasa, virya, vipaka, dosha effects)

**Search:**
- By name ("ashwagandha")
- By benefit ("stress relief", "improve sleep")
- By dosha ("balance vata")

### Track Supplement Intake

1. Click **"Log Supplement"**
2. Select supplement from database
3. Enter dosage & time taken
4. Click **"Save"**

**Adherence Tracking:**
- % of days taken vs. recommended
- Streak counter
- Reminders (optional)

**💡 Tip:** Always consult a healthcare professional before starting new supplements, especially if you're on medications.

---

## Settings

### Profile Management

**Edit Profile:**
- Update personal information
- Change dietary preferences
- Adjust wellness goals
- Retake personality assessments

**Notification Preferences:**
- Email reminders for meals
- Push notifications for workouts
- Daily wellness tips

### Data & Privacy

**Export Your Data:**
- Download all your health data as CSV or JSON
- Includes metrics, meal logs, EEG analyses

**Delete Account:**
- Permanently remove your account and all data
- Cannot be undone

### Integrations

**Connect Wearables:**
- Fitbit
- Apple Health
- Garmin
- Whoop

**Connect Calendar:**
- Google Calendar
- Outlook
- Apple Calendar
- Sync your daily schedule

### Subscription (if applicable)

- View current plan (Free, Pro, Premium)
- Upgrade/downgrade
- Billing history
- Cancel subscription

---

## Tips & Best Practices

### 1. Morning Routine
✅ Check Dashboard for today's wellness score
✅ Review daily schedule
✅ Log any morning metrics (weight, sleep quality)

### 2. Consistency is Key
- Log health metrics daily (even if approximate)
- Follow meal plan at least 80% of the time
- Track adherence to see what works for you

### 3. Use EEG Analysis Strategically
- **Before important work:** Check focus levels
- **After meditation:** Validate relaxation state
- **End of stressful day:** Measure stress, try interventions, re-measure

### 4. Engage with AI Coach
- Ask follow-up questions for clarity
- Request guided sessions when stressed
- Report how recommendations worked (helps AI learn)

### 5. Adjust Plans as Needed
- If meal plan feels too restrictive, increase budget or simplify
- If schedule isn't working, retake chronotype assessment
- Update goals as you progress

### 6. Weekly Review
- Every Sunday, review the past week:
  - What went well?
  - What was challenging?
  - Adjust plans for the upcoming week

### 7. Share Progress (Optional)
- Share meal plan PDFs with family/roommates
- Export schedule to shared calendar
- Accountability partner feature (coming soon)

---

## Troubleshooting

### Login Issues

**Problem:** "Incorrect email or password"
- **Solution:** Use "Forgot Password" link (coming soon) or contact support
- **Workaround:** Try demo account: `demo@wellnessai.com` / `demo123`

**Problem:** Can't create account - "Email already registered"
- **Solution:** Email is already in use. Try logging in or use a different email.

---

### EEG Upload Fails

**Problem:** "Invalid file format"
- **Solution:** Ensure CSV format with `timestamp,channel_1,channel_2,...` headers
- Check that values are numeric (not text)

**Problem:** "Analysis failed"
- **Solution:** Ensure at least 30 seconds of data
- Check that sampling rate is between 125-500 Hz

---

### Meal Plan Not Generating

**Problem:** "Could not generate meal plan - budget too low"
- **Solution:** Increase weekly food budget in Settings > Profile > Dietary Preferences
- Minimum recommended: $50/week for basic plan

**Problem:** "No foods match your preferences"
- **Solution:** Reduce restrictions (e.g., remove some disliked foods)
- Expand cuisine preferences

---

### AI Coach Not Responding

**Problem:** Long wait times or timeout
- **Solution:** Backend may be processing. Wait 30 seconds and try again.
- Check internet connection

**Problem:** Generic responses
- **Solution:** Coach needs more data. Log at least:
  - 3 days of health metrics
  - Complete Life Optimization profile
  - 1 EEG analysis

---

### Data Not Saving

**Problem:** "Error saving data"
- **Solution:** Check internet connection
- Try logging out and back in
- Clear browser cache

---

### PDF Export Issues

**Problem:** PDF download fails
- **Solution:** Ensure meal plan exists for selected date
- Try different browser (Chrome, Firefox recommended)

---

### Wearable Sync Issues

**Problem:** Fitbit data not syncing
- **Solution:**
  1. Check authorization in Settings > Integrations
  2. Re-authorize if needed
  3. Ensure Fitbit app is updated

---

## Getting Help

**In-App Support:**
- Click the "?" icon in any section for contextual help

**Email Support:**
- support@wellnessai.com
- Response within 24 hours

**Community Forum:**
- https://community.wellnessai.com
- Ask questions, share tips, connect with other users

**Documentation:**
- Complete docs: https://docs.wellnessai.com

**Video Tutorials:**
- YouTube Channel: @WellnessAI
- Playlists for each feature

---

## Glossary

**Ayurveda:** Ancient Indian system of medicine focused on balance
**Chronotype:** Your natural sleep-wake preference (morning person vs. night person)
**Dosha:** Ayurvedic mind-body type (Vata, Pitta, Kapha)
**EEG:** Electroencephalogram - measures brain electrical activity
**Macros:** Macronutrients - protein, carbohydrates, fats
**Micros:** Micronutrients - vitamins, minerals
**RAG:** Retrieval-Augmented Generation (how AI Coach accesses your data)
**TDEE:** Total Daily Energy Expenditure - calories burned per day

---

**User Guide Version:** 1.0.0
**Last Updated:** November 16, 2025

**Happy Wellness Journey! 🧘‍♀️💚**
