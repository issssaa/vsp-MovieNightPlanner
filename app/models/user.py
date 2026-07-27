"""SQLAlchemy ORM model for a User.

Identity only: a unique username and an optional display name. No password, no
email. See Design Decision 5 in the design document — M1 has no authentication,
so there is no credential to store or leak.
"""

from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    display_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Deleting a user removes their tracking rows but never the shared media rows.
    entries = relationship(
        "UserMedia",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
