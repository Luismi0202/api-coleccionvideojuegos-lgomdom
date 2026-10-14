"""Configuración de la base de datos (SQLite + SQLAlchemy 2.0)."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# La BD se guarda como archivo local: ./coleccion_videojuegos.db
DATABASE_URL = "sqlite:///./coleccion_videojuegos.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # necesario para SQLite
)


@event.listens_for(engine, "connect")
def _activar_claves_foraneas(dbapi_connection, connection_record):
    """SQLite tiene las claves foráneas desactivadas por defecto."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Clase base declarativa de todos los modelos ORM."""


def get_db():
    """Dependencia de FastAPI: crea una sesión de BD por cada petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
