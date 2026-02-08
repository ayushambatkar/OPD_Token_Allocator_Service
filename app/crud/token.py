from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import TokenCreate, TokenStatus, TokenSource, TokenPriority
from app.schemas import Token


class TokenCRUD:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_token(self, token_data: TokenCreate) -> Token:
        """Create a new token."""
        # Map source to priority
        priority_map = {
            TokenSource.emergency: TokenPriority.EMERGENCY,
            TokenSource.paid: TokenPriority.PAID,
            TokenSource.follow_up: TokenPriority.FOLLOW_UP,
            TokenSource.walk_in: TokenPriority.WALK_IN,
            TokenSource.online: TokenPriority.ONLINE,
        }

        token = Token(
            doctor_id=str(token_data.doctor_id),
            slot_id=str(token_data.slot_id) if token_data.slot_id else None,
            source=token_data.source,
            priority=priority_map[token_data.source],
            status=TokenStatus.active,
            patient_name=token_data.patient_name,
            patient_contact=token_data.patient_contact,
        )
        self.db_session.add(token)
        self.db_session.commit()
        self.db_session.refresh(token)
        return token

    def get_token(self, token_id: str) -> Optional[Token]:
        """Get a token by ID."""
        return self.db_session.query(Token).filter(Token.id == token_id).first()

    def get_tokens_for_slot(self, slot_id: str) -> List[Token]:
        """Get all active tokens for a slot."""
        return (
            self.db_session.query(Token)
            .filter(Token.slot_id == slot_id, Token.status == TokenStatus.active)
            .order_by(Token.priority, Token.created_at)
            .all()
        )

    def get_waiting_tokens_for_doctor(self, doctor_id: str) -> List[Token]:
        """Get all waiting tokens for a doctor."""
        return (
            self.db_session.query(Token)
            .filter(Token.doctor_id == doctor_id, Token.status == TokenStatus.waiting)
            .order_by(Token.priority, Token.created_at)
            .all()
        )

    def get_waiting_tokens_for_doctor_by_date(
        self, doctor_id: str, request_date: date
    ) -> List[Token]:
        """Get waiting tokens for a doctor on a specific date."""
        from sqlalchemy import func, cast, Date

        return (
            self.db_session.query(Token)
            .filter(
                Token.doctor_id == doctor_id,
                Token.status == TokenStatus.waiting,
                cast(Token.created_at, Date) == request_date,
            )
            .order_by(Token.priority, Token.created_at)
            .all()
        )

    def assign_slot_to_token(self, token_id: str, slot_id: str) -> Token:
        """Assign a slot to a token."""
        token = self.get_token(token_id)
        if token:
            token.slot_id = slot_id
            token.status = TokenStatus.active
            self.db_session.commit()
            self.db_session.refresh(token)
        return token

    def update_token_status(
        self, token_id: str, status: TokenStatus
    ) -> Optional[Token]:
        """Update token status."""
        token = self.get_token(token_id)
        if token:
            token.status = status
            self.db_session.commit()
            self.db_session.refresh(token)
        return token
