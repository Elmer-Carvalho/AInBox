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
from app.dependencies import rate_limit_dependency
from app import dependencies

# A dependência continua aplicada a nível de router
router = APIRouter(dependencies=[Depends(rate_limit_dependency)])


# O modelo de resposta continua o mesmo
class EmailAnalysisResponse(BaseModel):
    message: str
    task_id: str
    total_emails: int


# Unificamos as rotas em um único endpoint
@router.post("", response_model=EmailAnalysisResponse)
async def analyze_emails_unified(
    request_obj: Request,
    background_tasks: BackgroundTasks,
    # E-mails como arquivos: opcional, pode ser uma lista vazia
    email_files: List[UploadFile] = File(None),
    # E-mails como strings: opcional, pode ser uma lista vazia
    email_strings: List[str] = Form(None),
    # Contexto como arquivo: opcional
    context_file: Optional[UploadFile] = File(None),
    # Contexto como string: opcional
    context_string: Optional[str] = Form(None),
    # Connection ID: obrigatório
    connection_id: str = Form(...)
) -> EmailAnalysisResponse:
    """
    Inicia o processo de análise para e-mails de múltiplas fontes (arquivos e strings).
    """
    logger.info("📧 Análise unificada de e-mails iniciada")

    # Garante que as listas não sejam None para facilitar o processamento
    email_files = email_files or []
    
    # --- CORREÇÃO APLICADA AQUI ---
    # Filtra strings vazias que podem ser enviadas pelo formulário quando o campo está vazio
    email_strings = [s for s in (email_strings or []) if s.strip()]
    # --- FIM DA CORREÇÃO ---

    # Validação: Pelo menos um e-mail deve ser enviado
    if not email_files and not email_strings:
        raise HTTPException(
            status_code=400,
            detail="Nenhum e-mail foi fornecido. Envie e-mails através de 'email_files' ou 'email_strings'."
        )

    # Validação de segurança
    all_files_to_validate = email_files + ([context_file] if context_file else [])
    validation_result = security_validator.validate_file_upload_request(
        files=all_files_to_validate, strings=email_strings
    )
    
    if not validation_result["valid"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Validation failed: {', '.join(validation_result['errors'])}"
        )
    
    task_id = f"task_{asyncio.get_event_loop().time()}"
    total_emails = len(email_files) + len(email_strings)
    
    logger.info(f"  - Total de e-mails a processar: {total_emails}")
    logger.info(f"  - Connection ID: {connection_id}")

    # Inicia a tarefa de background com todos os dados
    background_tasks.add_task(
        process_all_sources_background,
        email_files,
        email_strings,
        context_file,
        context_string,
        connection_id,
        task_id
    )

    return EmailAnalysisResponse(
        message="Análise de e-mails iniciada",
        task_id=task_id,
        total_emails=total_emails,
    )


async def process_all_sources_background(
    email_files: List[UploadFile],
    email_strings: List[str],
    context_file: Optional[UploadFile],
    context_string: Optional[str],
    connection_id: str,
    task_id: str
):
    """
    Tarefa de background para processar e-mails de todas as fontes.
    """
    all_email_contents = list(email_strings)
    final_context = context_string or ""
    
    file_processor = FileProcessor()

    # 1. Processa o arquivo de contexto primeiro
    if context_file:
        try:
            logger.info(f"Processando arquivo de contexto: {context_file.filename}")
            context_content_result = await file_processor.process_uploaded_files([context_file])
            if context_content_result and context_content_result[0]['success']:
                final_context += "\n\n--- Contexto Adicional ---\n" + context_content_result[0]['text_content']
        except Exception as e:
            logger.error(f"Falha ao processar arquivo de contexto: {e}")
            # Opcional: notificar o usuário sobre a falha no contexto via WebSocket

    # 2. Processa os arquivos de e-mail
    if email_files:
        processed_files = await file_processor.process_uploaded_files(email_files)
        for result in processed_files:
            if result['success'] and result['text_content']:
                all_email_contents.append(result['text_content'])

    # 3. Envia para a tarefa de análise final
    if not all_email_contents:
        error_msg = "Nenhum conteúdo de e-mail válido foi extraído."
        await websocket_manager.send_error(error_msg, connection_id)
        return

    await process_emails_background(
        all_email_contents, final_context, connection_id, task_id
    )


# A função process_emails_background original pode ser mantida como está
async def process_emails_background(emails: List[str], context: Optional[str], connection_id: Optional[str], task_id: str) -> None:
    # ... (código existente sem alterações)
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
        # --- CORREÇÃO APLICADA AQUI ---
        # Envia a mensagem de conclusão
        if connection_id:
            await websocket_manager.send_analysis_complete(connection_id)
            # Adiciona um pequeno delay para garantir que a mensagem seja enviada antes de fechar
            await asyncio.sleep(1)
            # Fecha ativamente a conexão
            await websocket_manager.disconnect_by_id(connection_id)
        else:
            # Se for um broadcast, não fechamos conexões individuais
            await websocket_manager.broadcast_message({
                "type": "analysis_complete",
                "task_id": task_id,
                "message": "All emails processed successfully"
            })
        # --- FIM DA CORREÇÃO ---
    except Exception as e:
        error_msg = f"Error processing emails: {str(e)}"
        await (websocket_manager.send_error(error_msg, connection_id) if connection_id else websocket_manager.broadcast_message({"type": "error", "message": error_msg, "task_id": task_id}))