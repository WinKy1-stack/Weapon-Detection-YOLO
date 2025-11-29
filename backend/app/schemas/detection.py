"""
Detection schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class Detection(BaseModel):
    class_name: str
    confidence: float
    bbox: BoundingBox


class DetectionRequest(BaseModel):
    confidence_threshold: Optional[float] = Field(default=0.5, ge=0.0, le=1.0)
    model_type: Optional[str] = Field(default="yolo", pattern="^(yolo|fasterrcnn)$")


class DetectionResponse(BaseModel):
    detections: List[Detection]
    processing_time: float
    image_url: Optional[str] = None
    model_used: str


class AlertCreate(BaseModel):
    weapon_class: str
    confidence: float
    distance: Optional[float] = None
    status: str
    danger_level: str
    image_path: str


class PersonWeaponPair(BaseModel):
    """Person-weapon pairing information"""
    weapon: Detection
    person_bbox: Optional[BoundingBox] = None
    distance: Optional[float] = None
    status: str  # "held_by_person" or "no_owner"
    danger_level: str  # "high", "medium", "low"


class PairingDetectionResponse(BaseModel):
    """Response with person-weapon pairing"""
    pairs: List[PersonWeaponPair]
    processing_time: float
    image_url: Optional[str] = None
    model_used: str
    total_weapons: int
    weapons_with_persons: int


class AlertResponse(BaseModel):
    id: str = Field(alias="_id")
    timestamp: datetime
    weapon_class: str
    confidence: float
    distance: Optional[float]
    status: str
    danger_level: str
    image_path: str
    
    class Config:
        populate_by_name = True
