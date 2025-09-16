# backend/app/api/endpoints/analysis.py

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
# Importe a nova dependência e o módulo dependencies
from app.dependencies import rate_limit_dependency
from app import dependencies

# Aplicamos a dependência a nível de router.
# Todas as rotas definidas neste router passarão por este check.
router = APIRouter(dependencies=[Depends(rate_limit_dependency)])


class EmailAnalysisRequest(BaseModel):
    emails: List[str] = []
    context: Optional[str] = None
    connection_id: Optional[str] = None


class EmailAnalysisResponse(BaseModel):
    message: str
    task_id: str
    total_emails: int


@router.post("/emails", response_model=EmailAnalysisResponse)
async def analyze_emails(
    request: EmailAnalysisRequest,
    background_tasks: BackgroundTasks,
    request_obj: Request
    # O parâmetro rate_limiter foi removido daqui
) -> EmailAnalysisResponse:
    """
    Start email analysis process
    """
    logger.info("📧 Email analysis endpoint called")
    logger.info(f"  - Rate limiter status: {'Enabled' if dependencies.RATE_LIMITER_AVAILABLE else 'Disabled'}")
    logger.info(f"  - Number of emails: {len(request.emails)}")
    logger.info(f"  - Connection ID: {request.connection_id}")
    
    # O corpo da função permanece o mesmo
    try:
        validation_result = security_validator.validate_file_upload_request(
            files=[], strings=request.emails
        )
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Validation failed: {', '.join(validation_result['errors'])}"
            )
        task_id = f"task_{asyncio.get_event_loop().time()}"
        background_tasks.add_task(
            process_emails_background,
            request.emails,
            request.context,
            request.connection_id,
            task_id,
        )
        return EmailAnalysisResponse(
            message="Email analysis started",
            task_id=task_id,
            total_emails=len(request.emails),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting analysis: {str(e)}")


@router.post("/files", response_model=EmailAnalysisResponse)
async def analyze_email_files(
    request_obj: Request,
    files: List[UploadFile] = File(...),
    context: Optional[str] = Form(None),
    connection_id: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
    # O parâmetro rate_limiter foi removido daqui
) -> EmailAnalysisResponse:
    """
    Start email analysis process from uploaded files
    """
    logger.info("📁 File analysis endpoint called")
    logger.info(f"  - Rate limiter status: {'Enabled' if dependencies.RATE_LIMITER_AVAILABLE else 'Disabled'}")
    logger.info(f"  - Number of files: {len(files)}")
    logger.info(f"  - Connection ID: {connection_id}")
    
    # O corpo da função permanece o mesmo
    try:
        validation_result = security_validator.validate_file_upload_request(
            files=files, strings=[]
        )
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Validation failed: {', '.join(validation_result['errors'])}"
            )
        task_id = f"task_{asyncio.get_event_loop().time()}"
        background_tasks.add_task(
            process_files_background,
            files,
            context,
            connection_id,
            task_id,
        )
        return EmailAnalysisResponse(
            message="Email file analysis started",
            task_id=task_id,
            total_emails=len(files),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting file analysis: {str(e)}")


# As funções de background permanecem inalteradas
async def process_files_background(files: List[UploadFile], context: Optional[str], connection_id: Optional[str], task_id: str) -> None:
    try:
        file_processor = FileProcessor()
        processed_files = await file_processor.process_uploaded_files(files)
        email_contents = [res['text_content'] for res in processed_files if res['success'] and res['text_content']]
        if not email_contents:
            error_msg = "No valid text content extracted from files"
            await (websocket_manager.send_error(error_msg, connection_id) if connection_id else websocket_manager.broadcast_message({"type": "error", "message": error_msg, "task_id": task_id}))
            return
        await process_emails_background(email_contents, context, connection_id, task_id)
    except Exception as e:
        error_msg = f"Error processing files: {str(e)}"
        await (websocket_manager.send_error(error_msg, connection_id) if connection_id else websocket_manager.broadcast_message({"type": "error", "message": error_msg, "task_id": task_id}))

async def process_emails_background(emails: List[str], context: Optional[str], connection_id: Optional[str], task_id: str) -> None:
    try:
        ai_service = AIService()
        email_processor = EmailProcessor(ai_service)
        for index, email_content in enumerate(emails):
            try:
                result = await email_processor.process_single_email(
                    email_content=email_content, context=context, email_index=index + 1, total_emails=len(emails)
                )
                await (websocket_manager.send_analysis_result(result, connection_id) if connection_id else websocket_manager.broadcast_message({"type": "analysis_result", "data": result, "task_id": task_id}))
                await asyncio.sleep(0.5)
            except Exception as e:
                error_result = {"email_index": index + 1, "total_emails": len(emails), "error": str(e), "classification": "Error", "suggestion": None}
                await (websocket_manager.send_analysis_result(error_result, connection_id) if connection_id else websocket_manager.broadcast_message({"type": "analysis_result", "data": error_result, "task_id": task_id}))
        await (websocket_manager.send_analysis_complete(connection_id) if connection_id else websocket_manager.broadcast_message({"type": "analysis_complete", "task_id": task_id, "message": "All emails processed successfully"}))
    except Exception as e:
        error_msg = f"Error processing emails: {str(e)}"
        await (websocket_manager.send_error(error_msg, connection_id) if connection_id else websocket_manager.broadcast_message({"type": "error", "message": error_msg, "task_id": task_id}))