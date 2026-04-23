import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.config import get_settings
from app.db.session import get_db, Base
from app.models.user_model import User
from app.models.book_model import Book
from app.models.revoked_token_model import RevokedToken
from app.core.security import hash_password, create_access_token

settings = get_settings()

engine = create_engine(settings.TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def user_token(db, client):
    user = User(
        email = "user@test.com",
        username = "testuser",
        hashed_password = hash_password("Test1234"),
        is_active = True,
        is_superuser = False
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id), scopes=["user"])
    return token

@pytest.fixture(scope="function")
def admin_token(db, client):
    user = User(
        email = "admin@teste.com",
        username = "adminuser",
        hashed_password = hash_password("Test1234"),
        is_active = True,
        is_superuser = True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id), scopes=["admin", "user"])
    return token

@pytest.fixture
def sample_book(db):
    book = Book(
        title = "Clean Code",
        author = "Robert C. Martin",
        description = " handbook of agile software craftsmanship.",
        release_year = 2008
    )

    db.add(book)
    db.commit()
    db.refresh(book)
    return book