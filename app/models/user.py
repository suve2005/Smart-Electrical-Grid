"""User model for app_users table.
Contains user information linked to Firebase UID.
All sensitive fields (NIC, employee_id) are hashed before storage.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base
from sqlalchemy.orm import relationship


class AppUser(Base):
    __tablename__ = "app_users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String(120), unique=True, nullable=False, index=True)
    employee_id_hash = Column(String, nullable=False)  # PBKDF2 hashed employee_id
    fullname = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    nic_hash = Column(String, nullable=False)  # PBKDF2 hashed NIC
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False, default=1)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationship to roles
    role = relationship("Role", back_populates="users")

    def __repr__(self) -> str:
        return f"<AppUser(id={self.id}, email={self.email}, firebase_uid={self.firebase_uid[:8]}...)>"