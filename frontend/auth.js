/* ============================================================
   Ludoteca · autenticación (registro / inicio de sesión con JWT)
   ============================================================ */

// Igual que en app.js: si se abre como archivo local apuntamos al servidor,
// si se sirve desde FastAPI usamos rutas relativas (mismo origen).
const API = location.protocol === "file:" ? "http://localhost:8000" : "";
const PAGINA_INICIO = location.protocol === "file:" ? "index.html" : "/panel/";

const CLAVE_TOKEN = "ludoteca_token";
const CLAVE_USUARIO = "ludoteca_usuario";

/* ---------- Utilidades ---------- */
const $ = (sel, ctx = document) => ctx.querySelector(sel);

function toast(mensaje, tipo = "ok") {
  const cont = $("#toasts");
  const el = document.createElement("div");
  el.className = `toast ${tipo}`;
  el.textContent = mensaje;
  cont.appendChild(el);
  setTimeout(() => {
    el.classList.add("salir");
    setTimeout(() => el.remove(), 300);
  }, 3400);
}

function mostrarAviso(mensaje) {
  const el = $("#auth-aviso");
  el.textContent = mensaje;
  el.hidden = !mensaje;
}

async function api(ruta, { method = "GET", body } = {}) {
  const res = await fetch(API + ruta, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try { data = await res.json(); } catch (_) { /* sin cuerpo */ }
  if (!res.ok) {
    let mensaje = `Error ${res.status}`;
    if (data && typeof data.detail === "string") mensaje = data.detail;
    else if (data && Array.isArray(data.detail)) mensaje = data.detail.map((d) => d.msg).join(" · ");
    throw new Error(mensaje);
  }
  return data;
}

/* ---------- Sesión ---------- */
function guardarSesion(respuesta) {
  localStorage.setItem(CLAVE_TOKEN, respuesta.access_token);
  localStorage.setItem(CLAVE_USUARIO, JSON.stringify(respuesta.usuario));
}

function haySesion() {
  return Boolean(localStorage.getItem(CLAVE_TOKEN));
}

/* ---------- Cambio de vista ---------- */
function mostrarVista(vista) {
  const esLogin = vista === "login";
  $("#tab-login").classList.toggle("activo", esLogin);
  $("#tab-registro").classList.toggle("activo", !esLogin);
  $("#form-login").hidden = !esLogin;
  $("#form-registro").hidden = esLogin;
  mostrarAviso("");
}

/* ---------- Envío de formularios ---------- */
async function enviarLogin(fd, boton) {
  boton.disabled = true;
  try {
    const respuesta = await api("/api/auth/login", {
      method: "POST",
      body: { email: fd.get("email").trim(), password: fd.get("password") },
    });
    guardarSesion(respuesta);
    toast(`¡Bienvenido, ${respuesta.usuario.nombre}! 🎉`);
    setTimeout(() => { location.href = PAGINA_INICIO; }, 550);
  } catch (e) {
    mostrarAviso(e.message);
    toast(e.message, "error");
    boton.disabled = false;
  }
}

async function enviarRegistro(fd, boton) {
  boton.disabled = true;
  try {
    const respuesta = await api("/api/auth/registro", {
      method: "POST",
      body: {
        nombre: fd.get("nombre").trim(),
        email: fd.get("email").trim(),
        password: fd.get("password"),
      },
    });
    guardarSesion(respuesta);
    toast(`Cuenta creada. ¡A por tu colección, ${respuesta.usuario.nombre}! 🚀`);
    setTimeout(() => { location.href = PAGINA_INICIO; }, 650);
  } catch (e) {
    mostrarAviso(e.message);
    toast(e.message, "error");
    boton.disabled = false;
  }
}

/* ---------- Eventos ---------- */
function conectarEventos() {
  $(".auth-tabs").addEventListener("click", (e) => {
    const tab = e.target.closest("[data-vista]");
    if (tab) mostrarVista(tab.dataset.vista);
  });

  document.querySelectorAll("[data-ir]").forEach((a) => {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      mostrarVista(a.dataset.ir);
    });
  });

  $("#form-login").addEventListener("submit", (e) => {
    e.preventDefault();
    mostrarAviso("");
    enviarLogin(new FormData(e.target), $("button[type=submit]", e.target));
  });

  $("#form-registro").addEventListener("submit", (e) => {
    e.preventDefault();
    mostrarAviso("");
    enviarRegistro(new FormData(e.target), $("button[type=submit]", e.target));
  });

  // Mostrar / ocultar contraseña
  document.querySelectorAll("[data-ver]").forEach((boton) => {
    boton.addEventListener("click", () => {
      const input = boton.parentElement.querySelector("input");
      const visible = input.type === "text";
      input.type = visible ? "password" : "text";
      boton.textContent = visible ? "👁" : "🙈";
    });
  });
}

/* ---------- Arranque ---------- */
document.addEventListener("DOMContentLoaded", () => {
  // Si ya hay sesión, directo al panel.
  if (haySesion()) {
    location.replace(PAGINA_INICIO);
    return;
  }
  conectarEventos();
});
