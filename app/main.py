"""Punto de entrada de la API Colección de Videojuegos."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (registra los modelos en el metadata)
from app.database import Base, SessionLocal, engine
from app.routers import (
    colecciones,
    desarrolladoras,
    estadisticas,
    generos,
    plataformas,
    videojuegos,
)
from app.seed import seed_si_vacio


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crea las tablas y carga datos de ejemplo al arrancar."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_si_vacio(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="API Colección de Videojuegos",
    description=(
        "Backend REST para gestionar una colección de videojuegos.\n\n"
        "**Apartados:**\n"
        "1. **Videojuegos** — CRUD con carátula, descripción, filtros y paginación\n"
        "2. **Plataformas** — CRUD\n"
        "3. **Géneros** — CRUD\n"
        "4. **Desarrolladoras** — CRUD\n"
        "5. **Colección** — tus ejemplares: estado, precio, valoración y favoritos\n"
        "6. **Estadísticas** — resúmenes y conteos\n\n"
        "CORS abierto: puedes llamarla desde cualquier página web (fetch/axios)."
    ),
    version="1.0.0",
    lifespan=lifespan,
    contact={"name": "API Colección de Videojuegos"},
)

# CORS: permite peticiones desde cualquier frontend (páginas web, Postman...)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(videojuegos.router)
app.include_router(plataformas.router)
app.include_router(generos.router)
app.include_router(desarrolladoras.router)
app.include_router(colecciones.router)
app.include_router(estadisticas.router)


@app.get("/", tags=["General"], summary="Información de la API")
def raiz():
    return {
        "mensaje": "API Colección de Videojuegos",
        "version": "1.0.0",
        "documentacion_interactiva": "/docs",
        "openapi": "/openapi.json",
        "apartados": {
            "videojuegos": "/api/videojuegos",
            "plataformas": "/api/plataformas",
            "generos": "/api/generos",
            "desarrolladoras": "/api/desarrolladoras",
            "colecciones": "/api/colecciones",
            "estadisticas": "/api/estadisticas/resumen",
        },
    }


@app.get("/api/salud", tags=["General"], summary="Comprobar que la API vive")
def salud():
    return {"estado": "ok"}
