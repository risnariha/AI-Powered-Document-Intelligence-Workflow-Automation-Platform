from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Float, Enum, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.base import Base, TimestampMixin, UUIDMixin


class WorkflowStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class WorkflowTrigger(enum.Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT = "event"
    WEBHOOK = "webhook"


class Workflow(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflows"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(50), default="1.0.0")
    definition = Column(JSON, nullable=False)
    nodes = Column(JSON, default=[])
    edges = Column(JSON, default=[])
    trigger_type = Column(Enum(WorkflowTrigger), default=WorkflowTrigger.MANUAL)
    trigger_config = Column(JSON, default={})
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)
    timeout_seconds = Column(Integer, default=3600)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING)
    is_enabled = Column(Boolean, default=True)
    owner_id = Column(String(255), nullable=True)
    organization_id = Column(String(255), nullable=True)
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    avg_execution_time_ms = Column(Float, nullable=True)

    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "definition": self.definition,
            "nodes": self.nodes,
            "edges": self.edges,
            "trigger_type": self.trigger_type.value if self.trigger_type else None,
            "trigger_config": self.trigger_config,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "is_enabled": self.is_enabled,
            "status": self.status.value if self.status else None,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class WorkflowExecution(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflow_executions"

    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    execution_id = Column(String(255), nullable=False, unique=True)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING)
    input_data = Column(JSON, default={})
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    triggered_by = Column(String(255), nullable=True)
    context = Column(JSON, default={})
    checkpoint_data = Column(JSON, nullable=True)
    checkpoint_at = Column(DateTime, nullable=True)

    workflow = relationship("Workflow", back_populates="executions")
    steps = relationship("WorkflowStep", back_populates="execution", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_workflow_executions_workflow_id', 'workflow_id'),
        Index('idx_workflow_executions_status', 'status'),
        Index('idx_workflow_executions_started_at', 'started_at'),
    )

    def start_execution(self):
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.utcnow()

    def complete_execution(self, success: bool, output_data: dict = None, error: str = None):
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        if success:
            self.status = WorkflowStatus.COMPLETED
            if output_data:
                self.output_data = output_data
        else:
            self.status = WorkflowStatus.FAILED
            self.error_message = error
        self.workflow.total_executions += 1
        if success:
            self.workflow.successful_executions += 1
        else:
            self.workflow.failed_executions += 1


class WorkflowStep(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflow_steps"

    execution_id = Column(String(36), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False)
    step_name = Column(String(255), nullable=False)
    step_type = Column(String(100), nullable=False)
    step_order = Column(Integer, nullable=False)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.PENDING)
    input_data = Column(JSON, default={})
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    execution = relationship("WorkflowExecution", back_populates="steps")

    def start_step(self):
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.utcnow()

    def complete_step(self, success: bool, output: dict = None, error: str = None):
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        if success:
            self.status = WorkflowStatus.COMPLETED
            if output:
                self.output_data = output
        else:
            self.status = WorkflowStatus.FAILED
            self.error_message = error


class WorkflowEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflow_events"

    execution_id = Column(String(36), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON, default={})
    event_level = Column(String(20), default="info")
    source = Column(String(255), nullable=True)