from app.crud.doctor import DoctorCRUD
from app.crud.slot import SlotCRUD
from app.crud.token import TokenCRUD
from app.db import SessionLocal
from app.schemas import Doctor, Slot, Token


def clear_db():
    db = SessionLocal()
    try:
        # Delete in order to handle foreign keys
        # First tokens, then slots, then doctors

        # Delete all tokens
        db.query(Token).delete()

        # Delete all slots
        db.query(Slot).delete()

        # Delete all doctors
        db.query(Doctor).delete()

        db.commit()
        print("Database cleared successfully")

    except Exception as e:
        db.rollback()
        print(f"Error clearing database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    clear_db()
