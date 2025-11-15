# 🚀 Wellness AI Platform - Quick Start Guide

This is your complete wellness AI platform with EEG analysis, LLM coach, voice emotion detection, and food recognition!

## 🎯 What You Get

✅ **EEG Brainwave Analysis** - Upload EEG data, get mental state classification
✅ **AI Wellness Coach** - Chat with LLM coach powered by RAG + knowledge base
✅ **Voice Emotion Analysis** - Detect stress and emotion from voice
✅ **Food Recognition** - Identify food items from photos
✅ **Supplement OCR** - Extract info from supplement labels
✅ **Health Tracking** - Track sleep, steps, calories, stress levels

## 🚀 Quick Start (5 minutes)

```bash
# 1. Start databases
docker-compose up -d postgres mongodb redis

# 2. Initialize database
python scripts/init_db.py

# 3. Start API server  
uvicorn backend.main:app --reload
```

Then open: **http://localhost:8000/docs**

## 📖 Full Documentation

See `COMPLETE_PROJECT_SUMMARY.md` for detailed feature breakdown and testing instructions.

**Project Status: 85% Complete - All core features working!**
