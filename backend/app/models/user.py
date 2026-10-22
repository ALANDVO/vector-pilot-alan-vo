import enum
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base

if TYPE_CHECKING:
    from .evaluation import Evaluation


class Role(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    ANALYST = "analyst"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keycloak_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.ANALYST, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    evaluations: Mapped[list["Evaluation"]] = relationship("Evaluation", back_populates="owner", lazy="selectin")