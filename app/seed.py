from datetime import datetime, time, timedelta, UTC
from typing import List
from app.crud.doctor import DoctorCRUD
from app.crud.slot import SlotCRUD
from app.db import SessionLocal
from app.models import SlotCreate
from app.schemas import Doctor


def seed_data():
    db = SessionLocal()
    try:
        DoctorCRUD.set_db_session(db)
        SlotCRUD.set_db_session(db)

        doctor_crud = DoctorCRUD()
        slot_crud = SlotCRUD()

        doctors = seed_doctors(doctor_crud)
        seed_slots(slot_crud, doctors)
        print("Seed data created successfully")

    finally:
        db.close()


def seed_doctors(doctor_crud: DoctorCRUD):

    # Create doctors
    doctors = [
        doctor_crud.create_doctor("Dr. Shukla", "Cardiology"),
        doctor_crud.create_doctor("Dr. Verma", "Dermatology"),
        doctor_crud.create_doctor("Dr. Iyer", "Orthopedics"),
        doctor_crud.create_doctor("Dr. Rao", "Pediatrics"),
        doctor_crud.create_doctor("Dr. Nair", "Neurology"),
        doctor_crud.create_doctor("Dr. Arjuna", "Gynecology"),
    ]
    print(f"Created {len(doctors)} doctors.")
    return doctors


def seed_slots(slot_crud: SlotCRUD, doctors: List[Doctor]):
    # Create slots for today
    base_time = time(9, 0)  # 9 AM

    for doctor in doctors:
        for i in range(4):  # 4 slots per doctor
            start = (
                datetime.combine(datetime.today(), base_time) + timedelta(hours=i)
            ).time()
            end = (
                datetime.combine(datetime.today(), start) + timedelta(hours=1)
            ).time()
            slot_crud.create_slot(
                slot_data=SlotCreate(
                    capacity=10,
                    doctor_id=doctor.id,
                    start_time=start,
                    end_time=end,
                ),
                slot_date=datetime.today().date() + timedelta(days=i),
            )
    print(f"Created slots for {len(doctors)} doctors.")

if __name__ == "__main__":
    seed_data()
