# API Colección de Videojuegos

Backend REST completo hecho con **FastAPI** para gestionar una colección de
videojuegos. Pensada para consumirse desde páginas web (fetch/axios) o desde
**Postman**: cada videojuego devuelve su **carátula**, **descripción**, géneros,
plataformas y desarrolladora en un solo JSON.

Incluye **autenticación con JSON Web Tokens (JWT)** y **roles**: se puede crear
cuenta, iniciar sesión y cada usuario tiene **su propia colección**. Hay tres
roles: **usuario** (por defecto), **gestor** (edita el catálogo) y **admin**
(además administra las cuentas).

## Arranque rápido

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

- **Panel web "Ludoteca"** (interfaz gráfica): <http://localhost:8000/panel>
- Pantalla de **login / registro**: <http://localhost:8000/panel/login.html>
- Documentación interactiva (Swagger): <http://localhost:8000/docs>
- Documentación alternativa (ReDoc): <http://localhost:8000/redoc>
- Índice de la API: <http://localhost:8000/>

> La base de datos (SQLite, archivo `coleccion_videojuegos.db`) se crea sola al
> arrancar y se carga con datos de ejemplo: 10 juegos clásicos, 6 plataformas,
> 8 géneros, 9 desarrolladoras y 6 ejemplares de colección. Si quieres empezar
> de cero, borra el archivo `.db` y reinicia el servidor.

### Cuenta de ejemplo

Los datos de ejemplo pertenecen a una cuenta creada automáticamente:

| Email | Contraseña | Rol |
|-------|------------|-----|
| `admin@ludoteca.local` | `admin123` | admin |

Cualquier persona puede **crear su propia cuenta** desde el panel o con
`POST /api/auth/registro`; empezará con el rol **usuario** y la colección vacía.

## Roles y permisos

| Rol | Colección propia | Catálogo (juegos, plataformas, géneros, desarrolladoras) | Usuarios |
|-----|:---:|:---:|:---:|
| `usuario` | Gestionar la suya | Solo lectura | — |
| `gestor` | Gestionar la suya | Crear, editar y borrar | — |
| `admin` | Gestionar la suya | Crear, editar y borrar | Listar, buscar y cambiar roles |

- El rol se asigna al registrarse (`usuario`) y solo un **admin** puede
  cambiarlo (`PATCH /api/usuarios/{id}/rol`).
- Escribir en el catálogo (POST/PUT/DELETE) exige rol `gestor` o `admin`
  (si no, `403 Forbidden`).

## Autenticación (JWT)

Todos los endpoints de la API salvo `/`, `/api/salud`, `/docs` y los de
`/api/auth/*` exigen un token **Bearer**. El token se obtiene al registrarse o
al iniciar sesión.

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/auth/registro` | Crea la cuenta y devuelve el token (201) |
| POST | `/api/auth/login` | Inicia sesión y devuelve el token |
| GET | `/api/auth/yo` | Devuelve el usuario del token (requiere token) |

Ejemplo de registro:

```bash
curl -X POST http://localhost:8000/api/auth/registro \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Maic", "email": "maic@ejemplo.com", "password": "secreto123"}'
```

Respuesta:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expira_en_segundos": 28800,
  "usuario": { "id": 2, "nombre": "Maic", "email": "maic@ejemplo.com", "rol": "usuario", "es_admin": false, "activo": true }
}
```

Y para usar el token en cualquier petición:

```bash
curl http://localhost:8000/api/colecciones \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Detalles:

- El token es un **JWT firmado (HS256)** con validez de **8 horas** (`exp`).
- Las contraseñas se guardan con **hash bcrypt** (nunca en claro).
- En Swagger (`/docs`) pulsa **Authorize** y pega el token para probar.
- La clave de firma se puede cambiar con la variable de entorno
  `LUDOTECA_SECRET_KEY` (por defecto hay una de desarrollo).
- La **colección es por usuario**: cada cuenta solo ve y gestiona sus propios
  ejemplares. El catálogo (juegos, plataformas, géneros, desarrolladoras) es
  compartido.

### Datos de prueba de la saga Trails

Para ampliar los datos de prueba con **11 juegos de la saga
*The Legend of Heroes: Trails*** (más el género JRPG, la desarrolladora
Nihon Falcom y 4 ejemplares de colección):

```bash
python -m app.datos_prueba
```

Es idempotente: se puede ejecutar tantas veces como quieras sin duplicar nada.
Con eso la BD queda con **21 juegos** en total.

## Apartados

| # | Apartado | Prefijo | Qué hace |
|---|----------|---------|----------|
| 0 | **Autenticación** | `/api/auth` | Registro, login y usuario actual con JWT |
| 1 | **Videojuegos** | `/api/videojuegos` | CRUD completo + búsqueda, filtros y paginación. Es el corazón de la API: carátula, descripción, año, PEGI, puntuación, plataformas, géneros y desarrolladora |
| 2 | **Plataformas** | `/api/plataformas` | CRUD de plataformas (PC, PS5, Switch...) |
| 3 | **Géneros** | `/api/generos` | CRUD de géneros (RPG, Indie, Metroidvania...) |
| 4 | **Desarrolladoras** | `/api/desarrolladoras` | CRUD de estudios/empresas |
| 5 | **Colección** | `/api/colecciones` | Tus ejemplares: estado, fecha y precio de compra, valoración, favoritos y notas (por usuario) |
| 6 | **Estadísticas** | `/api/estadisticas` | Resumen de tu colección, conteos por plataforma/género/estado y top valoraciones |
| 7 | **Usuarios** | `/api/usuarios` | Listar, buscar y cambiar el rol de las cuentas (**solo admin**) |

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

> Cada usuario tiene **su propia colección**: los ejemplares se filtran por el
> usuario del token. Un mismo juego solo puede estar una vez por plataforma en
> *tu* colección (devuelve `409` si se repite); otra cuenta puede tenerlo sin
> problema.

### 6. Estadísticas

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/estadisticas/resumen` | Totales, favoritos, valoración media e inversión |
| GET | `/api/estadisticas/por-plataforma` | Juegos y ejemplares por plataforma |
| GET | `/api/estadisticas/por-genero` | Juegos por género |
| GET | `/api/estadisticas/por-estado` | Ejemplares agrupados por estado |
| GET | `/api/estadisticas/top-valoraciones` | 10 ejemplares mejor valorados |

### 7. Usuarios

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/usuarios` | Listado paginado con búsqueda (`q`) y filtro por `rol` (**admin**) |
| GET | `/api/usuarios/{id}` | Detalle de una cuenta (**admin**) |
| PATCH | `/api/usuarios/{id}/rol` | Cambiar el rol: `usuario`, `gestor` o `admin` (**admin**) |

Reglas: un admin no puede cambiarse su **propio** rol (`400`) ni quitar el
**último admin** que queda (`409`).

## Panel web "Ludoteca"

Interfaz gráfica incluida y servida por la propia API en
**<http://localhost:8000/panel>**. Está hecha con HTML, CSS y JavaScript
"vanilla" (sin build, sin frameworks) y consume los 6 apartados de la API.

- **🔐 Login / registro**: al entrar sin sesión te redirige a
  <http://localhost:8000/panel/login.html>, una pantalla con el mismo estilo
  del panel (pestañas *Iniciar sesión* / *Crear cuenta*). Al autenticarte se
  guarda el token y te **redirige al panel**. El botón *Salir* cierra la sesión.
- **🗂️ Catálogo**: rejilla de carátulas con búsqueda y filtros por género,
  plataforma, desarrolladora y orden; paginación. Cada tarjeta abre una
  **ficha** con carátula grande, descripción, nota, PEGI y plataformas.
- **📚 Mi colección**: tus ejemplares con su estado, valoración y precio.
  Puedes marcarlos como favoritos, cambiar el estado/valoración al vuelo
  (PUT) o quitarlos (DELETE).
- **📊 Estadísticas**: KPIs (juegos, favoritos, nota media, inversión...) y
  gráficas de barras por género, plataforma y estado, además del top de
  mejores valoraciones.
- **CRUD desde la interfaz**: botón "＋ Nuevo juego" y editar/eliminar juegos
  (solo **gestor/admin**), y "Añadir a mi colección" desde cada ficha.
- **👥 Usuarios** (solo **admin**): pestaña con buscador (lupa) por nombre,
  email o rol y un selector para asignar el rol de cada cuenta. En la cabecera
  se muestra el rol del usuario conectado.

El panel detecta automáticamente la URL de la API: si se sirve desde FastAPI
usa rutas relativas y, si abres el HTML como archivo local, apunta a
`http://localhost:8000`. Todas las llamadas llevan la cabecera
`Authorization: Bearer <token>`.

## Uso desde Postman

1. Arranca el servidor (`python -m uvicorn app.main:app --port 8000`).
2. Importa el archivo **`postman_collection.json`** en Postman
   (*Import → File*).
3. La variable `base_url` ya apunta a `http://localhost:8000`.
4. Ejecuta primero **«0. Autenticación → Iniciar sesión»**: guarda el token
   automáticamente en la variable `token` (auth *Bearer* a nivel de colección),
   así el resto de peticiones ya van autenticadas.
5. Ejecuta el resto de carpetas: General, 1. Videojuegos, 2. Plataformas,
   3. Géneros, 4. Desarrolladoras, 5. Colección, 6. Estadísticas y
   7. Usuarios (solo funciona con el token del admin).

## Uso desde una página web

CORS está abierto, así que cualquier frontend puede llamarla. Recuerda enviar
el token en la cabecera `Authorization`:

```js
// 1) Inicia sesión y guarda el token
const login = await fetch("http://localhost:8000/api/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email: "admin@ludoteca.local", password: "admin123" }),
}).then((r) => r.json());

const token = login.access_token;

// 2) Lista juegos y píntalos en tarjetas
const { items } = await fetch(
  "http://localhost:8000/api/videojuegos?por_pagina=12",
  { headers: { Authorization: "Bearer " + token } }
).then((r) => r.json());

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
// Búsqueda con filtro (con el mismo token)
const { items } = await fetch(
  "http://localhost:8000/api/videojuegos?q=mario&genero=Plataformas",
  { headers: { Authorization: "Bearer " + token } }
).then(r => r.json());
```

## Pruebas

Con el servidor levantado:

```bash
python tests/probar_api.py
```

Ejecuta ~66 comprobaciones (CRUD de los 7 apartados, filtros, paginación,
validaciones, códigos 404/409/422 y **autenticación JWT**: registro, login,
rechazo sin token, aislamiento de la colección por usuario y **roles**: un
`usuario` no puede escribir en el catálogo (`403`), un `gestor` sí, y solo un
`admin` administra las cuentas).

## Estructura del proyecto

```
├── app/
│   ├── main.py            # App FastAPI, CORS, lifespan, raíz
│   ├── database.py        # SQLite + SQLAlchemy (sesiones, PRAGMA FK, migración)
│   ├── models.py          # Modelos ORM (tablas y relaciones, incl. Usuario)
│   ├── schemas.py         # Esquemas Pydantic (entrada/salida)
│   ├── seguridad.py       # Hash de contraseñas y tokens JWT
│   ├── seed.py            # Datos de ejemplo + cuenta admin
│   ├── datos_prueba.py     # Añade la saga Trails (idempotente)
│   └── routers/
│       ├── auth.py            # 0. Registro / login / usuario actual (JWT) + 7. Usuarios (roles)
│       ├── videojuegos.py     # 1. CRUD + filtros + paginación
│       ├── plataformas.py     # 2. CRUD
│       ├── generos.py         # 3. CRUD
│       ├── desarrolladoras.py # 4. CRUD
│       ├── colecciones.py     # 5. Colección personal (por usuario)
│       └── estadisticas.py    # 6. Estadísticas
├── tests/probar_api.py     # Batería de pruebas
├── frontend/               # Panel web "Ludoteca"
│   ├── index.html          # Panel principal
│   ├── login.html          # Login / registro
│   ├── styles.css
│   ├── app.js              # Lógica del panel
│   └── auth.js             # Lógica de login / registro
├── postman_collection.json # Colección lista para importar
├── requirements.txt
└── README.md
```

## Notas

- Las `caratula_url` de los datos de ejemplo apuntan a `placehold.co`
  (imágenes de relleno). Sustituirlas por portadas reales es solo hacer
  `PUT /api/videojuegos/{id}` con la URL de la imagen que quieras
  (por ejemplo, la de RAWG, IGDB o Wikipedia).
- Autenticación: las contraseñas se guardan con **bcrypt** y los tokens se
  firman con HS256. Define `LUDOTECA_SECRET_KEY` (y opcionalmente
  `LUDOTECA_TOKEN_MINUTOS`) en el entorno para producción; si no, se usan
  valores de desarrollo.
- Código de estado: `200` OK · `201` creado · `401` sin autenticar ·
  `403` sin permisos (rol insuficiente) · `404` no existe ·
  `409` conflicto/duplicado · `422` datos inválidos.
