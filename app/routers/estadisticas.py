"""Endpoints de estadísticas y resúmenes de la colección."""
from fastapi import APIRouter, Depends
from sqlalchemy import distinct, desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import (
    Desarrolladora,
    Genero,
    ItemColeccion,
    Plataforma,
    Videojuego,
    videojuego_genero,
    videojuego_plataforma,
)
from app.schemas import (
    ColeccionSalida,
    ConteoPorNombre,
    EstadoEstadistica,
    GeneroEstadistica,
    PlataformaEstadistica,
    ResumenEstadisticas,
)

router = APIRouter(prefix="/api/estadisticas", tags=["6. Estadísticas"])


@router.get(
    "/resumen",
    response_model=ResumenEstadisticas,
    summary="Resumen general",
)
def resumen(db: Session = Depends(get_db)):
    """Totales generales: juegos, plataformas, favoritos, gasto..."""
    videojuegos = db.scalar(
        select(func.count()).select_from(Videojuego)
    ) or 0
    plataformas = db.scalar(
        select(func.count()).select_from(Plataforma)
    ) or 0
    generos = db.scalar(select(func.count()).select_from(Genero)) or 0
    desarrolladoras = (
        db.scalar(select(func.count()).select_from(Desarrolladora)) or 0
    )
    ejemplares = db.scalar(
        select(func.count()).select_from(ItemColeccion)
    ) or 0
    favoritos = (
        db.scalar(
            select(func.count())
            .select_from(ItemColeccion)
            .where(ItemColeccion.favorito.is_(True))
        )
        or 0
    )
    valoracion_media = db.scalar(
        select(func.avg(ItemColeccion.valoracion)).where(
            ItemColeccion.valoracion.is_not(None)
        )
    )
    inversion_total = db.scalar(
        select(func.coalesce(func.sum(ItemColeccion.precio_compra), 0.0))
    )

    return ResumenEstadisticas(
        videojuegos=videojuegos,
        plataformas=plataformas,
        generos=generos,
        desarrolladoras=desarrolladoras,
        ejemplares_en_coleccion=ejemplares,
        favoritos=favoritos,
        valoracion_media=(
            round(valoracion_media, 2) if valoracion_media is not None else None
        ),
        inversion_total=round(inversion_total or 0.0, 2),
    )


@router.get(
    "/por-plataforma",
    response_model=list[PlataformaEstadistica],
    summary="Juegos y ejemplares por plataforma",
)
def por_plataforma(db: Session = Depends(get_db)):
    filas = db.execute(
        select(
            Plataforma.nombre,
            Plataforma.fabricante,
            func.count(distinct(videojuego_plataforma.c.videojuego_id)).label(
                "juegos"
            ),
            func.count(distinct(ItemColeccion.id)).label("en_coleccion"),
        )
        .select_from(Plataforma)
        .outerjoin(
            videojuego_plataforma,
            videojuego_plataforma.c.plataforma_id == Plataforma.id,
        )
        .outerjoin(
            ItemColeccion, ItemColeccion.plataforma_id == Plataforma.id
        )
        .group_by(Plataforma.id)
        .order_by(desc("juegos"), Plataforma.nombre)
    ).all()

    return [
        PlataformaEstadistica(
            plataforma=nombre,
            fabricante=fabricante,
            juegos=juegos,
            en_coleccion=en_coleccion,
        )
        for nombre, fabricante, juegos, en_coleccion in filas
    ]


@router.get(
    "/por-genero",
    response_model=list[GeneroEstadistica],
    summary="Juegos por género",
)
def por_genero(db: Session = Depends(get_db)):
    filas = db.execute(
        select(
            Genero.nombre,
            func.count(distinct(videojuego_genero.c.videojuego_id)).label(
                "juegos"
            ),
        )
        .select_from(Genero)
        .outerjoin(
            videojuego_genero,
            videojuego_genero.c.genero_id == Genero.id,
        )
        .group_by(Genero.id)
        .order_by(desc("juegos"), Genero.nombre)
    ).all()

    return [
        GeneroEstadistica(genero=nombre, juegos=juegos)
        for nombre, juegos in filas
    ]


@router.get(
    "/por-estado",
    response_model=list[EstadoEstadistica],
    summary="Ejemplares agrupados por estado",
)
def por_estado(db: Session = Depends(get_db)):
    filas = db.execute(
        select(
            ItemColeccion.estado,
            func.count(ItemColeccion.id).label("cantidad"),
        )
        .group_by(ItemColeccion.estado)
        .order_by(desc("cantidad"))
    ).all()

    return [
        EstadoEstadistica(estado=estado, cantidad=cantidad)
        for estado, cantidad in filas
    ]


@router.get(
    "/top-valoraciones",
    response_model=list[ColeccionSalida],
    summary="Los 10 ejemplares mejor valorados",
)
def top_valoraciones(db: Session = Depends(get_db)):
    return db.scalars(
        select(ItemColeccion)
        .where(ItemColeccion.valoracion.is_not(None))
        .options(
            selectinload(ItemColeccion.videojuego).selectinload(
                Videojuego.plataformas
            ),
            selectinload(ItemColeccion.videojuego).selectinload(
                Videojuego.generos
            ),
            selectinload(ItemColeccion.videojuego).selectinload(
                Videojuego.desarrolladora
            ),
            selectinload(ItemColeccion.plataforma),
        )
        .order_by(desc(ItemColeccion.valoracion), ItemColeccion.id)
        .limit(10)
    ).all()
