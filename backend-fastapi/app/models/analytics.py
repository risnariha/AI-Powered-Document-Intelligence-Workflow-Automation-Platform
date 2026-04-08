from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Float, Boolean, Index, BigInteger
from datetime import datetime

from app.models.base import Base, TimestampMixin, UUIDMixin


class QueryLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "query_logs"

    query_text = Column(Text, nullable=False)
    query_type = Column(String(50), nullable=False)
    user_id = Column(String(255), nullable=True)
    session_id = Column(String(255), nullable=True)
    organization_id = Column(String(255), nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)
    documents_retrieved = Column(Integer, nullable=True)
    chunks_retrieved = Column(Integer, nullable=True)
    retrieval_time_ms = Column(Integer, nullable=True)
    llm_model = Column(String(100), nullable=True)
    llm_temperature = Column(Float, nullable=True)
    response_text = Column(Text, nullable=True)
    was_successful = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    user_rating = Column(Integer, nullable=True)
    was_helpful = Column(Boolean, nullable=True)
    metadata = Column(JSON, default={})

    __table_args__ = (
        Index('idx_query_logs_user_id', 'user_id'),
        Index('idx_query_logs_timestamp', 'created_at'),
        Index('idx_query_logs_type', 'query_type', 'created_at'),
        Index('idx_query_logs_performance', 'response_time_ms', 'tokens_used'),
    )


class DocumentAccessLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_access_logs"

    document_id = Column(String(36), nullable=False)
    user_id = Column(String(255), nullable=True)
    session_id = Column(String(255), nullable=True)
    access_type = Column(String(50), nullable=False)
    access_count = Column(Integer, default=1)


class PerformanceMetric(Base, TimestampMixin):
    __tablename__ = "performance_metrics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(Float, nullable=False)
    tags = Column(JSON, default={})
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_performance_metrics_name', 'metric_name', 'timestamp'),
        Index('idx_performance_metrics_timestamp', 'timestamp'),
    )