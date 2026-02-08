from sqlalchemy.orm import Session


class OPDCRUD:
    _db_session: Session = None

    @classmethod
    def set_db_session(cls, db_session: Session):
        cls._db_session = db_session

    def __init__(self):
        if self._db_session is None:
            raise RuntimeError(
                "DB session not set. Call OPDCRUD.set_db_session(db_session) first."
            )
        self.db_session = self._db_session
