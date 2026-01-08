from sqlalchemy import Column, String, Boolean, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from ..database import Base


class PuzzleRun(Base):
    __tablename__ = "puzzle_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    puzzle_id = Column(String(255), nullable=False, index=True)
    user_code = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    stars = Column(Integer)
    error_message = Column(Text)
    execution_log = Column(Text)
    hint = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    metrics = relationship("RunMetrics", back_populates="run", cascade="all, delete-orphan", uselist=False)
    execution_data = relationship("ExecutionData", back_populates="run", cascade="all, delete-orphan", uselist=False)
    execution_plan = relationship("ExecutionPlan", back_populates="run", cascade="all, delete-orphan", uselist=False)
    output_data = relationship("RunOutput", back_populates="run", cascade="all, delete-orphan", uselist=False)


class RunMetrics(Base):
    __tablename__ = "run_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("puzzle_runs.id", ondelete="CASCADE"), nullable=False)
    time_simulated = Column(Float)
    shuffles = Column(Integer)
    stages = Column(Integer)
    skew_detected = Column(Boolean)
    cache_used = Column(Boolean)
    broadcast_used = Column(Boolean)

    run = relationship("PuzzleRun", back_populates="metrics")


class ExecutionData(Base):
    __tablename__ = "execution_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("puzzle_runs.id", ondelete="CASCADE"), nullable=False)
    execution_simulation_json = Column(JSONB)
    stage_flow_json = Column(JSONB)
    cluster_config_json = Column(JSONB)
    dag_structure_json = Column(JSONB)

    run = relationship("PuzzleRun", back_populates="execution_data")


class ExecutionPlan(Base):
    __tablename__ = "execution_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("puzzle_runs.id", ondelete="CASCADE"), nullable=False)
    physical_plan = Column(Text)
    logical_plan = Column(Text)
    spark_ui_url = Column(String(512))

    run = relationship("PuzzleRun", back_populates="execution_plan")


class RunOutput(Base):
    __tablename__ = "run_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("puzzle_runs.id", ondelete="CASCADE"), nullable=False)
    output_data_json = Column(JSONB)
    expected_output_json = Column(JSONB)

    run = relationship("PuzzleRun", back_populates="output_data")
