# API Colección de Videojuegos

Backend REST completo hecho con **FastAPI** para gestionar una colección de
videojuegos. Pensada para consumirse desde páginas web (fetch/axios) o desde
**Postman**: cada videojuego devuelve su **carátula**, **descripción**, géneros,
plataformas y desarrolladora en un solo JSON.

## Arranque rápido

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

- **Panel web "Ludoteca"** (interfaz gráfica): <http://localhost:8000/panel>
- Documentación interactiva (Swagger): <http://localhost:8000/docs>
- Documentación alternativa (ReDoc): <http://localhost:8000/redoc>
- Índice de la API: <http://localhost:8000/>

> La base de datos (SQLite, archivo `coleccion_videojuegos.db`) se crea sola al
> arrancar y se carga con datos de ejemplo: 10 juegos clásicos, 6 plataformas,
> 8 géneros, 9 desarrolladoras y 6 ejemplares de colección. Si quieres empezar
> de cero, borra el archivo `.db` y reinicia el servidor.

### Datos de prueba de la saga Trails

Para ampliar los datos de prueba con **11 juegos de la saga
*The Legend of Heroes: Trails*** (más el género JRPG, la desarrolladora
Nihon Falcom y 4 ejemplares de colección):

```bash
python -m app.datos_prueba
```

Es idempotente: se puede ejecutar tantas veces como quieras sin duplicar nada.
Con eso la BD queda con **21 juegos** en total.

## Apartados (6 subapartados)

| # | Apartado | Prefijo | Qué hace |
|---|----------|---------|----------|
| 1 | **Videojuegos** | `/api/videojuegos` | CRUD completo + búsqueda, filtros y paginación. Es el corazón de la API: carátula, descripción, año, PEGI, puntuación, plataformas, géneros y desarrolladora |
| 2 | **Plataformas** | `/api/plataformas` | CRUD de plataformas (PC, PS5, Switch...) |
| 3 | **Géneros** | `/api/generos` | CRUD de géneros (RPG, Indie, Metroidvania...) |
| 4 | **Desarrolladoras** | `/api/desarrolladoras` | CRUD de estudios/empresas |
| 5 | **Colección** | `/api/colecciones` | Tus ejemplares: estado, fecha y precio de compra, valoración, favoritos y notas |
| 6 | **Estadísticas** | `/api/estadisticas` | Resumen general, conteos por plataforma/género/estado y top valoraciones |

## Endpoints

### 1. Videojuegos

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/videojuegos` | Listado paginado con filtros |
| GET | `/api/videojuegos/{id}` | Detalle completo |
| POST | `/api/videojuegos` | Crear (201) |
| PUT | `/api/videojuegos/{id}` | Actualizar (parcial) |
| DELETE | `/api/videojuegos/{id}` | Eliminar (borra también sus ejemplares) |

Parámetros de `GET /api/videojuegos`:

| Parámetro | Ejemplo | Descripción |
|-----------|---------|-------------|
| `q` | `?q=zelda` | Busca en título y descripción |
| `genero` | `?genero=RPG` o `?genero=3` | Por ID o nombre |
| `plataforma` | `?plataforma=PC` o `?plataforma=5` | Por ID o nombre |
| `desarrolladora` | `?desarrolladora=Nintendo` | Por ID o nombre |
| `anio_desde` / `anio_hasta` | `?anio_desde=2020` | Rango de años |
| `orden` | `?orden=anio-desc` | `titulo-asc`, `titulo-desc`, `anio-asc`, `anio-desc`, `recientes` |
| `pagina` / `por_pagina` | `?pagina=2&por_pagina=10` | Paginación (máx. 100 por página) |

Ejemplo de respuesta (`GET /api/videojuegos/2`):

```json
{
  "id": 2,
  "titulo": "Elden Ring",
  "descripcion": "Las Tierras Intermedias te esperan...",
  "caratula_url": "https://placehold.co/600x800/1f2937/f9fafb?text=Elden+Ring",
  "anio_lanzamiento": 2022,
  "clasificacion": "PEGI 16",
  "puntuacion": 9.5,
  "desarrolladora": { "id": 1, "nombre": "FromSoftware", "pais": "Japón", ... },
  "plataformas": [ { "id": 1, "nombre": "PC", ... }, ... ],
  "generos": [ { "id": 1, "nombre": "Acción", ... }, ... ]
}
```

Crear un videojuego:

```json
POST /api/videojuegos
{
  "titulo": "Metroid Dread",
  "descripcion": "Samus Aran persigue a los titanes M.M. en ZDR...",
  "caratula_url": "https://i.imgur.com/ejemplo.jpg",
  "anio_lanzamiento": 2021,
  "clasificacion": "PEGI 12",
  "puntuacion": 8.8,
  "desarrolladora_id": 2,
  "plataformas_ids": [5],
  "generos_ids": [1, 5]
}
```

### 2-4. Plataformas, Géneros y Desarrolladoras

CRUD estándar en cada prefijo:

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/plataformas` | Listar |
| GET | `/api/plataformas/{id}` | Detalle |
| POST | `/api/plataformas` | Crear (201) |
| PUT | `/api/plataformas/{id}` | Actualizar |
| DELETE | `/api/plataformas/{id}` | Eliminar |

Mismo patrón para `/api/generos` y `/api/desarrolladoras`.
Reglas: no se puede eliminar algo que esté en uso (devuelve `409 Conflict`),
ni crear duplicados por nombre (`409`).

### 5. Colección

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/colecciones` | Listado paginado (cada ejemplar incluye su videojuego completo) |
| GET | `/api/colecciones/{id}` | Detalle del ejemplar |
| POST | `/api/colecciones` | Añadir juego a la colección (201) |
| PUT | `/api/colecciones/{id}` | Actualizar (parcial) |
| PATCH | `/api/colecciones/{id}/favorito` | Marcar/desmarcar favorito |
| DELETE | `/api/colecciones/{id}` | Quitar de la colección |

Filtros de `GET /api/colecciones`:
`q`, `estado` (`nuevo`, `como nuevo`, `bueno`, `aceptable`, `malo`, `digital`),
`favorito=true|false`, `plataforma`, `valoracion_min`, `orden`
(`fecha-desc`, `fecha-asc`, `valoracion-desc`, `precio-desc`, `titulo-asc`),
`pagina`, `por_pagina`.

> Un mismo juego solo puede estar una vez por plataforma en la colección
> (devuelve `409` si se repite).

### 6. Estadísticas

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/estadisticas/resumen` | Totales, favoritos, valoración media e inversión |
| GET | `/api/estadisticas/por-plataforma` | Juegos y ejemplares por plataforma |
| GET | `/api/estadisticas/por-genero` | Juegos por género |
| GET | `/api/estadisticas/por-estado` | Ejemplares agrupados por estado |
| GET | `/api/estadisticas/top-valoraciones` | 10 ejemplares mejor valorados |

## Panel web "Ludoteca"

Interfaz gráfica incluida y servida por la propia API en
**<http://localhost:8000/panel>**. Está hecha con HTML, CSS y JavaScript
"vanilla" (sin build, sin frameworks) y consume los 6 apartados de la API:

- **🗂️ Catálogo**: rejilla de carátulas con búsqueda y filtros por género,
  plataforma, desarrolladora y orden; paginación. Cada tarjeta abre una
  **ficha** con carátula grande, descripción, nota, PEGI y plataformas.
- **📚 Mi colección**: tus ejemplares con su estado, valoración y precio.
  Puedes marcarlos como favoritos, cambiar el estado/valoración al vuelo
  (PUT) o quitarlos (DELETE).
- **📊 Estadísticas**: KPIs (juegos, favoritos, nota media, inversión...) y
  gráficas de barras por género, plataforma y estado, además del top de
  mejores valoraciones.
- **CRUD desde la interfaz**: botón "＋ Nuevo juego", editar y eliminar
  juegos, y "Añadir a mi colección" desde cada ficha.

El panel detecta automáticamente la URL de la API: si se sirve desde FastAPI
usa rutas relativas y, si abres el HTML como archivo local, apunta a
`http://localhost:8000`.

## Uso desde Postman

1. Arranca el servidor (`python -m uvicorn app.main:app --port 8000`).
2. Importa el archivo **`postman_collection.json`** en Postman
   (*Import → File*).
3. La variable `base_url` ya apunta a `http://localhost:8000`.
4. Ejecuta las carpetas: General, 1. Videojuegos, 2. Plataformas,
   3. Géneros, 4. Desarrolladoras, 5. Colección, 6. Estadísticas.

## Uso desde una página web

CORS está abierto, así que cualquier frontend puede llamarla:

```js
// Listar juegos y pintarlos en tarjetas
const res = await fetch("http://localhost:8000/api/videojuegos?por_pagina=12");
const { items } = await res.json();

items.forEach(juego => {
  document.body.insertAdjacentHTML("beforeend", `
    <article>
      <img src="${juego.caratula_url}" alt="${juego.titulo}">
      <h3>${juego.titulo} (${juego.anio_lanzamiento})</h3>
      <p>${juego.descripcion}</p>
      <small>${juego.generos.map(g => g.nombre).join(", ")}</small>
    </article>
  `);
});
```

```js
// Búsqueda con filtro
const { items } = await fetch(
  "http://localhost:8000/api/videojuegos?q=mario&genero=Plataformas"
).then(r => r.json());
```

## Pruebas

Con el servidor levantado:

```bash
python tests/probar_api.py
```

Ejecuta ~45 comprobaciones (CRUD de los 6 apartados, filtros, paginación,
validaciones y códigos 404/409/422).

## Estructura del proyecto

```
├── app/
│   ├── main.py            # App FastAPI, CORS, lifespan, raíz
│   ├── database.py        # SQLite + SQLAlchemy (sesiones, PRAGMA FK)
│   ├── models.py          # Modelos ORM (tablas y relaciones)
│   ├── schemas.py         # Esquemas Pydantic (entrada/salida)
│   ├── seed.py            # Datos de ejemplo
│   ├── datos_prueba.py     # Añade la saga Trails (idempotente)
│   └── routers/
│       ├── videojuegos.py     # 1. CRUD + filtros + paginación
│       ├── plataformas.py     # 2. CRUD
│       ├── generos.py         # 3. CRUD
│       ├── desarrolladoras.py # 4. CRUD
│       ├── colecciones.py     # 5. Colección personal
│       └── estadisticas.py    # 6. Estadísticas
├── tests/probar_api.py     # Batería de pruebas
├── frontend/               # Panel web "Ludoteca"
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── postman_collection.json # Colección lista para importar
├── requirements.txt
└── README.md
```

## Notas

- Las `caratula_url` de los datos de ejemplo apuntan a `placehold.co`
  (imágenes de relleno). Sustituirlas por portadas reales es solo hacer
  `PUT /api/videojuegos/{id}` con la URL de la imagen que quieras
  (por ejemplo, la de RAWG, IGDB o Wikipedia).
- Código de estado: `200` OK · `201` creado · `404` no existe ·
  `409` conflicto/duplicado · `422` datos inválidos.
