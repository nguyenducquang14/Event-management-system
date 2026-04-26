"""
app/database/schemas.py
Pydantic schemas — type-safe data models cho toàn bộ hệ thống
Dùng để validate input và serialize output, không phụ thuộc SQLAlchemy
"""

from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, field_validator, model_validator


# ── Enums ────────────────────────────────────────────────────

VenueStatus   = Literal["Available", "Booked", "Maintenance"]
EventStatus   = Literal["Draft", "Scheduled", "Full", "Completed", "Cancelled"]
AttendStatus  = Literal["Registered", "Attended", "No-show"]
FinanceType   = Literal["Income", "Expense"]


# ════════════════════════════════════════════════════════════
# VENUES
# ════════════════════════════════════════════════════════════

class VenueCreate(BaseModel):
    venue_name:          str
    address:             str
    capacity:            int           = 0
    availability_status: VenueStatus   = "Available"
    phone_number:        Optional[str] = None

    @field_validator("capacity")
    @classmethod
    def capacity_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Capacity phải >= 0")
        return v


class VenueRead(VenueCreate):
    venue_id: int

    model_config = {"from_attributes": True}


# ════════════════════════════════════════════════════════════
# ORGANIZERS
# ════════════════════════════════════════════════════════════

class OrganizerCreate(BaseModel):
    organizer_name: str
    address:        str
    phone_number:   str
    email:          Optional[str] = None
    department:     Optional[str] = None


class OrganizerRead(OrganizerCreate):
    organizer_id: int

    model_config = {"from_attributes": True}


# ════════════════════════════════════════════════════════════
# EVENTS
# ════════════════════════════════════════════════════════════

class EventCreate(BaseModel):
    event_name:   str
    start_time:   datetime
    end_time:     datetime
    venue_id:     int
    organizer_id: int
    status:       EventStatus     = "Draft"
    max_capacity: Optional[int]   = None
    description:  Optional[str]   = None

    @model_validator(mode="after")
    def end_after_start(self) -> "EventCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time phải sau start_time")
        return self

    @field_validator("max_capacity")
    @classmethod
    def cap_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("max_capacity phải > 0 hoặc None")
        return v


class EventRead(EventCreate):
    event_id: int

    model_config = {"from_attributes": True}


class EventSummary(BaseModel):
    """Kết quả từ view_event_summary"""
    event_id:             int
    event_name:           str
    start_time:           datetime
    status:               str
    venue_name:           str
    total_registered:     int
    total_attended:       int
    total_noshow:         int
    attendance_rate_pct:  Optional[Decimal]
    total_income:         Decimal
    total_expense:        Decimal
    net_balance:          Decimal

    model_config = {"from_attributes": True}


# ════════════════════════════════════════════════════════════
# GUESTS
# ════════════════════════════════════════════════════════════

class GuestCreate(BaseModel):
    guest_name:   str
    email:        str
    phone_number: Optional[str] = None
    address:      Optional[str] = None

    @field_validator("email")
    @classmethod
    def email_format(cls, v: str) -> str:
        import re
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError("Email không hợp lệ")
        return v.lower().strip()

    @field_validator("guest_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Tên không được để trống")
        return v.strip()


class GuestRead(GuestCreate):
    guest_id:   int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class GuestActivity(BaseModel):
    """Kết quả từ view_guest_activity"""
    guest_id:             int
    guest_name:           str
    email:                str
    total_registrations:  int
    total_attended:       int
    total_noshow:         int
    personal_rate_pct:    Optional[Decimal]
    last_registration:    Optional[date]

    model_config = {"from_attributes": True}


# ════════════════════════════════════════════════════════════
# REGISTRATIONS
# ════════════════════════════════════════════════════════════

class RegistrationCreate(BaseModel):
    event_id:          int
    guest_id:          int
    registration_date: date              = date.today()
    attendance_status: AttendStatus      = "Registered"
    checkin_time:      Optional[datetime] = None


class RegistrationRead(RegistrationCreate):
    registration_id: int

    model_config = {"from_attributes": True}


class RegistrationDetail(BaseModel):
    """Kết quả JOIN đầy đủ"""
    registration_id:   int
    event_name:        str
    guest_name:        str
    email:             str
    registration_date: date
    attendance_status: str
    checkin_time:      Optional[datetime]

    model_config = {"from_attributes": True}


# ════════════════════════════════════════════════════════════
# FINANCES
# ════════════════════════════════════════════════════════════

class FinanceCreate(BaseModel):
    event_id:         int
    type:             FinanceType
    amount:           Decimal
    description:      Optional[str] = None
    transaction_date: date           = date.today()
    created_by:       Optional[int]  = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Số tiền phải > 0")
        return v


class FinanceRead(FinanceCreate):
    finance_id: int

    model_config = {"from_attributes": True}


class FinanceBalance(BaseModel):
    """Tổng hợp thu-chi một sự kiện"""
    event_id:           int
    event_name:         str
    total_income:       Decimal
    total_expense:      Decimal
    net_balance:        Decimal
    total_transactions: int

    model_config = {"from_attributes": True}


# ════════════════════════════════════════════════════════════
# RESPONSES CHUẨN
# ════════════════════════════════════════════════════════════

class ProcedureResult(BaseModel):
    """Kết quả trả về từ Stored Procedure"""
    success: bool
    message: str
    raw:     str  # chuỗi gốc từ MySQL

    @classmethod
    def from_raw(cls, raw: str) -> "ProcedureResult":
        return cls(
            success=raw.startswith(("OK", "SUCCESS")),
            message=raw.split(":", 1)[-1].strip() if ":" in raw else raw,
            raw=raw,
        )


class DashboardStats(BaseModel):
    """Thống kê tổng quan cho dashboard"""
    total_events:        int
    upcoming_events:     int
    total_guests:        int
    total_registrations: int
    total_attended:      int
    total_income:        Decimal
    total_expense:       Decimal
    net_balance:         Decimal
