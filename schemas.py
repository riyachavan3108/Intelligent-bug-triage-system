# schemas.py
from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# ===== ENUMS =====

class SeverityLevel(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class BugStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"

class AssignmentAction(str, Enum):
    APPROVE = "approved"
    REJECT = "rejected"
    MODIFY = "modified"

class AssignmentStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

# ===== BASE SCHEMAS =====

class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        use_enum_values = True

# ===== BUG REPORT SCHEMAS =====

class BugReportBase(BaseSchema):
    title: str
    description: str
    severity: SeverityLevel = SeverityLevel.MEDIUM
    component: Optional[str] = None
    labels: Optional[str] = None
    stack_trace: Optional[str] = None

class BugReportCreate(BugReportBase):
    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    @validator('description')
    def description_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()

class BugReportResponse(BaseModel):
    id: int
    title: str
    description: str
    severity: str
    component: Optional[str] = None
    labels: Optional[str] = None
    stack_trace: Optional[str] = None
    predicted_developer: Optional[str] = None
    confidence_score: Optional[float] = 0.0
    assigned_developer: Optional[str] = None
    assignment_reason: Optional[str] = None  # NEW FIELD: Assignment reasoning
    status: str
    github_issue_url: Optional[str] = None
    jira_ticket_key: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BugReportUpdate(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[SeverityLevel] = None
    component: Optional[str] = None
    labels: Optional[str] = None
    stack_trace: Optional[str] = None
    assigned_developer: Optional[str] = None
    status: Optional[BugStatus] = None

# ===== DEVELOPER SCHEMAS =====

class DeveloperBase(BaseSchema):
    name: str
    email: str
    skills: Optional[str] = None
    specialty: Optional[str] = None
    github_username: Optional[str] = None
    jira_username: Optional[str] = None

class DeveloperCreate(DeveloperBase):
    max_concurrent_assignments: int = 5
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

class DeveloperResponse(BaseModel):
    id: int
    name: str
    email: str
    skills: Optional[str] = None
    specialty: Optional[str] = None
    github_username: Optional[str] = None
    jira_username: Optional[str] = None
    total_assigned: int = 0
    avg_resolution_time: float = 0.0
    satisfaction_rating: float = 5.0
    is_active: bool = True
    max_concurrent_assignments: int = 5
    current_workload: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DeveloperUpdate(BaseSchema):
    name: Optional[str] = None
    email: Optional[str] = None
    skills: Optional[str] = None
    specialty: Optional[str] = None
    github_username: Optional[str] = None
    jira_username: Optional[str] = None
    is_active: Optional[bool] = None

# ===== ASSIGNMENT SCHEMAS =====

class AssignmentRequest(BaseSchema):
    bug_id: int
    action: AssignmentAction
    assigned_developer: Optional[str] = None

class AssignmentResponse(BaseModel):
    id: int
    bug_report_id: int
    assigned_developer: str
    action: str
    confidence_score: float
    assigned_at: datetime
    
    class Config:
        from_attributes = True

# ===== ANALYTICS SCHEMAS =====

class AnalyticsResponse(BaseModel):
    total_reports: int
    approved_reports: int
    pending_reports: int
    developer_distribution: Dict[str, int]
    severity_distribution: Dict[str, int]
    component_distribution: Dict[str, int]
    average_confidence: float
    
    class Config:
        from_attributes = True