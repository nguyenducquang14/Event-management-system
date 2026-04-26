"""
app/models.py
SQLAlchemy ORM models ánh xạ với database Giai đoạn 1
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Integer, String, DateTime, Date, Enum, Text,
    ForeignKey, DECIMAL, Boolean, TIMESTAMP, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.config import Base


# ── Venues ──────────────────────────────────────────────────
class Venue(Base):
    __tablename__ = "Venues"

    venue_id:            Mapped[int]          = mapped_column(Integer, primary_key=True, autoincrement=True)
    venue_name:          Mapped[str]          = mapped_column(String(100), nullable=False)
    address:             Mapped[str]          = mapped_column(String(200), nullable=False)
    capacity:            Mapped[int]          = mapped_column(Integer, default=0)
    availability_status: Mapped[str]          = mapped_column(
        Enum("Available", "Booked", "Maintenance"), default="Available"
    )
    phone_number:        Mapped[Optional[str]] = mapped_column(String(15))

    events: Mapped[List["Event"]] = relationship("Event", back_populates="venue")

    def __repr__(self):
        return f"<Venue {self.venue_id}: {self.venue_name}>"


# ── Organizers ───────────────────────────────────────────────
class Organizer(Base):
    __tablename__ = "Organizers"

    organizer_id:   Mapped[int]          = mapped_column(Integer, primary_key=True, autoincrement=True)
    organizer_name: Mapped[str]          = mapped_column(String(150), nullable=False)
    address:        Mapped[str]          = mapped_column(String(200), nullable=False)
    phone_number:   Mapped[str]          = mapped_column(String(15),  nullable=False)
    email:          Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    department:     Mapped[Optional[str]] = mapped_column(String(100))

    events: Mapped[List["Event"]] = relationship("Event", back_populates="organizer")

    def __repr__(self):
        return f"<Organizer {self.organizer_id}: {self.organizer_name}>"


# ── Events ───────────────────────────────────────────────────
class Event(Base):
    __tablename__ = "Events"

    event_id:     Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_name:   Mapped[str]           = mapped_column(String(150), nullable=False)
    start_time:   Mapped[datetime]      = mapped_column(DateTime, nullable=False)
    end_time:     Mapped[datetime]      = mapped_column(DateTime, nullable=False)
    venue_id:     Mapped[int]           = mapped_column(ForeignKey("Venues.venue_id"), nullable=False)
    organizer_id: Mapped[int]           = mapped_column(ForeignKey("Organizers.organizer_id"), nullable=False)
    status:       Mapped[str]           = mapped_column(
        Enum("Draft", "Scheduled", "Full", "Completed", "Cancelled"), default="Draft"
    )
    max_capacity: Mapped[Optional[int]]  = mapped_column(Integer)
    description:  Mapped[Optional[str]] = mapped_column(Text)

    venue:         Mapped["Venue"]               = relationship("Venue",     back_populates="events")
    organizer:     Mapped["Organizer"]           = relationship("Organizer", back_populates="events")
    registrations: Mapped[List["Registration"]] = relationship("Registration", back_populates="event", cascade="all, delete-orphan")
    finances:      Mapped[List["Finance"]]       = relationship("Finance",      back_populates="event", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Event {self.event_id}: {self.event_name}>"


# ── Guests ───────────────────────────────────────────────────
class Guest(Base):
    __tablename__ = "Guests"

    guest_id:    Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    guest_name:  Mapped[str]           = mapped_column(String(100), nullable=False)
    email:       Mapped[str]           = mapped_column(String(100), nullable=False, unique=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(15))
    address:     Mapped[Optional[str]] = mapped_column(String(200))
    created_at:  Mapped[datetime]      = mapped_column(TIMESTAMP, server_default=func.now())

    registrations: Mapped[List["Registration"]] = relationship("Registration", back_populates="guest", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Guest {self.guest_id}: {self.guest_name}>"


# ── Registrations ────────────────────────────────────────────
class Registration(Base):
    __tablename__ = "Registrations"

    registration_id:   Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id:          Mapped[int]           = mapped_column(ForeignKey("Events.event_id"), nullable=False)
    guest_id:          Mapped[int]           = mapped_column(ForeignKey("Guests.guest_id"), nullable=False)
    registration_date: Mapped[date]          = mapped_column(Date, nullable=False, server_default=func.current_date())
    attendance_status: Mapped[str]           = mapped_column(
        Enum("Registered", "Attended", "No-show"), default="Registered"
    )
    checkin_time:      Mapped[Optional[datetime]] = mapped_column(DateTime)

    event: Mapped["Event"] = relationship("Event", back_populates="registrations")
    guest: Mapped["Guest"] = relationship("Guest", back_populates="registrations")

    def __repr__(self):
        return f"<Registration {self.registration_id}: E{self.event_id}-G{self.guest_id}>"


# ── Finances ─────────────────────────────────────────────────
class Finance(Base):
    __tablename__ = "Finances"

    finance_id:       Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id:         Mapped[int]           = mapped_column(ForeignKey("Events.event_id"), nullable=False)
    type:             Mapped[str]           = mapped_column(Enum("Income", "Expense"), nullable=False)
    amount:           Mapped[Decimal]       = mapped_column(DECIMAL(15, 2), nullable=False)
    description:      Mapped[Optional[str]] = mapped_column(String(200))
    transaction_date: Mapped[date]          = mapped_column(Date, nullable=False, server_default=func.current_date())
    created_by:       Mapped[Optional[int]] = mapped_column(Integer)

    event: Mapped["Event"] = relationship("Event", back_populates="finances")

    def __repr__(self):
        return f"<Finance {self.finance_id}: {self.type} {self.amount}>"
