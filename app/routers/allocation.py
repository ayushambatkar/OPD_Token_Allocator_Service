from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import db
from app.allocation_service import AllocationService
from app.crud.doctor import DoctorCRUD
from app.crud.slot import SlotCRUD
from app.crud.token import TokenCRUD
from app.models import SlotResponse, TokenCreate, TokenResponse
from app.schemas import Doctor

router = APIRouter(prefix="/allocation", tags=["allocation"])


def get_allocation_service(db_session: Session = Depends(db.get_db)):
    DoctorCRUD.set_db_session(db_session)
    SlotCRUD.set_db_session(db_session)
    TokenCRUD.set_db_session(db_session)
    return AllocationService(DoctorCRUD(), SlotCRUD(), TokenCRUD())


@router.post("/tokens", response_model=TokenResponse)
async def allocate_token(
    token_request: TokenCreate,
    service: AllocationService = Depends(get_allocation_service),
):
    """Allocate a token to a slot or waiting list."""
    try:
        token = service.allocate_token(token_request)
        return TokenResponse.model_validate(token)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/tokens/{token_id}/cancel")
async def cancel_token(
    token_id: str, service: AllocationService = Depends(get_allocation_service)
):
    """Cancel a token and reallocate if possible."""
    if not service.cancel_token(token_id):
        raise HTTPException(status_code=404, detail="Token not found or not active")
    return {"message": "Token cancelled"}


@router.put("/tokens/{token_id}/serve")
async def serve_token(
    token_id: str, service: AllocationService = Depends(get_allocation_service)
):
    """Mark token as served."""
    if not service.serve_token(token_id):
        raise HTTPException(status_code=404, detail="Token not found or not active")
    return {"message": "Token served"}


@router.put("/tokens/{token_id}/no_show")
async def mark_no_show(
    token_id: str, service: AllocationService = Depends(get_allocation_service)
):
    """Mark token as no-show and reallocate."""
    if not service.mark_no_show(token_id):
        raise HTTPException(status_code=404, detail="Token not found or not active")
    return {"message": "Token marked as no-show"}


@router.get("/doctors/{doctor_id}/waiting", response_model=List[TokenResponse])
async def get_waiting_list(
    doctor_id: str, service: AllocationService = Depends(get_allocation_service)
):
    """Get waiting list for a doctor."""
    tokens = service.get_waiting_list(doctor_id)
    return [TokenResponse.model_validate(t) for t in tokens]


@router.get("/slots/{doctor_id}", response_model=List[SlotResponse])
async def get_slots_for_doctor(
    doctor_id: str, service: AllocationService = Depends(get_allocation_service)
):
    """Get slots for a doctor."""
    slots = service.get_slots_for_doctor(doctor_id)
    return [SlotResponse.model_validate(s) for s in slots]


@router.get("/slots", response_model=List[SlotResponse])
async def get_all_slots_for_date(
    date: str = None, service: AllocationService = Depends(get_allocation_service)
):
    """Get all slots, optionally filtered by date."""
    slots = service.get_all_slots_for_date(date)
    return [SlotResponse.model_validate(s) for s in slots]

@router.get("/doctors", response_model=List[Doctor])
async def get_all_doctors(
    service: AllocationService = Depends(get_allocation_service),
):
    """Get all doctors."""
    doctors = service.get_all_doctors()
    return [Doctor.model_validate(d) for d in doctors]
