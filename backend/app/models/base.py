"""Base models for database entities."""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId field for Pydantic models."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema: Any) -> None:
        field_schema.update(type="string")


class BaseDocument(BaseModel):
    """Base model for all database documents."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    schema_version: str = Field(default="1.0.0")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

    def dict(self, **kwargs):
        """Override dict to handle MongoDB ID field."""
        exclude_unset = kwargs.pop('exclude_unset', False)
        by_alias = kwargs.pop('by_alias', True)

        d = super().dict(
            exclude_unset=exclude_unset,
            by_alias=by_alias,
            **kwargs
        )

        # Convert ObjectId to string for JSON serialization
        if "_id" in d and d["_id"] is not None:
            d["_id"] = str(d["_id"])

        return d

    def model_dump_json(self, **kwargs):
        """Dump model to JSON with proper ObjectId handling."""
        return super().model_dump_json(by_alias=True, **kwargs)