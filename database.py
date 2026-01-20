# database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bug_triage.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables and default data"""
    Base.metadata.create_all(bind=engine)
    
    # Create default developers if they don't exist
    db = SessionLocal()
    try:
        if db.query(Developer).count() == 0:
            default_developers = [
                Developer(
                    name="Alice Johnson",
                    email="alice@company.com",
                    skills="Frontend,React,JavaScript,UI/UX",
                    github_username="alice_dev",
                    specialty="Frontend Development"
                ),
                Developer(
                    name="Bob Smith",
                    email="bob@company.com",
                    skills="Backend,Python,FastAPI,Database",
                    github_username="bob_backend",
                    specialty="Backend Development"
                ),
                Developer(
                    name="Carol Davis",
                    email="carol@company.com",
                    skills="Mobile,React Native,iOS,Android",
                    github_username="carol_mobile",
                    specialty="Mobile Development"
                ),
                Developer(
                    name="David Wilson",
                    email="david@company.com",
                    skills="DevOps,Docker,Kubernetes,AWS",
                    github_username="david_ops",
                    specialty="DevOps Engineering"
                ),
                Developer(
                    name="Emma Brown",
                    email="emma@company.com",
                    skills="Data Science,Machine Learning,Python,Analytics",
                    github_username="emma_data",
                    specialty="Data Science"
                ),
                Developer(
                    name="Frank Miller",
                    email="frank@company.com",
                    skills="Security,Penetration Testing,Compliance",
                    github_username="frank_sec",
                    specialty="Security Engineering"
                ),
                Developer(
                    name="Grace Lee",
                    email="grace@company.com",
                    skills="QA,Testing,Automation,Selenium",
                    github_username="grace_qa",
                    specialty="Quality Assurance"
                ),
                Developer(
                    name="Henry Taylor",
                    email="henry@company.com",
                    skills="Full Stack,Node.js,MongoDB,GraphQL",
                    github_username="henry_fullstack",
                    specialty="Full Stack Development"
                )
            ]
            
            for dev in default_developers:
                db.add(dev)
            
            db.commit()
            print("Default developers created successfully")
    
    finally:
        db.close()

# ===== DATABASE MODELS =====

class BugReport(Base):
    """Bug report model"""
    __tablename__ = "bug_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=False)
    severity = Column(String(20), default="Medium", index=True)  # Critical, High, Medium, Low
    component = Column(String(100), index=True)  # Frontend, Backend, Database, etc.
    labels = Column(String(500))  # Comma-separated tags
    stack_trace = Column(Text)
    
    # ML Prediction fields
    predicted_developer = Column(String(100), index=True)
    confidence_score = Column(Float, default=0.0)
    assignment_reason = Column(Text)  # NEW FIELD: Reasoning for assignment
    
    # Assignment fields
    assigned_developer = Column(String(100), index=True)
    status = Column(String(20), default="pending", index=True)  # pending, approved, rejected, modified
    
    # External integration fields
    github_issue_url = Column(String(500))
    jira_ticket_key = Column(String(50))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignments = relationship("Assignment", back_populates="bug_report", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BugReport(id={self.id}, title='{self.title[:50]}...', severity='{self.severity}')>"

class Developer(Base):
    """Developer model"""
    __tablename__ = "developers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    email = Column(String(150), unique=True, index=True)
    skills = Column(String(500))  # Comma-separated skills
    specialty = Column(String(100))  # Primary area of expertise
    
    # External integration usernames
    github_username = Column(String(100))
    jira_username = Column(String(100))
    
    # Performance metrics
    total_assigned = Column(Integer, default=0)
    avg_resolution_time = Column(Float, default=0.0)  # in hours
    satisfaction_rating = Column(Float, default=5.0)  # 1-10 scale
    
    # Status
    is_active = Column(Boolean, default=True)
    max_concurrent_assignments = Column(Integer, default=5)
    current_workload = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignments = relationship("Assignment", back_populates="developer")
    
    def __repr__(self):
        return f"<Developer(id={self.id}, name='{self.name}', specialty='{self.specialty}')>"

class Assignment(Base):
    """Assignment tracking model"""
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    bug_report_id = Column(Integer, ForeignKey("bug_reports.id"), nullable=False)
    developer_id = Column(Integer, ForeignKey("developers.id"))
    assigned_developer = Column(String(100), nullable=False, index=True)
    
    # Assignment details
    action = Column(String(20), nullable=False, index=True)  # approved, rejected, modified
    confidence_score = Column(Float, default=0.0)
    original_prediction = Column(String(100))  # Original ML prediction
    
    # Resolution tracking
    status = Column(String(20), default="open", index=True)  # open, in_progress, resolved, closed
    resolution_time = Column(Float)  # in hours
    resolution_notes = Column(Text)
    
    # Feedback
    user_feedback = Column(Text)
    rating = Column(Integer)  # 1-5 rating of assignment quality
    
    # Timestamps
    assigned_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    # Relationships
    bug_report = relationship("BugReport", back_populates="assignments")
    developer = relationship("Developer", back_populates="assignments")
    
    def __repr__(self):
        return f"<Assignment(id={self.id}, bug_id={self.bug_report_id}, developer='{self.assigned_developer}')>"

class MLModel(Base):
    """ML Model versioning and metadata"""
    __tablename__ = "ml_models"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), nullable=False, unique=True)
    model_type = Column(String(50), nullable=False)  # tfidf_knn, bert_mlp
    
    # Performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    
    # Training details
    training_samples = Column(Integer)
    features_count = Column(Integer)
    hyperparameters = Column(Text)  # JSON string of hyperparameters
    
    # Model file paths
    model_file_path = Column(String(500))
    vectorizer_file_path = Column(String(500))
    
    # Status
    is_active = Column(Boolean, default=False)
    
    # Metadata
    trained_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), default="system")
    
    def __repr__(self):
        return f"<MLModel(version='{self.version}', type='{self.model_type}', active={self.is_active})>"

class SystemConfig(Base):
    """System configuration settings"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text)
    data_type = Column(String(20), default="string")  # string, integer, float, boolean, json
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default="system")
    
    def __repr__(self):
        return f"<SystemConfig(key='{self.key}', value='{self.value[:50]}...')>"

class AuditLog(Base):
    """Audit log for tracking system changes"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(Integer, index=True)
    
    # Change details
    old_values = Column(Text)  # JSON string
    new_values = Column(Text)  # JSON string
    user_id = Column(String(100), index=True)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<AuditLog(action='{self.action}', entity='{self.entity_type}:{self.entity_id}')>"

# ===== ADDITIONAL HELPER MODELS =====

class ProjectComponent(Base):
    """Project components for better categorization"""
    __tablename__ = "project_components"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    primary_developer = Column(String(100), index=True)
    secondary_developers = Column(String(500))  # Comma-separated backup developers
    
    # Component metadata
    complexity_score = Column(Float, default=1.0)  # 1-10 scale
    business_criticality = Column(String(20), default="Medium")  # Low, Medium, High, Critical
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ProjectComponent(name='{self.name}', primary_dev='{self.primary_developer}')>"

class DeveloperSkill(Base):
    """Individual developer skills with proficiency levels"""
    __tablename__ = "developer_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    developer_id = Column(Integer, ForeignKey("developers.id"), nullable=False)
    skill_name = Column(String(100), nullable=False, index=True)
    proficiency_level = Column(Integer, default=1)  # 1-5 scale
    years_experience = Column(Float, default=0.0)
    last_used = Column(DateTime)
    
    # Validation through assignments
    successful_assignments = Column(Integer, default=0)
    total_assignments = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<DeveloperSkill(dev_id={self.developer_id}, skill='{self.skill_name}', level={self.proficiency_level})>"