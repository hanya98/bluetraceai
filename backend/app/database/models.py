"""
database/models.py
==================
SQLAlchemy PostGIS-ready ORM models for storing spill detections and attribution results.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class SpillRecordDB(Base):
    """Database model for recorded oil spill detections."""

    __tablename__ = "spill_records"

    id = Column(Integer, primary_key=True, index=True)
    spill_id = Column(String(64), unique=True, index=True, nullable=False)
    timestamp_utc = Column(DateTime(timezone=True), nullable=False)

    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)
    area_km2 = Column(Float, nullable=True)

    confidence = Column(Float, nullable=True)
    oil_probability = Column(Float, nullable=True)

    # PostGIS GeoJSON representation stored as JSON
    mask_polygon = Column(JSON, nullable=True)
    bounding_box = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    attributions = relationship("AttributionDB", back_populates="spill", cascade="all, delete-orphan")


class AttributionDB(Base):
    """Database model for candidate vessel attribution results."""

    __tablename__ = "vessel_attributions"

    id = Column(Integer, primary_key=True, index=True)
    spill_id = Column(String(64), ForeignKey("spill_records.spill_id"), nullable=False)
    vessel_id = Column(String(64), index=True, nullable=False)

    rank = Column(Integer, nullable=False)
    candidate_priority_score = Column(Float, nullable=False)
    explanation = Column(Text, nullable=False)
    mode_used = Column(String(32), default="heuristic")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    spill = relationship("SpillRecordDB", back_populates="attributions")
