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


def _copiar_legacy(conn, admin_id: int) -> None:
    """Copia los ejemplares de ``colecciones_legacy`` a ``colecciones``."""
    conn.exec_driver_sql(
        """
        INSERT INTO colecciones (
            id, usuario_id, videojuego_id, plataforma_id, estado,
            fecha_compra, precio_compra, valoracion, favorito, notas,
            fecha_adicion
        )
        SELECT
            id, ?, videojuego_id, plataforma_id, estado,
            fecha_compra, precio_compra, valoracion, favorito, notas,
            fecha_adicion
        FROM colecciones_legacy
        """,
        (admin_id,),
    )


def _recrear_indices(conn) -> None:
    conn.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_colecciones_usuario_id "
        "ON colecciones (usuario_id)"
    )
    conn.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS ix_colecciones_videojuego_id "
        "ON colecciones (videojuego_id)"
    )


def migrar_colecciones(admin_id: int) -> bool:
    """Adapta la tabla ``colecciones`` al modelo "una colección por usuario".

    Las bases de datos creadas antes de añadir la autenticación tienen la
    tabla sin la columna ``usuario_id`` y con una restricción única que no
    incluye el usuario. Como SQLite no permite quitar restricciones, se
    reconstruye la tabla conservando los datos y asignando los ejemplares
    antiguos al usuario admin.

    SQLite autoconfirma las sentencias DDL, así que la función está pensada
    para poder reanudarse si un intento anterior quedó a medias (por ejemplo,
    si existe la tabla temporal ``colecciones_legacy``).

    Devuelve ``True`` si hubo que tocar la base de datos.
    """
    conn = engine.connect()
    try:
        tablas = {
            fila[0]
            for fila in conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if "colecciones" not in tablas:  # la creará create_all()
            return False

        hubo_cambios = False

        # 1) Reanudar una migración que quedó a medias.
        if "colecciones_legacy" in tablas:
            en_colecciones = conn.exec_driver_sql(
                "SELECT COUNT(*) FROM colecciones"
            ).scalar()
            if not en_colecciones:
                _copiar_legacy(conn, admin_id)
            conn.exec_driver_sql("DROP TABLE colecciones_legacy")
            hubo_cambios = True

        columnas = [
            fila[1]
            for fila in conn.exec_driver_sql("PRAGMA table_info(colecciones)")
        ]
        sql_tabla = (
            conn.exec_driver_sql(
                "SELECT sql FROM sqlite_master "
                "WHERE type='table' AND name='colecciones'"
            ).scalar()
            or ""
        )
        ya_migrada = (
            "usuario_id" in columnas
            and "uq_coleccion_usuario_juego_plataforma" in sql_tabla
        )
        if ya_migrada:
            if hubo_cambios:
                _recrear_indices(conn)
                conn.commit()
            return hubo_cambios

        # 2) Migración completa desde un esquema antiguo (sin usuario_id).
        #    Los índices viajan con la tabla al renombrarla, así que hay que
        #    quitarlos antes de crear la nueva para evitar choques de nombre.
        conn.exec_driver_sql("DROP INDEX IF EXISTS ix_colecciones_usuario_id")
        conn.exec_driver_sql("DROP INDEX IF EXISTS ix_colecciones_videojuego_id")
        conn.exec_driver_sql(
            "ALTER TABLE colecciones RENAME TO colecciones_legacy"
        )
        Base.metadata.tables["colecciones"].create(bind=conn)
        _copiar_legacy(conn, admin_id)
        conn.exec_driver_sql("DROP TABLE colecciones_legacy")
        _recrear_indices(conn)
        conn.commit()
        return True
    finally:
        conn.close()
