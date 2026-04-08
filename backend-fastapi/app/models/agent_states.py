from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Float, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base, TimestampMixin, UUIDMixin


class AgentState(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_states"

    session_id = Column(String(255), nullable=False)
    agent_type = Column(String(100), nullable=False)
    state_data = Column(JSON, nullable=False, default={})
    checkpoint_data = Column(JSON, nullable=True)
    context = Column(JSON, default={})
    variables = Column(JSON, default={})
    current_node = Column(String(255), nullable=True)
    iteration_count = Column(Integer, default=0)
    max_iterations = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    error_state = Column(JSON, nullable=True)

    memories = relationship("AgentMemory", back_populates="agent_state", cascade="all, delete-orphan")
    messages = relationship("AgentMessage", back_populates="agent_state", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_agent_states_session_id', 'session_id'),
        Index('idx_agent_states_agent_type', 'agent_type'),
        Index('idx_agent_states_active', 'session_id', 'is_active'),
    )

    def update_state(self, new_state: dict):
        self.state_data.update(new_state)
        self.updated_at = datetime.utcnow()

    def create_checkpoint(self):
        self.checkpoint_data = {
            "state": self.state_data,
            "context": self.context,
            "variables": self.variables,
            "current_node": self.current_node,
            "timestamp": datetime.utcnow().isoformat()
        }

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "agent_type": self.agent_type,
            "state": self.state_data,
            "context": self.context,
            "variables": self.variables,
            "current_node": self.current_node,
            "iteration_count": self.iteration_count,
            "is_active": self.is_active,
            "is_completed": self.is_completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AgentMemory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_memories"

    agent_state_id = Column(String(36), ForeignKey("agent_states.id", ondelete="CASCADE"), nullable=False)
    memory_type = Column(String(50), nullable=False)
    memory_key = Column(String(255), nullable=False)
    memory_value = Column(JSON, nullable=False)
    importance_score = Column(Float, default=0.0)
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    agent_state = relationship("AgentState", back_populates="memories")

    __table_args__ = (
        Index('idx_agent_memories_state_id', 'agent_state_id'),
        Index('idx_agent_memories_type_key', 'agent_state_id', 'memory_type', 'memory_key'),
    )

    def access(self):
        self.access_count += 1
        self.last_accessed_at = datetime.utcnow()


class AgentMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "