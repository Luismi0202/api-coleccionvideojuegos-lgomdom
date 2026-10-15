"""Seguridad: hash de contraseñas y tokens JWT."""
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ROL_ADMIN, ROL_GESTOR, Usuario

# En producción define LUDOTECA_SECRET_KEY como variable de entorno.
SECRET_KEY = os.getenv(
    "LUDOTECA_SECRET_KEY", "ludoteca-clave-de-desarrollo-cambiala-en-produccion"
)
ALGORITHM = "HS256"
MINUTOS_TOKEN = int(os.getenv("LUDOTECA_TOKEN_MINUTOS", "480"))  # 8 horas

# Esquema "Bearer": Swagger muestra el botón Authorize para pegar el token.
esquema_bearer = HTTPBearer(
    auto_error=False,
    description="Token JWT obtenido en POST /api/auth/login",
)


# ---------------------------------------------------------------------------
# Contraseñas
# ---------------------------------------------------------------------------
def _bytes_password(password: str) -> bytes:
    # bcrypt solo admite 72 bytes
    return password.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_bytes_password(password), bcrypt.gensalt()).decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_bytes_password(password), password_hash.encode("utf-8"))
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Tokens JWT
# ---------------------------------------------------------------------------
def crear_token(usuario_id: int) -> str:
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario_id),
        "iat": ahora,
        "exp": ahora + timedelta(minutes=MINUTOS_TOKEN),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token(token: str) -> int:
    """Devuelve el id de usuario o lanza 401 si el token no es válido."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o caducado",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# Dependencias de FastAPI
# ---------------------------------------------------------------------------
def usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    """Devuelve el usuario autenticado o lanza 401."""
    if credenciales is None or not credenciales.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado: falta el token Bearer",
            headers={"WWW-Authenticate": "Bearer"},
        )

    usuario = db.get(Usuario, decodificar_token(credenciales.credentials))
    if usuario is None or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario del token no existe o está desactivado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


# ---------------------------------------------------------------------------
# Permisos por rol
# ---------------------------------------------------------------------------
def es_admin(usuario: Usuario) -> bool:
    """True si la cuenta tiene rol de administrador."""
    return usuario.rol == ROL_ADMIN


def puede_gestionar(usuario: Usuario) -> bool:
    """True si la cuenta puede gestionar el catálogo (gestor o admin)."""
    return usuario.rol in (ROL_GESTOR, ROL_ADMIN)


def requiere_gestor(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
    """Permite gestionar el catálogo: administradores y gestores."""
    if not puede_gestionar(usuario):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Necesitas permiso de gestor o administrador para esta acción",
        )
    return usuario


def requiere_admin(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
    """Permite administrar la plataforma: solo administradores."""
    if not es_admin(usuario):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede realizar esta acción",
        )
    return usuario
