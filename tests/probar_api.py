"""Pruebas rápidas de la API (se ejecutan contra el servidor en :8000)."""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://localhost:8000"
fallos = []


def req(metodo, ruta, cuerpo=None):
    datos = None if cuerpo is None else json.dumps(cuerpo).encode("utf-8")
    r = urllib.request.Request(
        BASE + ruta, data=datos, method=metodo,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def comprobar(nombre, condicion, extra=""):
    estado = "OK " if condicion else "FALLO"
    print(f"[{estado}] {nombre} {extra}")
    if not condicion:
        fallos.append(nombre)


# ---- General --------------------------------------------------------------
codigo, datos = req("GET", "/")
comprobar("GET / responde 200", codigo == 200)

codigo, datos = req("GET", "/api/salud")
comprobar("GET /api/salud ok", codigo == 200 and datos["estado"] == "ok")

# ---- Listados -------------------------------------------------------------
codigo, datos = req("GET", "/api/videojuegos")
comprobar("Listar videojuegos (>= 10 seed)", codigo == 200 and datos["total"] >= 10,
          f"total={datos.get('total')}")

codigo, datos = req("GET", "/api/videojuegos?q=zelda")
comprobar("Búsqueda q=zelda", datos["total"] == 1 and "Zelda" in datos["items"][0]["titulo"])

codigo, datos = req("GET", "/api/videojuegos?genero=RPG")
comprobar("Filtro genero=RPG", datos["total"] >= 3, f"total={datos['total']}")

codigo, datos = req("GET", "/api/videojuegos?genero=3&plataforma=PC")
comprobar("Filtro genero id=3 + plataforma PC", datos["total"] >= 1)

codigo, datos = req("GET", "/api/videojuegos?anio_desde=2020&orden=anio-desc")
comprobar("Filtro rango de años", all(
    i["anio_lanzamiento"] >= 2020 for i in datos["items"]))

codigo, datos = req("GET", "/api/videojuegos?desarrolladora=Nintendo")
comprobar("Filtro por desarrolladora", datos["total"] == 2, f"total={datos['total']}")

codigo, datos = req("GET", "/api/videojuegos?pagina=2&por_pagina=5")
comprobar("Paginación (página 2 de 5)", datos["pagina"] == 2 and len(datos["items"]) == 5)

# ---- CRUD videojuegos -----------------------------------------------------
nuevo = {
    "titulo": "Hollow Knight: Silksong",
    "descripcion": "Hornet viaja a Pharatum como cazadora en esta secuela del metroidvania.",
    "caratula_url": "https://placehold.co/600x800?text=Silksong",
    "anio_lanzamiento": 2025,
    "clasificacion": "PEGI 7",
    "puntuacion": 9.0,
    "desarrolladora_id": 3,
    "plataformas_ids": [1, 5],
    "generos_ids": [5, 6],
}
codigo, datos = req("POST", "/api/videojuegos", nuevo)
comprobar("POST crear videojuego 201", codigo == 201, f"codigo={codigo}")
id_vj = datos.get("id")

codigo, datos = req("GET", f"/api/videojuegos/{id_vj}")
comprobar("GET detalle con relaciones", codigo == 200 and len(datos["plataformas"]) == 2
          and datos["desarrolladora"]["nombre"] == "Team Cherry")

codigo, datos = req("PUT", f"/api/videojuegos/{id_vj}", {"puntuacion": 9.9, "titulo": "Hollow Knight: Silksong"})
comprobar("PUT actualizar parcial", codigo == 200 and datos["puntuacion"] == 9.9)

codigo, datos = req("PUT", f"/api/videojuegos/{id_vj}", {"plataformas_ids": [1]})
comprobar("PUT cambia plataformas", codigo == 200 and len(datos["plataformas"]) == 1)

codigo, datos = req("POST", "/api/videojuegos", {**nuevo, "desarrolladora_id": 999})
comprobar("POST con desarrolladora inexistente 404", codigo == 404, f"codigo={codigo}")

codigo, datos = req("POST", "/api/videojuegos", {**nuevo, "caratula_url": "no-es-url"})
comprobar("POST con caratula no-URL 422", codigo == 422, f"codigo={codigo}")

codigo, datos = req("GET", "/api/videojuegos/99999")
comprobar("GET inexistente 404", codigo == 404)

# ---- CRUD plataformas -----------------------------------------------------
codigo, datos = req("POST", "/api/plataformas", {"nombre": "Dreamcast", "fabricante": "Sega", "anio_lanzamiento": 1998})
comprobar("POST crear plataforma 201", codigo == 201, f"codigo={codigo}")
id_plataforma = datos["id"]

codigo, datos = req("POST", "/api/plataformas", {"nombre": "Dreamcast"})
comprobar("POST duplicado 409", codigo == 409, f"codigo={codigo}")

codigo, datos = req("PUT", f"/api/plataformas/{id_plataforma}", {"fabricante": "Sega (Corporation)"})
comprobar("PUT actualizar plataforma", codigo == 200 and "Corporation" in datos["fabricante"])

codigo, datos = req("DELETE", f"/api/plataformas/{id_plataforma}")
comprobar("DELETE plataforma libre 200", codigo == 200)

codigo, datos = req("DELETE", "/api/plataformas/5")
comprobar("DELETE plataforma en uso 409", codigo == 409, f"codigo={codigo}")

# ---- CRUD géneros ---------------------------------------------------------
codigo, datos = req("POST", "/api/generos", {"nombre": "Terror", "descripcion": "Miedo y supervivencia."})
comprobar("POST crear género 201", codigo == 201)
id_genero = datos["id"]

codigo, datos = req("DELETE", f"/api/generos/{id_genero}")
comprobar("DELETE género libre 200", codigo == 200)

codigo, datos = req("DELETE", "/api/generos/1")
comprobar("DELETE género en uso 409", codigo == 409)

codigo, datos = req("PUT", f"/api/generos/{id_genero}", {"nombre": "Terror"})
comprobar("PUT género eliminado 404", codigo == 404)

# ---- CRUD desarrolladoras -------------------------------------------------
codigo, datos = req("POST", "/api/desarrolladoras", {"nombre": "Larian Studios", "pais": "Bélgica", "web": "https://larian.com"})
comprobar("POST crear desarrolladora 201", codigo == 201)
id_dev = datos["id"]

codigo, datos = req("PUT", f"/api/desarrolladoras/{id_dev}", {"pais": "Bélgica (Gante)"})
comprobar("PUT actualizar desarrolladora", codigo == 200)

codigo, datos = req("DELETE", "/api/desarrolladoras/3")
comprobar("DELETE desarrolladora con juegos 409", codigo == 409)

codigo, datos = req("DELETE", f"/api/desarrolladoras/{id_dev}")
comprobar("DELETE desarrolladora libre 200", codigo == 200)

# ---- CRUD colección -------------------------------------------------------
codigo, datos = req("GET", "/api/colecciones")
comprobar("Listar colección (>= 6 seed)", codigo == 200 and datos["total"] >= 6,
          f"total={datos.get('total')}")

codigo, datos = req("GET", "/api/colecciones?favorito=true")
comprobar("Filtro favoritos", datos["total"] >= 3, f"total={datos['total']}")
favoritos_antes = datos["total"]

codigo, datos = req("GET", "/api/colecciones?estado=digital&valoracion_min=9")
comprobar("Filtro estado+valoración", datos["total"] >= 2, f"total={datos['total']}")

nuevo_item = {
    "videojuego_id": id_vj,
    "plataforma_id": 1,
    "estado": "nuevo",
    "fecha_compra": "2025-09-30",
    "precio_compra": 19.99,
    "valoracion": 9,
    "favorito": False,
    "notas": "Edición física con mapa.",
}
codigo, datos = req("POST", "/api/colecciones", nuevo_item)
comprobar("POST añadir a colección 201", codigo == 201, f"codigo={codigo}")
id_item = datos["id"]

codigo, datos = req("POST", "/api/colecciones", nuevo_item)
comprobar("POST duplicado 409", codigo == 409, f"codigo={codigo}")

codigo, datos = req("POST", "/api/colecciones", {"videojuego_id": 99999})
comprobar("POST con videojuego inexistente 404", codigo == 404)

codigo, datos = req("PUT", f"/api/colecciones/{id_item}", {"valoracion": 10, "estado": "como nuevo"})
comprobar("PUT actualizar ejemplar", codigo == 200 and datos["valoracion"] == 10)

codigo, datos = req("PATCH", f"/api/colecciones/{id_item}/favorito", {"favorito": True})
comprobar("PATCH marcar favorito", codigo == 200 and datos["favorito"] is True)

codigo, datos = req("GET", "/api/colecciones?favorito=true")
comprobar("Filtro favoritos ahora (antes + 1)", datos["total"] == favoritos_antes + 1,
          f"total={datos['total']}")

codigo, datos = req("DELETE", f"/api/colecciones/{id_item}")
comprobar("DELETE ejemplar 200", codigo == 200)

# ---- Estadísticas ---------------------------------------------------------
codigo, datos = req("GET", "/api/estadisticas/resumen")
comprobar("Resumen general", codigo == 200 and datos["videojuegos"] >= 10
          and datos["ejemplares_en_coleccion"] >= 6,
          f"={json.dumps(datos, ensure_ascii=False)}")

codigo, datos = req("GET", "/api/estadisticas/por-plataforma")
comprobar("Por plataforma", codigo == 200 and len(datos) >= 6
          and all("juegos" in d for d in datos))

codigo, datos = req("GET", "/api/estadisticas/por-genero")
comprobar("Por género", codigo == 200 and len(datos) >= 8)

codigo, datos = req("GET", "/api/estadisticas/por-estado")
comprobar("Por estado", codigo == 200 and len(datos) >= 3)

codigo, datos = req("GET", "/api/estadisticas/top-valoraciones")
comprobar("Top valoraciones", codigo == 200 and datos[0]["valoracion"] == 10
          and "videojuego" in datos[0])

# ---- Limpieza: borrar el videojuego creado (prueba cascade) ---------------
codigo, datos = req("DELETE", f"/api/videojuegos/{id_vj}")
comprobar("DELETE videojuego 200", codigo == 200)

codigo, datos = req("GET", f"/api/videojuegos/{id_vj}")
comprobar("Detalle tras borrar 404", codigo == 404)

print()
if fallos:
    print(f"RESULTADO: {len(fallos)} fallo(s): {fallos}")
    sys.exit(1)
print("RESULTADO: todas las pruebas pasaron [OK]")
