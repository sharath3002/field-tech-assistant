"""
Pydantic models for Field Tech Visual Assistant environment.
OpenEnv-compliant type definitions.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class FieldTechAction(BaseModel):
    """
    Action model for Field Tech environment.
    
    Represents the technician's response/decision.
    """
    response: str = Field(
        ...,
        description="Technician's answer (cable ID, port number, or diagnostic results)"
    )


class FieldTechObservation(BaseModel):
    """
    Observation model for Field Tech environment.
    
    Contains the scenario, visual context, and question for the technician.
    """
    scenario: str = Field(
        ...,
        description="Brief description of the technical scenario"
    )
    visual_context: str = Field(
        ...,
        description="Detailed description of what the technician sees"
    )
    question: str = Field(
        ...,
        description="The question or task to complete"
    )
    step: int = Field(
        default=0,
        description="Current step number in the episode"
    )


class FieldTechReward(BaseModel):
    """
    Reward model for Field Tech environment.
    
    Provides feedback on action correctness.
    """
    score: float = Field(
        ...,
        gt=0.0,
        lt=1.0,
        description="Normalized score between 0.0 (wrong) and 1.0 (perfect)"
    )
    feedback: str = Field(
        default="",
        description="Explanation of the result"
    )
    correct: bool = Field(
        default=False,
        description="Whether the answer was correct"
    )
