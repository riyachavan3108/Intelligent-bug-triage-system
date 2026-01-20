from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uvicorn
from typing import List, Optional
import os
from datetime import datetime
import logging

# Local imports
from database import get_db, init_db, BugReport, Developer, Assignment
from schemas import (
    BugReportResponse, 
    DeveloperResponse, 
    AssignmentRequest, 
    AssignmentResponse,
    AnalyticsResponse
)
from services.pdf_parser import PDFParser
from services.external_integrations import GitHubIntegration, JiraIntegration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Intelligent Bug Triage System",
    description="Automatically assign bug reports to developers using AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
pdf_parser = PDFParser()
github_integration = GitHubIntegration()
jira_integration = JiraIntegration()

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    logger.info("Application startup complete")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Intelligent Bug Triage System API", "status": "running"}

@app.post("/upload-pdf/", response_model=List[BugReportResponse])
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process a PDF file containing bug reports
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Save uploaded file temporarily
        temp_file_path = f"temp_{datetime.now().timestamp()}_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Parse PDF and extract bug reports (PDF parser now handles ML assignment)
        logger.info(f"Processing PDF: {file.filename}")
        bug_reports_data = pdf_parser.extract_bug_reports(temp_file_path)
        
        # Clean up temp file
        os.remove(temp_file_path)
        
        # Process each bug report (already assigned by ML system)
        processed_reports = []
        for bug_data in bug_reports_data:
            # Save to database
            bug_report = BugReport(
                title=bug_data.get("title", ""),
                description=bug_data.get("description", ""),
                severity=bug_data.get("severity", "Medium"),
                component=bug_data.get("component", "General"),
                labels=bug_data.get("labels", ""),
                stack_trace=bug_data.get("stack_trace", ""),
                predicted_developer=bug_data.get("predicted_developer", "Unassigned"),
                confidence_score=bug_data.get("confidence", 0.5),
                assignment_reason=bug_data.get("reason", "AI-based assignment"),
                status="pending"
            )
            
            db.add(bug_report)
            db.commit()
            db.refresh(bug_report)
            
            processed_reports.append(BugReportResponse.from_orm(bug_report))
        
        logger.info(f"Successfully processed {len(processed_reports)} bug reports")
        return processed_reports
        
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.get("/bug-reports/", response_model=List[BugReportResponse])
async def get_bug_reports(
    status: Optional[str] = None,
    developer: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get bug reports with optional filtering
    """
    query = db.query(BugReport)
    
    if status:
        query = query.filter(BugReport.status == status)
    if developer:
        query = query.filter(BugReport.predicted_developer == developer)
    if severity:
        query = query.filter(BugReport.severity == severity)
    
    bug_reports = query.all()
    return [BugReportResponse.from_orm(report) for report in bug_reports]

@app.get("/bug-reports/{report_id}", response_model=BugReportResponse)
async def get_bug_report(report_id: int, db: Session = Depends(get_db)):
    """
    Get a specific bug report by ID
    """
    bug_report = db.query(BugReport).filter(BugReport.id == report_id).first()
    if not bug_report:
        raise HTTPException(status_code=404, detail="Bug report not found")
    
    return BugReportResponse.from_orm(bug_report)

@app.post("/assign-bug/", response_model=AssignmentResponse)
async def assign_bug(
    assignment: AssignmentRequest,
    db: Session = Depends(get_db)
):
    """
    Approve, reject, or modify bug assignment
    """
    bug_report = db.query(BugReport).filter(BugReport.id == assignment.bug_id).first()
    if not bug_report:
        raise HTTPException(status_code=404, detail="Bug report not found")
    
    # Update bug report status
    bug_report.status = assignment.action
    if assignment.assigned_developer:
        bug_report.assigned_developer = assignment.assigned_developer
    else:
        bug_report.assigned_developer = bug_report.predicted_developer
    
    # Create assignment record
    assignment_record = Assignment(
        bug_report_id=bug_report.id,
        assigned_developer=bug_report.assigned_developer,
        action=assignment.action,
        confidence_score=bug_report.confidence_score,
        assigned_at=datetime.utcnow()
    )
    
    db.add(assignment_record)
    db.commit()
    db.refresh(assignment_record)
    
    # If approved, create external tickets
    if assignment.action == "approved":
        try:
            # Create GitHub issue if configured
            if os.getenv("GITHUB_TOKEN"):
                github_issue = await github_integration.create_issue(bug_report)
                logger.info(f"Created GitHub issue: {github_issue.get('html_url')}")
            
            # Create JIRA ticket if configured
            if os.getenv("JIRA_TOKEN"):
                jira_ticket = await jira_integration.create_ticket(bug_report)
                logger.info(f"Created JIRA ticket: {jira_ticket.get('key')}")
                
        except Exception as e:
            logger.error(f"Error creating external tickets: {str(e)}")
    
    return AssignmentResponse.from_orm(assignment_record)

@app.post("/bulk-assign/")
async def bulk_assign_bugs(
    assignments: List[AssignmentRequest],
    db: Session = Depends(get_db)
):
    """
    Process multiple bug assignments in bulk
    """
    results = []
    for assignment in assignments:
        try:
            result = await assign_bug(assignment, db)
            results.append(result)
        except Exception as e:
            logger.error(f"Error in bulk assignment for bug {assignment.bug_id}: {str(e)}")
            results.append({"bug_id": assignment.bug_id, "error": str(e)})
    
    return {"processed": len(results), "results": results}

@app.get("/developers/", response_model=List[DeveloperResponse])
async def get_developers(db: Session = Depends(get_db)):
    """
    Get list of all developers
    """
    developers = db.query(Developer).filter(Developer.is_active == True).all()
    return [DeveloperResponse.from_orm(dev) for dev in developers]

@app.post("/developers/", response_model=DeveloperResponse)
async def create_developer(developer_data: dict, db: Session = Depends(get_db)):
    """
    Add a new developer to the system
    """
    developer = Developer(
        name=developer_data["name"],
        email=developer_data["email"],
        skills=developer_data.get("skills", ""),
        github_username=developer_data.get("github_username"),
        jira_username=developer_data.get("jira_username")
    )
    
    db.add(developer)
    db.commit()
    db.refresh(developer)
    
    return DeveloperResponse.from_orm(developer)

@app.get("/analytics/", response_model=AnalyticsResponse)
async def get_analytics(db: Session = Depends(get_db)):
    """
    Get system analytics and metrics
    """
    # Basic counts
    total_reports = db.query(BugReport).count()
    approved_reports = db.query(BugReport).filter(BugReport.status == "approved").count()
    pending_reports = db.query(BugReport).filter(BugReport.status == "pending").count()
    
    # Developer assignment distribution
    developer_stats = db.query(
        Assignment.assigned_developer,
        db.func.count(Assignment.id).label('count')
    ).group_by(Assignment.assigned_developer).all()
    
    # Severity distribution
    severity_stats = db.query(
        BugReport.severity,
        db.func.count(BugReport.id).label('count')
    ).group_by(BugReport.severity).all()
    
    # Component distribution
    component_stats = db.query(
        BugReport.component,
        db.func.count(BugReport.id).label('count')
    ).group_by(BugReport.component).all()
    
    # Average confidence score
    avg_confidence = db.query(db.func.avg(BugReport.confidence_score)).scalar() or 0
    
    return AnalyticsResponse(
        total_reports=total_reports,
        approved_reports=approved_reports,
        pending_reports=pending_reports,
        developer_distribution={dev: count for dev, count in developer_stats},
        severity_distribution={sev: count for sev, count in severity_stats},
        component_distribution={comp: count for comp, count in component_stats},
        average_confidence=float(avg_confidence)
    )

@app.delete("/bug-reports/{report_id}")
async def delete_bug_report(report_id: int, db: Session = Depends(get_db)):
    """
    Delete a bug report
    """
    bug_report = db.query(BugReport).filter(BugReport.id == report_id).first()
    if not bug_report:
        raise HTTPException(status_code=404, detail="Bug report not found")
    
    db.delete(bug_report)
    db.commit()
    
    return {"message": "Bug report deleted successfully"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )