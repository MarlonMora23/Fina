"""
Gestor de historial de conversación para que los agentes recuerden el contexto
"""

from datetime import datetime
from typing import List, Dict, Optional


class ConversationHistory:
    """Mantiene el historial de conversación en memoria (sin persistencia)."""
    
    def __init__(self, user_id: str = "default", max_messages: int = 20):
        self.user_id = user_id
        self.messages: List[Dict] = []
        self.max_messages = max_messages
    
    def add_user_message(self, mensaje: str, metadata: Dict = None) -> None:
        """Agrega mensaje del usuario al historial."""
        self.messages.append({
            "role": "user",
            "content": mensaje,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
        self._truncate()
    
    def add_agent_response(self, agent_name: str, response: str, metadata: Dict = None) -> None:
        """Agrega respuesta del agente al historial."""
        self.messages.append({
            "role": "assistant",
            "agent": agent_name,
            "content": response,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
        self._truncate()
    
    def get_context(self, last_n: Optional[int] = None) -> str:
        """
        Retorna los últimos N mensajes formateados como contexto para el LLM.
        
        Args:
            last_n: Últimos N mensajes a incluir (default: 10)
        
        Returns:
            String con el historial formateado
        """
        if not last_n:
            last_n = min(10, len(self.messages))
        
        if not self.messages:
            return "Sin historial previo."
        
        context_messages = self.messages[-last_n:]
        formatted = []
        
        for msg in context_messages:
            timestamp = msg.get("timestamp", "").split("T")[1][:5]  # HH:MM
            
            if msg["role"] == "user":
                formatted.append(f"[{timestamp}] Usuario: {msg['content']}")
            else:
                agent = msg.get("agent", "Agente")
                formatted.append(f"[{timestamp}] {agent}: {msg['content']}")
        
        return "\n".join(formatted)
    
    def get_system_context(self) -> str:
        """
        Retorna contexto formateado para el system prompt del LLM.
        Útil para agentes que necesitan entender conversaciones previas.
        """
        if not self.messages:
            return ""
        
        context = "HISTORIAL DE CONVERSACIÓN RECIENTE:\n"
        context += "=" * 50 + "\n"
        context += self.get_context(last_n=15)
        context += "\n" + "=" * 50 + "\n"
        
        return context
    
    def get_last_user_intent(self) -> Optional[str]:
        """Retorna el último mensaje del usuario."""
        for msg in reversed(self.messages):
            if msg["role"] == "user":
                return msg["content"]
        return None
    
    def get_agent_context(self, agent_name: str, last_n: int = 5) -> str:
        """
        Retorna contexto filtrado solo para un agente específico.
        Incluye mensajes del usuario y respuestas del agente.
        """
        relevant = [m for m in self.messages[-last_n:] 
                   if m["role"] == "user" or m.get("agent") == agent_name]
        
        if not relevant:
            return "Sin contexto previo para este agente."
        
        formatted = []
        for msg in relevant:
            if msg["role"] == "user":
                formatted.append(f"Usuario: {msg['content']}")
            else:
                formatted.append(f"{agent_name}: {msg['content']}")
        
        return "\n".join(formatted)
    
    def clear(self) -> None:
        """Limpia el historial (para nuevas sesiones)."""
        self.messages = []
    
    def _truncate(self) -> None:
        """Mantiene el historial dentro del límite de mensajes."""
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_summary(self) -> Dict:
        """Retorna estadísticas del historial."""
        user_msgs = [m for m in self.messages if m["role"] == "user"]
        agent_msgs = [m for m in self.messages if m["role"] == "assistant"]
        
        agents_used = set(m.get("agent") for m in agent_msgs)
        
        return {
            "total_messages": len(self.messages),
            "user_messages": len(user_msgs),
            "agent_responses": len(agent_msgs),
            "agents_used": list(agents_used),
            "is_empty": len(self.messages) == 0
        }


# Instancia global (por usuario podría ampliarse a usar session ID)
_conversation_history = ConversationHistory()


def get_history() -> ConversationHistory:
    """Retorna la instancia global de historial."""
    return _conversation_history


def reset_history() -> None:
    """Resetea el historial (útil para testing)."""
    global _conversation_history
    _conversation_history = ConversationHistory()
