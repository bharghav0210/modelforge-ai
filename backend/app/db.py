from datetime import datetime, timezone
from uuid import uuid4
from fastapi import Request
from sqlalchemy import create_engine, event, String, ForeignKey, JSON, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

def uid(): return str(uuid4())
def now(): return datetime.now(timezone.utc).isoformat()

class Base(DeclarativeBase): pass

class Dataset(Base):
    __tablename__ = 'datasets'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str]
    storage_name: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=now, index=True)
    info: Mapped[dict] = mapped_column(JSON)

class Experiment(Base):
    __tablename__ = 'experiments'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    dataset_id: Mapped[str] = mapped_column(ForeignKey('datasets.id'), index=True)
    task: Mapped[str] = mapped_column(index=True)
    algorithm: Mapped[str]
    config: Mapped[dict] = mapped_column(JSON)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(default='running', index=True)
    started_at: Mapped[str] = mapped_column(default=now, index=True)
    finished_at: Mapped[str | None]
    duration: Mapped[float | None] = mapped_column(Float)
    error: Mapped[str | None]
    artifact: Mapped[str | None]
    details: Mapped[dict] = mapped_column(JSON, default=dict)

class RegisteredModel(Base):
    __tablename__ = 'models'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    experiment_id: Mapped[str] = mapped_column(ForeignKey('experiments.id'), unique=True, index=True)
    name: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=now)

class PredictionRecord(Base):
    __tablename__ = 'predictions'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    model_id: Mapped[str] = mapped_column(ForeignKey('models.id'), index=True)
    created_at: Mapped[str] = mapped_column(default=now, index=True)
    inputs: Mapped[dict] = mapped_column(JSON)
    outputs: Mapped[dict] = mapped_column(JSON)

def setup_database(directory):
    directory.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f'sqlite:///{directory / "metadata.sqlite3"}', connect_args={'check_same_thread': False})
    @event.listens_for(engine, 'connect')
    def foreign_keys(connection, _): connection.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    return engine, sessionmaker(engine, expire_on_commit=False)

def session(request: Request):
    with request.app.state.sessions() as db:
        yield db
