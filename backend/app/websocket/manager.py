"""
WebSocket connection manager
Handles WebSocket connections and message broadcasting
"""

import json
import asyncio
from typing import Dict, List, Any
from fastapi import WebSocket
from loguru import logger

from app.core.config import settings


class WebSocketManager:
    """
    Manages WebSocket connections and message broadcasting
    """
    
    def __init__(self):
        # Active connections storage
        self.active_connections: Dict[str, WebSocket] = {}
        # Connection counter for unique IDs
        self.connection_counter = 0
    
    async def connect(self, websocket: WebSocket) -> str:
        """
        Accept a new WebSocket connection
        
        Args:
            websocket: The WebSocket connection
            
        Returns:
            str: Unique connection ID
        """
        await websocket.accept()
        
        # Generate unique connection ID
        self.connection_counter += 1
        connection_id = f"conn_{self.connection_counter}"
        
        # Store connection
        self.active_connections[connection_id] = websocket
        
        logger.info(f"WebSocket connected: {connection_id}")
        logger.info(f"Total active connections: {len(self.active_connections)}")
        
        # Send welcome message
        await self.send_personal_message(
            {
                "type": "connection_established",
                "connection_id": connection_id,
                "message": "Connected to AInBox WebSocket"
            },
            connection_id
        )
        
        return connection_id
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection
        
        Args:
            websocket: The WebSocket connection to remove
        """
        # Find and remove connection
        connection_id = None
        for conn_id, conn in self.active_connections.items():
            if conn == websocket:
                connection_id = conn_id
                break
        
        if connection_id:
            del self.active_connections[connection_id]
            logger.info(f"WebSocket disconnected: {connection_id}")
            logger.info(f"Total active connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], connection_id: str) -> None:
        """
        Send a message to a specific connection
        
        Args:
            message: Message data to send
            connection_id: Target connection ID
        """
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message))
                logger.debug(f"Message sent to {connection_id}: {message}")
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                # Remove broken connection
                if connection_id in self.active_connections:
                    del self.active_connections[connection_id]
    
    async def broadcast_message(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all active connections
        
        Args:
            message: Message data to broadcast
        """
        if not self.active_connections:
            logger.warning("No active connections to broadcast to")
            return
        
        # Create a list of tasks for concurrent sending
        tasks = []
        broken_connections = []
        
        for connection_id, websocket in self.active_connections.items():
            try:
                task = websocket.send_text(json.dumps(message))
                tasks.append(task)
            except Exception as e:
                logger.error(f"Error preparing broadcast to {connection_id}: {e}")
                broken_connections.append(websocket)
        
        # Remove broken connections
        for websocket in broken_connections:
            await self.disconnect(websocket)
        
        # Send messages concurrently
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
                logger.debug(f"Broadcasted message to {len(tasks)} connections")
            except Exception as e:
                logger.error(f"Error during broadcast: {e}")
    
    async def send_analysis_result(self, result: Dict[str, Any], connection_id: str = None) -> None:
        """
        Send email analysis result
        
        Args:
            result: Analysis result data
            connection_id: Target connection ID (if None, broadcasts to all)
        """
        import time
        message = {
            "type": "analysis_result",
            "data": result,
            "timestamp": time.time()
        }
        
        if connection_id:
            await self.send_personal_message(message, connection_id)
        else:
            await self.broadcast_message(message)
    
    async def send_analysis_complete(self, connection_id: str = None) -> None:
        """
        Send analysis completion notification
        
        Args:
            connection_id: Target connection ID (if None, broadcasts to all)
        """
        import time
        message = {
            "type": "analysis_complete",
            "message": "All emails have been processed",
            "timestamp": time.time()
        }
        
        if connection_id:
            await self.send_personal_message(message, connection_id)
        else:
            await self.broadcast_message(message)
    
    async def send_error(self, error: str, connection_id: str = None) -> None:
        """
        Send error message
        
        Args:
            error: Error message
            connection_id: Target connection ID (if None, broadcasts to all)
        """
        import time
        message = {
            "type": "error",
            "message": error,
            "timestamp": time.time()
        }
        
        if connection_id:
            await self.send_personal_message(message, connection_id)
        else:
            await self.broadcast_message(message)
    
    async def disconnect_by_id(self, connection_id: str):
        """
        Fecha e remove uma conexão WebSocket usando seu ID.
        """
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                logger.info(f"Server is closing connection: {connection_id}")
                await websocket.close(code=1000) # 1000 é o código para fechamento normal
            except Exception as e:
                logger.error(f"Error while closing connection {connection_id}: {e}")
            
            # Remove a conexão do dicionário para garantir a limpeza
            del self.active_connections[connection_id]
            logger.info(f"WebSocket disconnected by server: {connection_id}")
            logger.info(f"Total active connections: {len(self.active_connections)}")
    
    def get_connection_count(self) -> int:
        """
        Get the number of active connections
        
        Returns:
            int: Number of active connections
        """
        return len(self.active_connections)
    
    def get_connection_ids(self) -> List[str]:
        """
        Get list of active connection IDs
        
        Returns:
            List[str]: List of connection IDs
        """
        return list(self.active_connections.keys())


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
