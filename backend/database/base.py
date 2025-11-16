"""
SQLAlchemy Declarative Base

This file contains the shared Base class for all SQLAlchemy models.
Extracted to avoid circular imports between postgres.py and postgres_models.py
"""
from sqlalchemy.ext.declarative import declarative_base

# Create the declarative base
Base = declarative_base()
