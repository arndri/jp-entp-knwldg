from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _build_engine():
    settings = get_settings()
    database_url = settings.database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(database_url, pool_pre_ping=True)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    bootstrap_default_users()


def get_db_session() -> Generator[Session, None, None]:
    init_db()
    with SessionLocal() as session:
        yield session


def bootstrap_default_users() -> None:
    from sqlalchemy import select

    from app.models import User
    from app.services.auth import hash_password

    settings = get_settings()
    with SessionLocal() as session:
        existing_emails = set(session.scalars(select(User.email)).all())
        users = []
        if settings.bootstrap_admin_email not in existing_emails:
            users.append(
                User(
                    email=settings.bootstrap_admin_email,
                    password_hash=hash_password(settings.bootstrap_admin_password),
                    role="admin",
                )
            )
        if settings.bootstrap_user_email not in existing_emails:
            users.append(
                User(
                    email=settings.bootstrap_user_email,
                    password_hash=hash_password(settings.bootstrap_user_password),
                    role="user",
                )
            )
        if users:
            session.add_all(users)
            session.commit()
