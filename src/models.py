"""
Pydantic models for NGRS Solver API.

Defines request/response schemas for validation and documentation.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List, Any
from datetime import datetime


class SolveRequest(BaseModel):
    """Request payload for POST /solve endpoint."""
    
    input_json: Optional[Dict[str, Any]] = Field(
        None,
        description="Full NGRS input JSON (required if file not provided). "
                    "Should match schema v0.43+."
    )
    
    model_config = ConfigDict(extra='allow')  # Forgiving: accept extra fields


class Score(BaseModel):
    """Score breakdown."""
    hard: int = Field(0, description="Hard constraint violations count")
    soft: int = Field(0, description="Soft constraint penalties")
    overall: int = Field(0, description="Overall score (hard + soft)")


class SolverRunMetadata(BaseModel):
    """Metadata about the solve run."""
    runId: str = Field(..., description="Unique run ID")
    solverVersion: str = Field(default="optfold-py-0.4.2")
    startedAt: str = Field(..., description="ISO 8601 timestamp")
    ended: str = Field(..., description="ISO 8601 timestamp")
    durationSeconds: float = Field(..., description="Total solve time in seconds")
    status: str = Field(..., description="Final solver status: OPTIMAL, FEASIBLE, INFEASIBLE, etc.")
    timeLimitSec: Optional[int] = Field(None, description="Time limit applied")
    numVars: Optional[int] = Field(None, description="Number of decision variables")
    numConstraints: Optional[int] = Field(None, description="Number of constraints")


class Meta(BaseModel):
    """Response metadata."""
    requestId: str = Field(..., description="Unique request ID for tracing")
    generatedAt: str = Field(..., description="ISO 8601 timestamp of response generation")
    inputHash: Optional[str] = Field(None, description="SHA256 hash of input (excluding runtime data)")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    employeeHours: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Per-employee weekly normal hours and monthly OT aggregates"
    )
    hourBreakdown: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Hour breakdown per assignment (gross, lunch, normal, ot, paid)"
    )


class Assignment(BaseModel):
    """Single assignment in solution."""
    employeeId: str
    date: str
    demandId: str
    shiftCode: str
    startDateTime: str
    endDateTime: str
    hours: Optional[Dict[str, float]] = Field(
        None,
        description="Hour breakdown: gross, lunch, normal, ot, paid"
    )
    
    model_config = ConfigDict(extra='allow')


class Violation(BaseModel):
    """Constraint violation."""
    constraintId: str
    employeeId: Optional[str] = None
    message: str
    
    model_config = ConfigDict(extra='allow')


class SolveResponse(BaseModel):
    """Response payload from POST /solve endpoint."""
    
    schemaVersion: Optional[str] = Field(
        "0.43",
        description="Schema version of the response"
    )
    
    planningReference: Optional[str] = Field(
        None,
        description="Reference for the planning period"
    )
    
    solverRun: Optional[SolverRunMetadata] = Field(
        None,
        description="Metadata about the solver execution"
    )
    
    score: Score = Field(..., description="Score breakdown")
    
    scoreBreakdown: Optional[Dict[str, Any]] = Field(
        None,
        description="Detailed score breakdown by constraint"
    )
    
    assignments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of assignments (employee-shift pairs)"
    )
    
    violations: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Constraint violations found (if any)"
    )
    
    unmetDemand: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Demands that could not be fully met"
    )
    
    meta: Meta = Field(..., description="Response metadata")
    
    error: Optional[str] = Field(
        None,
        description="Error message (if status='ERROR')"
    )
    
    model_config = ConfigDict(extra='allow')


class HealthResponse(BaseModel):
    """Response from GET /health endpoint."""
    status: str = Field("ok")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class SchemaResponse(BaseModel):
    """Response from GET /schema endpoint."""
    inputSchema: Dict[str, Any] = Field(..., description="JSON Schema for input")
    outputSchema: Dict[str, Any] = Field(..., description="JSON Schema for output")


class VersionResponse(BaseModel):
    """Response from GET /version endpoint."""
    apiVersion: str = Field("0.1.0")
    solverVersion: str = Field("optfold-py-0.4.2")
    schemaVersion: str = Field("0.43")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
