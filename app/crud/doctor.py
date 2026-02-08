from sqlalchemy.orm import Session
from app.crud.main import OPDCRUD
from app.schemas import Doctor


class DoctorCRUD(OPDCRUD):

    def __init__(self):
        super().__init__()

    def create_doctor(self, name: str, specialization: str) -> Doctor:
        doctor = Doctor(name=name, specialization=specialization)
        self.db_session.add(doctor)
        self.db_session.commit()
        self.db_session.refresh(doctor)
        return doctor

    def get_doctor(self, doctor_id: str) -> Doctor:
        return self.db_session.query(Doctor).filter(Doctor.id == doctor_id).first()

    def list_doctors(self, page: int = 1, page_size: int = 10):
        offset = (page - 1) * page_size
        return self.db_session.query(Doctor).offset(offset).limit(page_size).all()

    def update_doctor(
        self, doctor_id: str, name: str = None, specialization: str = None
    ) -> Doctor:
        doctor = self.get_doctor(doctor_id)
        if not doctor:
            return None
        if name:
            doctor.name = name
        if specialization:
            doctor.specialization = specialization
        self.db_session.commit()
        self.db_session.refresh(doctor)
        return doctor

    def delete_doctor(self, doctor_id: str) -> bool:
        if not doctor_id:
            return False

        doctor = self.get_doctor(doctor_id)

        if not doctor:
            return False

        self.db_session.delete(doctor)
        self.db_session.commit()
        return True
