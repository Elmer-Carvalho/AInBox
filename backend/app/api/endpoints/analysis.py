"""
Email analysis endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form, Request, Depends
from pydantic import BaseModel
from typing import List, Optional
import asyncio

from app.core.config import settings
from app.services.email_processor import EmailProcessor
from app.services.ai_service import AIService
from app.services.file_processor import FileProcessor
from app.services.security_validator import security_validator
from app.websocket.manager import websocket_manager
from loguru import logger
from app.dependencies import get_rate_limiter
from app import dependencies


router = APIRouter()


class EmailAnalysisRequest(BaseModel):
    """Email analysis request model"""
    emails: List[str] = []  # List of email contents (strings)
    context: Optional[str] = None  # Optional context for AI
    connection_id: Optional[str] = None  # WebSocket connection ID


class EmailAnalysisResponse(BaseModel):
    """Email analysis response model"""
    message: str
    task_id: str
    total_emails: int


@router.post(
    "/emails", 
    response_model=EmailAnalysisResponse
)
async def analyze_emails(
    request: EmailAnalysisRequest,
    background_tasks: BackgroundTasks,
    request_obj: Request,
    rate_limiter: None = Depends(get_rate_limiter())
) -> EmailAnalysisResponse:
    """
    Start email analysis process
    
    Args:
        request: Email analysis request
        background_tasks: FastAPI background tasks
        
    Returns:
        EmailAnalysisResponse: Analysis initiation response
    """
    logger.info("📧 Email analysis endpoint called")
    logger.info(f"  - Rate limiter status: {'Enabled' if dependencies.RATE_LIMITER_AVAILABLE else 'Disabled'}")
    logger.info(f"  - Number of emails: {len(request.emails)}")
    logger.info(f"  - Connection ID: {request.connection_id}")
    
    try:
        # Validate request using security validator
        validation_result = security_validator.validate_file_upload_request(
            files=[],  # No files for this endpoint
            strings=request.emails
        )
        
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Validation failed: {', '.join(validation_result['errors'])}"
            )
        
        # Generate task ID
        task_id = f"task_{asyncio.get_event_loop().time()}"
        
        # Start background processing
        background_tasks.add_task(
            process_emails_background,
            request.emails,
            request.context,
            request.connection_id,
            task_id
        )
        
        return EmailAnalysisResponse(
            message="Email analysis started",
            task_id=task_id,
            total_emails=len(request.emails)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting analysis: {str(e)}")


@router.post(
    "/files", 
    response_model=EmailAnalysisResponse
)
async def analyze_email_files(
    request_obj: Request,
    files: List[UploadFile] = File(...),
    context: Optional[str] = Form(None),
    connection_id: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    rate_limiter: None = Depends(get_rate_limiter())
) -> EmailAnalysisResponse:
    """
    Start email analysis process from uploaded files
    
    Args:
        files: List of uploaded files (.pdf, .txt)
        context: Optional context for AI
        connection_id: WebSocket connection ID
        background_tasks: FastAPI background tasks
        
    Returns:
        EmailAnalysisResponse: Analysis initiation response
    """
    logger.info("📁 File analysis endpoint called")
    logger.info(f"  - Rate limiter status: {'Enabled' if dependencies.RATE_LIMITER_AVAILABLE else 'Disabled'}")
    logger.info(f"  - Number of files: {len(files)}")
    logger.info(f"  - Connection ID: {connection_id}")
    
    try:
        # Validate request using security validator
        validation_result = security_validator.validate_file_upload_request(
            files=files,
            strings=[]  # No strings for this endpoint
        )
        
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Validation failed: {', '.join(validation_result['errors'])}"
            )
        
        # Generate task ID
        task_id = f"task_{asyncio.get_event_loop().time()}"
        
        # Start background processing (including file processing)
        background_tasks.add_task(
            process_files_background,
            files,
            context,
            connection_id,
            task_id
        )
        
        return EmailAnalysisResponse(
            message="Email file analysis started",
            task_id=task_id,
            total_emails=len(files)  # Estimate based on file count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting file analysis: {str(e)}")


async def process_files_background(
    files: List[UploadFile],
    context: Optional[str],
    connection_id: Optional[str],
    task_id: str
) -> None:
    """
    Background task to process uploaded files and then analyze emails
    
    Args:
        files: List of uploaded files
        context: Optional context for AI
        connection_id: WebSocket connection ID
        task_id: Task identifier
    """
    try:
        # Initialize file processor
        file_processor = FileProcessor()
        
        # Process uploaded files
        processed_files = await file_processor.process_uploaded_files(files)
        
        # Extract text content from successfully processed files
        email_contents = []
        for file_result in processed_files:
            if file_result['success'] and file_result['text_content']:
                email_contents.append(file_result['text_content'])
        
        if not email_contents:
            error_msg = "No valid text content extracted from files"
            if connection_id:
                await websocket_manager.send_error(error_msg, connection_id)
            else:
                await websocket_manager.broadcast_message({
                    "type": "error",
                    "message": error_msg,
                    "task_id": task_id
                })
            return
        
        # Now process the extracted email contents
        await process_emails_background(
            email_contents,
            context,
            connection_id,
            task_id
        )
        
    except Exception as e:
        error_msg = f"Error processing files: {str(e)}"
        if connection_id:
            await websocket_manager.send_error(error_msg, connection_id)
        else:
            await websocket_manager.broadcast_message({
                "type": "error",
                "message": error_msg,
                "task_id": task_id
            })


async def process_emails_background(
    emails: List[str],
    context: Optional[str],
    connection_id: Optional[str],
    task_id: str
) -> None:
    """
    Background task to process emails
    
    Args:
        emails: List of email contents
        context: Optional context for AI
        connection_id: WebSocket connection ID
        task_id: Task identifier
    """
    try:
        # Initialize services
        ai_service = AIService()
        email_processor = EmailProcessor(ai_service)
        
        # Process each email
        for index, email_content in enumerate(emails):
            try:
                # Process single email
                result = await email_processor.process_single_email(
                    email_content=email_content,
                    context=context,
                    email_index=index + 1,
                    total_emails=len(emails)
                )
                
                # Send result via WebSocket
                if connection_id:
                    await websocket_manager.send_analysis_result(result, connection_id)
                else:
                    await websocket_manager.broadcast_message({
                        "type": "analysis_result",
                        "data": result,
                        "task_id": task_id
                    })
                
                # Small delay to prevent overwhelming the AI service
                await asyncio.sleep(0.5)
                
            except Exception as e:
                error_result = {
                    "email_index": index + 1,
                    "total_emails": len(emails),
                    "error": str(e),
                    "classification": "Error",
                    "suggestion": None
                }
                
                if connection_id:
                    await websocket_manager.send_analysis_result(error_result, connection_id)
                else:
                    await websocket_manager.broadcast_message({
                        "type": "analysis_result",
                        "data": error_result,
                        "task_id": task_id
                    })
        
        # Send completion message
        if connection_id:
            await websocket_manager.send_analysis_complete(connection_id)
        else:
            await websocket_manager.broadcast_message({
                "type": "analysis_complete",
                "task_id": task_id,
                "message": "All emails processed successfully"
            })
            
    except Exception as e:
        # Send error message
        error_msg = f"Error processing emails: {str(e)}"
        if connection_id:
            await websocket_manager.send_error(error_msg, connection_id)
        else:
            await websocket_manager.broadcast_message({
                "type": "error",
                "message": error_msg,
                "task_id": task_id
            })
