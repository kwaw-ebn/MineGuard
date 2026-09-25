import os
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mineguard.db").replace("postgres://", "postgresql://", 1)
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    location_name: Mapped[str] = mapped_column(String(160), index=True)
    report_type: Mapped[str] = mapped_column(String(80))
    area: Mapped[str] = mapped_column(String(80))
    severity: Mapped[int] = mapped_column(Integer)
    recurrence: Mapped[int] = mapped_column(Integer, default=0)
    control: Mapped[str] = mapped_column(String(20))
    review_required: Mapped[bool] = mapped_column(Boolean, default=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="Open")
    assignee: Mapped[str] = mapped_column(String(120), default="Unassigned")
    action_note: Mapped[str] = mapped_column(Text, default="")
    risk_score: Mapped[int] = mapped_column(Integer)
    risk_level: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Measurement(Base):
    __tablename__ = "measurements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    monitoring_point: Mapped[str] = mapped_column(String(160), index=True)
    indicator: Mapped[str] = mapped_column(String(80))
    result_value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(30), default="")
    review_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    observation: Mapped[str] = mapped_column(Text, default="")
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class IncidentIn(BaseModel):
    occurred_at: datetime
    location_name: str = Field(min_length=2, max_length=160)
    report_type: str
    area: str
    severity: int = Field(ge=1, le=4)
    recurrence: int = Field(ge=0, le=2)
    control: str
    review_required: bool = False
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    summary: str = Field(min_length=8, max_length=3000)


class MeasurementIn(BaseModel):
    measured_at: datetime
    monitoring_point: str = Field(min_length=2, max_length=160)
    indicator: str
    result_value: float
    unit: str = ""
    review_threshold: float | None = None
    observation: str = ""


class CaseUpdate(BaseModel):
    status: str = Field(pattern="^(Open|Under review|Action in progress|Closed)$")
    assignee: str = Field(max_length=120)
    action_note: str = Field(default="", max_length=3000)


def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def incident_dict(x: Incident):
    return {c.name: getattr(x, c.name) for c in x.__table__.columns}


def measurement_dict(x: Measurement):
    return {c.name: getattr(x, c.name) for c in x.__table__.columns}


app = FastAPI(title="MineGuard Ghana API", version="1.0.0")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "mineguard-api"}


@app.get("/api/dashboard")
def dashboard(session: Session = Depends(db)):
    total = session.query(func.count(Incident.id)).scalar() or 0
    open_cases = session.query(func.count(Incident.id)).filter(Incident.status != "Closed").scalar() or 0
    priority = session.query(func.count(Incident.id)).filter(Incident.risk_level == "Priority").scalar() or 0
    review_measurements = session.query(func.count(Measurement.id)).filter(Measurement.needs_review.is_(True)).scalar() or 0
    return {"incidents": total, "open_cases": open_cases, "priority_cases": priority, "measurements_needing_review": review_measurements}


@app.get("/api/incidents")
def list_incidents(session: Session = Depends(db)):
    return [incident_dict(x) for x in session.query(Incident).order_by(Incident.created_at.desc()).all()]


@app.post("/api/incidents", status_code=201)
def create_incident(payload: IncidentIn, session: Session = Depends(db)):
    score = payload.severity * 2 + payload.recurrence + (2 if payload.control == "no" else 1 if payload.control == "partial" else 0) + (1 if payload.review_required else 0)
    level = "Priority" if score >= 9 else "Review" if score >= 5 else "Routine"
    item = Incident(**payload.model_dump(), risk_score=score, risk_level=level)
    session.add(item); session.commit(); session.refresh(item)
    return incident_dict(item)


@app.patch("/api/incidents/{incident_id}")
def update_incident(incident_id: int, payload: CaseUpdate, session: Session = Depends(db)):
    item = session.get(Incident, incident_id)
    if not item:
        raise HTTPException(404, "Incident not found")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    session.commit(); session.refresh(item)
    return incident_dict(item)


@app.get("/api/measurements")
def list_measurements(session: Session = Depends(db)):
    return [measurement_dict(x) for x in session.query(Measurement).order_by(Measurement.created_at.desc()).all()]


@app.post("/api/measurements", status_code=201)
def create_measurement(payload: MeasurementIn, session: Session = Depends(db)):
    data = payload.model_dump()
    threshold = data.get("review_threshold")
    data["needs_review"] = threshold is not None and data["result_value"] > threshold
    item = Measurement(**data)
    session.add(item); session.commit(); session.refresh(item)
    return measurement_dict(item)
