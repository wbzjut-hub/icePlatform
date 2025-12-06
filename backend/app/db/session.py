from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# SQLite 需要 check_same_thread=False
connect_args = {"check_same_thread": False} if "sqlite" in settings.SQLALCHEMY_DATABASE_URL else {}

engine = create_engine(settings.SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

# 开启 WAL 模式 (Better Concurrency, Fix iCloud locking)
if "sqlite" in settings.SQLALCHEMY_DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL") # Optional: faster writes
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()