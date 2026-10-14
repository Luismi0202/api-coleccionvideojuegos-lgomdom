"""Endpoints de autenticación: registro, login y usuario actual (JWT)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario
from app.schemas import TokenSalida, UsuarioCrear, UsuarioLogin, UsuarioSalida
from app.seguridad import (
    MINUTOS_TOKEN,
    crear_token,
    hash_password,
    usuario_actual,
    verificar_password,
)

router = APIRouter(prefix="/api/auth", tags=["0. Autenticación"])


def _respuesta_token(usuario: Usuario) -> TokenSalida:
    return TokenSalida(
        access_token=crear_token(usuario.id),
        token_type="bearer",
        expira_en_segundos=MINUTOS_TOKEN * 60,
        usuario=UsuarioSalida.model_validate(usuario),
    )


@router.post(
    "/registro",
    response_model=TokenSalida,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una cuenta (devuelve token e inicia sesión)",
)
def registro(datos: UsuarioCrear, db: Session = Depends(get_db)):
    ya_existe = db.scalar(
        select(Usuario).where(func.lower(Usuario.email) == datos.email.lower())
    )
    if ya_existe:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya hay una cuenta registrada con el email '{datos.email}'",
        )

    usuario = Usuario(
        nombre=datos.nombre,
        email=datos.email.lower(),
        password_hash=hash_password(datos.password),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return _respuesta_token(usuario)


@router.post(
    "/login",
    response_model=TokenSalida,
    summary="Iniciar sesión y obtener el token JWT",
)
def login(datos: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.scalar(
        select(Usuario).where(func.lower(Usuario.email) == datos.email.strip().lower())
    )
    if usuario is None or not verificar_password(datos.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta está desactivada",
        )
    return _respuesta_token(usuario)


@router.get(
    "/yo",
    response_model=UsuarioSalida,
    summary="Datos del usuario autenticado",
)
def yo(usuario: Usuario = Depends(usuario_actual)):
    return usuario
