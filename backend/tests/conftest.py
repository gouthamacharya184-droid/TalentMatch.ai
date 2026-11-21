import pytest
from app.database.session import Base, engine, SessionLocal
from app.database.seed import seed_database


@pytest.fixture(scope="session", autouse=True)
def initialize_test_environment():
    """Ensure database schema is created and default seed data is populated for all tests."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield

