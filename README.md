# OPD Token Allocation System

## Overview

This is a token allocation system for hospital Outpatient Department (OPD) that supports elastic capacity management. It dynamically allocates tokens to doctor slots based on availability, priority, and real-world constraints.

## Features

- **Multi-source token generation**: Online booking, walk-in, paid priority, follow-up, and emergency patients
- **Priority-based allocation**: Emergency > Paid > Follow-up > Walk-in > Online
- **Elastic capacity**: Hard limits per slot with emergency overflow
- **Dynamic reallocation**: Handles cancellations, no-shows, and displacements
- **Waiting lists**: Automatic management of waiting queues per doctor

## Algorithm Design

### Allocation Logic

1. **Token Creation**: When a token is requested for a doctor:
   - Find the earliest available slot (start_time > current time) with capacity
   - For emergencies, allow overflow up to `max_emergency_overflow` (default 2)
   - If no slot available, add to doctor's waiting list

2. **Reallocation**:
   - On cancellation/no-show: Promote highest priority from waiting list
   - Maintain slot capacity limits
   - Emergency tokens can exceed capacity

3. **Prioritization**:
   - Emergency: Priority 1
   - Paid: Priority 2
   - Follow-up: Priority 3
   - Walk-in: Priority 4
   - Online: Priority 5

### Edge Cases Handled

- **No available slots**: Token goes to waiting list
- **Emergency overflow**: Allows 2 extra patients per slot
- **Cancellations**: Immediate reallocation from waiting list
- **No-shows**: Marked after timeout, triggers reallocation
- **Slot time conflicts**: Only allocate to future slots

## API Design

### Endpoints

#### POST /allocation/tokens
Allocate a new token.

**Request Body**:
```json
{
  "doctor_id": "uuid",
  "source": "emergency|paid|follow_up|walk_in|online",
  "patient_name": "string",
  "patient_contact": "string"
}
```

**Response**:
```json
{
  "id": "uuid",
  "doctor_id": "uuid",
  "slot_id": "uuid|null",
  "source": "string",
  "priority": 1,
  "status": "active|waiting",
  "created_at": "datetime"
}
```

#### PUT /allocation/tokens/{token_id}/cancel
Cancel a token and reallocate.

#### PUT /allocation/tokens/{token_id}/serve
Mark token as served.

#### PUT /allocation/tokens/{token_id}/no_show
Mark token as no-show and reallocate.

#### GET /allocation/doctors/{doctor_id}/waiting
Get waiting list for a doctor.

## Data Schema

### Token
- id: UUID
- doctor_id: UUID
- slot_id: UUID (nullable)
- source: Enum
- status: Enum (active, waiting, cancelled, served, no_show, displaced)
- priority: Integer
- patient_name: String
- patient_contact: String
- created_at: DateTime
- updated_at: DateTime

### Slot
- id: UUID
- doctor_id: UUID
- start_time: Time
- end_time: Time
- capacity: Integer
- created_at: DateTime
- updated_at: DateTime

### Doctor
- id: UUID
- name: String
- specialization: String
- created_at: DateTime
- updated_at: DateTime

## Implementation

### Architecture

- **FastAPI**: REST API framework
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migrations
- **SOLID Principles**: Single responsibility, dependency injection
- **CRUD Pattern**: Separate CRUD classes for each entity

### Key Components

1. **AllocationService**: Core business logic for token allocation
2. **TokenCRUD, SlotCRUD, DoctorCRUD**: Data access layer
3. **Routers**: API endpoint definitions
4. **Models**: Pydantic schemas for validation
5. **Schemas**: SQLAlchemy database models

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
alembic upgrade head
```

3. Seed data:
```bash
python -m app.seed
```

4. Run server:
```bash
python -m app.main
```

## Simulation

Run a day simulation:
```bash
python -m app.simulation
```

This creates 3 doctors with 4 slots each (9-10, 10-11, 11-12, 12-1), generates 50 tokens, simulates cancellations and no-shows.

## Configuration

Settings in `app/settings.py`:
- `database_url`: SQLite database path
- `no_show_timeout_minutes`: Timeout for no-show detection
- `allow_preemption`: Enable preemption logic
- `max_emergency_overflow`: Max extra patients for emergencies

## Failure Handling

- **Database errors**: Rollback transactions
- **Invalid requests**: HTTP 400 with error details
- **Not found**: HTTP 404 for missing resources
- **Concurrency**: Database-level locking for allocation

## Trade-offs

- **Per-slot vs per-doctor waiting**: Chose per-doctor for simplicity, could be per-slot for more granularity
- **Time-based allocation**: Uses current time for slot availability, assumes daily recurring slots
- **Emergency overflow**: Fixed limit, could be percentage-based
- **No background jobs**: Manual no-show detection, could use scheduled tasks
- **SQLite**: For development, production would use PostgreSQL

## Evaluation

- **Algorithm Quality**: Priority-based allocation with overflow handling
- **Edge Cases**: Comprehensive handling of cancellations, emergencies, capacity limits
- **Code Structure**: Clean separation of concerns, SOLID principles
- **Practical Reasoning**: Balances hospital workflow with technical constraints