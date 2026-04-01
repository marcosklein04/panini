const CLAVE_ESTADO = "panini_sesion_publica";
const CLAVE_ESTADO_ANTERIOR = "panini_prueba";

const estadoInicial = {
    tokenPublico: "",
    triviaId: "",
    triviaNombre: "",
    fotoId: "",
    resultadoId: "",
    figuritaId: "",
    fotoOriginalUrl: "",
    recorteUrl: "",
    figuritaUrl: "",
    estadoSesion: "pendiente",
    estadoFoto: "pendiente",
    estadoRecorte: "pendiente",
    estadoFigurita: "pendiente",
    triviaCompletada: false,
    puedeSubirFoto: false,
    preguntasRespondidas: 0,
    preguntasTotales: 0,
    camposCompletos: 0,
    camposTotales: 6,
    progresoPorcentaje: 0,
};

const estado = cargarEstado();
let cacheEquipos = [];
let temporizadorMensaje = null;
let temporizadorRecorte = null;
let temporizadorFigurita = null;

const elementos = {
    body: document.body,
    etapaActual: document.getElementById("etapa-actual"),
    descripcionEtapa: document.getElementById("descripcion-etapa"),
    valorProgreso: document.getElementById("valor-progreso"),
    detalleProgreso: document.getElementById("detalle-progreso"),
    barraProgreso: document.getElementById("barra-progreso"),
    indicadorActividad: document.getElementById("indicador-actividad"),
    textoActividad: document.getElementById("texto-actividad"),
    mensajeGlobal: document.getElementById("mensaje-global"),
    estadoTrivia: document.getElementById("estado-trivia"),
    estadoSesion: document.getElementById("estado-sesion"),
    estadoFoto: document.getElementById("estado-foto"),
    estadoRecorte: document.getElementById("estado-recorte"),
    estadoFigurita: document.getElementById("estado-figurita"),
    detalleModuloSesion: document.getElementById("estado-modulo-sesion"),
    detalleModuloTrivia: document.getElementById("estado-modulo-trivia"),
    detalleModuloImagen: document.getElementById("estado-modulo-imagen"),
    detalleModuloFigurita: document.getElementById("estado-modulo-figurita"),
    chipModuloSesion: document.getElementById("chip-modulo-sesion"),
    chipModuloTrivia: document.getElementById("chip-modulo-trivia"),
    chipModuloImagen: document.getElementById("chip-modulo-imagen"),
    chipModuloFigurita: document.getElementById("chip-modulo-figurita"),
    moduloSesion: document.getElementById("modulo-sesion"),
    moduloTrivia: document.getElementById("modulo-trivia"),
    moduloImagen: document.getElementById("modulo-imagen"),
    moduloFigurita: document.getElementById("modulo-figurita"),
    resumenSesion: document.getElementById("modulo-resumen-sesion"),
    resumenTrivia: document.getElementById("modulo-resumen-trivia"),
    resumenImagen: document.getElementById("modulo-resumen-imagen"),
    resumenFigurita: document.getElementById("modulo-resumen-figurita"),
    contenedorPreguntas: document.getElementById("contenedor-preguntas"),
    vistaOriginal: document.getElementById("vista-previa-original"),
    vistaRecorte: document.getElementById("vista-previa-recorte"),
    vistaFigurita: document.getElementById("vista-previa-figurita"),
    marcoOriginal: document.getElementById("marco-original"),
    marcoRecorte: document.getElementById("marco-recorte"),
    marcoFigurita: document.getElementById("marco-figurita"),
    inputArchivo: document.getElementById("input-archivo"),
    formularioTrivia: document.getElementById("form-trivia"),
    formularioSubida: document.getElementById("form-subida"),
    formularioProcesar: document.getElementById("form-procesar"),
    formularioFigurita: document.getElementById("form-figurita"),
    botonReiniciar: document.getElementById("boton-reiniciar"),
};

const fases = {
    sesion: {
        titulo: "Entrando al estadio",
        descripcion: "Estamos preparando tu recorrido y conectando tu sesion anonima.",
    },
    trivia: {
        titulo: "Completa la ficha del jugador",
        descripcion: "Responde las preguntas y desbloquea la foto oficial para tu figurita.",
    },
    imagen: {
        titulo: "Sube la foto oficial",
        descripcion: "La ficha ya esta completa. Ahora entra la imagen protagonista.",
    },
    procesando: {
        titulo: "La IA esta recortando tu silueta",
        descripcion: "Gemini y el pipeline visual estan preparando el acabado final.",
    },
    figurita: {
        titulo: "Genera la figurita final",
        descripcion: "Ya tienes el recorte listo. Solo falta componer la pieza final.",
    },
    completado: {
        titulo: "Tu figurita mundialista esta lista",
        descripcion: "El resultado final ya esta preparado para mostrarse, compartirse o descargarse.",
    },
};

function escribirLog(titulo, datos) {
    const salida = typeof datos === "string" ? datos : JSON.stringify(datos, null, 2);
    console.info(`[Panini] ${titulo}`, salida);
}

function cargarEstado() {
    const bruto = localStorage.getItem(CLAVE_ESTADO) || localStorage.getItem(CLAVE_ESTADO_ANTERIOR);
    try {
        return { ...estadoInicial, ...(bruto ? JSON.parse(bruto) : {}) };
    } catch {
        return { ...estadoInicial };
    }
}

function guardarEstado() {
    localStorage.setItem(CLAVE_ESTADO, JSON.stringify(estado));
    localStorage.removeItem(CLAVE_ESTADO_ANTERIOR);
}

function detenerSondeos() {
    if (temporizadorRecorte) {
        clearTimeout(temporizadorRecorte);
        temporizadorRecorte = null;
    }
    if (temporizadorFigurita) {
        clearTimeout(temporizadorFigurita);
        temporizadorFigurita = null;
    }
}

function limpiarEstado() {
    detenerSondeos();
    Object.assign(estado, { ...estadoInicial });
    guardarEstado();
    mostrarMensaje("La experiencia se reinicio. Cargando nuevas preguntas...", "info");
    renderizarEstado();
    renderizarImagenes();
    renderizarPlaceholderPreguntas();
}

function mostrarMensaje(texto, tipo = "info") {
    if (!elementos.mensajeGlobal) {
        return;
    }
    if (temporizadorMensaje) {
        clearTimeout(temporizadorMensaje);
    }
    elementos.mensajeGlobal.hidden = false;
    elementos.mensajeGlobal.textContent = texto;
    elementos.mensajeGlobal.className = `mensaje-global mensaje-global--${tipo}`;
    temporizadorMensaje = window.setTimeout(() => {
        elementos.mensajeGlobal.hidden = true;
    }, 4200);
}

function cambiarActividad(activa, texto = "Encendiendo experiencia mundialista") {
    elementos.indicadorActividad.hidden = !activa;
    elementos.textoActividad.textContent = texto;
    elementos.body.classList.toggle("app-cargando", activa);
}

function renderizarPlaceholderPreguntas() {
    elementos.contenedorPreguntas.innerHTML = `
        <div class="estado-vacio">
            <span class="estado-vacio__halo"></span>
            <strong>Estamos preparando tu ficha</strong>
            <p class="texto-suave">En unos instantes vas a ver las preguntas directamente aca.</p>
        </div>
    `;
}

function marcarEstadoVisual(elemento, texto, estadoVisual) {
    if (!elemento) {
        return;
    }
    elemento.textContent = texto;
    elemento.dataset.estado = estadoVisual;
}

function marcarModulo(elemento, chip, resumen, detalle, estadoVisual, textoChip, textoDetalle) {
    if (elemento) {
        elemento.classList.remove("activo", "completado", "bloqueado");
        if (estadoVisual === "activo") {
            elemento.classList.add("activo");
        } else if (estadoVisual === "completado") {
            elemento.classList.add("completado");
        } else {
            elemento.classList.add("bloqueado");
        }
    }
    if (resumen) {
        resumen.classList.remove("activo", "completado", "bloqueado");
        resumen.classList.add(
            estadoVisual === "activo" ? "activo" : estadoVisual === "completado" ? "completado" : "bloqueado",
        );
    }
    if (chip) {
        chip.textContent = textoChip;
        chip.dataset.estado = estadoVisual;
    }
    if (detalle) {
        detalle.textContent = textoDetalle;
    }
}

function obtenerFaseActual() {
    if (!estado.tokenPublico) {
        return "sesion";
    }
    if (estado.figuritaId || estado.estadoFigurita === "completado") {
        return "completado";
    }
    if (estado.estadoRecorte === "procesando" || estado.estadoFigurita === "procesando") {
        return "procesando";
    }
    if (estado.resultadoId || estado.estadoRecorte === "completado") {
        return "figurita";
    }
    if (estado.puedeSubirFoto || estado.fotoId) {
        return "imagen";
    }
    return "trivia";
}

function actualizarResumenVisual() {
    const fase = obtenerFaseActual();
    const config = fases[fase];
    elementos.body.dataset.fase = fase;
    elementos.etapaActual.textContent = config.titulo;
    elementos.descripcionEtapa.textContent = config.descripcion;

    const porcentaje = Math.max(0, Math.min(100, Number(estado.progresoPorcentaje || 0)));
    elementos.valorProgreso.textContent = `${porcentaje}%`;
    elementos.barraProgreso.style.width = `${porcentaje}%`;
    const preguntas = `${estado.preguntasRespondidas || 0}/${estado.preguntasTotales || 0}`;
    const campos = `${estado.camposCompletos || 0}/${estado.camposTotales || 6}`;
    elementos.detalleProgreso.textContent = estado.tokenPublico
        ? `${preguntas} preguntas | ${campos} campos obligatorios`
        : "Preparando sesion";

    marcarModulo(
        elementos.moduloSesion,
        elementos.chipModuloSesion,
        elementos.resumenSesion,
        elementos.detalleModuloSesion,
        estado.tokenPublico ? "completado" : "activo",
        estado.tokenPublico ? "lista" : "iniciando",
        estado.tokenPublico ? "Sesion activa" : "Entrando a la experiencia",
    );
    marcarModulo(
        elementos.moduloTrivia,
        elementos.chipModuloTrivia,
        elementos.resumenTrivia,
        elementos.detalleModuloTrivia,
        estado.triviaCompletada ? "completado" : estado.tokenPublico ? "activo" : "bloqueado",
        estado.triviaCompletada ? "completa" : estado.tokenPublico ? "jugando" : "esperando",
        estado.triviaCompletada ? "Ficha lista" : "Responde la ficha",
    );
    marcarModulo(
        elementos.moduloImagen,
        elementos.chipModuloImagen,
        elementos.resumenImagen,
        elementos.detalleModuloImagen,
        estado.resultadoId || estado.estadoRecorte === "completado"
            ? "completado"
            : estado.puedeSubirFoto || estado.fotoId
                ? "activo"
                : "bloqueado",
        estado.resultadoId || estado.estadoRecorte === "completado"
            ? "recorte listo"
            : estado.puedeSubirFoto || estado.fotoId
                ? "desbloqueado"
                : "bloqueado",
        estado.resultadoId || estado.estadoRecorte === "completado"
            ? "Recorte listo"
            : estado.puedeSubirFoto || estado.fotoId
                ? "Sube y procesa tu foto"
                : "Se habilita al completar la ficha",
    );
    marcarModulo(
        elementos.moduloFigurita,
        elementos.chipModuloFigurita,
        elementos.resumenFigurita,
        elementos.detalleModuloFigurita,
        estado.figuritaId || estado.estadoFigurita === "completado"
            ? "completado"
            : estado.resultadoId || estado.estadoRecorte === "completado"
                ? "activo"
                : "bloqueado",
        estado.figuritaId || estado.estadoFigurita === "completado"
            ? "lista"
            : estado.resultadoId || estado.estadoRecorte === "completado"
                ? "disponible"
                : "en espera",
        estado.figuritaId || estado.estadoFigurita === "completado"
            ? "Figurita final lista"
            : estado.resultadoId || estado.estadoRecorte === "completado"
                ? "Genera tu figurita"
                : "Esperando recorte",
    );
}

function renderizarEstado() {
    marcarEstadoVisual(
        elementos.estadoTrivia,
        estado.triviaCompletada ? "Ficha completa" : estado.triviaId ? "Preguntas en curso" : "Preparando preguntas",
        estado.triviaCompletada ? "completado" : estado.triviaId ? "activo" : "pendiente",
    );
    marcarEstadoVisual(
        elementos.estadoSesion,
        estado.tokenPublico ? "Experiencia activa" : "Iniciando experiencia",
        estado.tokenPublico ? (estado.estadoSesion === "error" ? "error" : "activo") : "pendiente",
    );
    marcarEstadoVisual(
        elementos.estadoFoto,
        estado.fotoId ? "Foto cargada" : "Sin foto",
        estado.fotoId ? (estado.estadoFoto || "activo") : "pendiente",
    );
    marcarEstadoVisual(
        elementos.estadoRecorte,
        estado.resultadoId ? "Recorte generado" : "Sin recorte",
        estado.resultadoId ? (estado.estadoRecorte || "activo") : "pendiente",
    );
    marcarEstadoVisual(
        elementos.estadoFigurita,
        estado.figuritaId ? "Figurita creada" : "Sin figurita",
        estado.figuritaId ? (estado.estadoFigurita || "activo") : "pendiente",
    );
    actualizarResumenVisual();
}

function pintarMarco(marco, url) {
    if (!marco) {
        return;
    }
    marco.dataset.vacio = url ? "false" : "true";
}

function renderizarImagenes() {
    elementos.vistaOriginal.src = estado.fotoOriginalUrl || "";
    elementos.vistaRecorte.src = estado.recorteUrl || "";
    elementos.vistaFigurita.src = estado.figuritaUrl || "";
    pintarMarco(elementos.marcoOriginal, estado.fotoOriginalUrl);
    pintarMarco(elementos.marcoRecorte, estado.recorteUrl);
    pintarMarco(elementos.marcoFigurita, estado.figuritaUrl);
}

function aplicarResumenSesion(resumen) {
    if (!resumen) {
        return;
    }
    estado.tokenPublico = resumen.token_publico || estado.tokenPublico;
    estado.triviaId = resumen.trivia_id || estado.triviaId;
    estado.estadoSesion = resumen.estado || estado.estadoSesion;
    estado.triviaCompletada = Boolean(resumen.trivia_completada);
    estado.puedeSubirFoto = Boolean(resumen.puede_subir_foto);
    estado.preguntasRespondidas = resumen.progreso?.preguntas_respondidas ?? estado.preguntasRespondidas;
    estado.preguntasTotales = resumen.progreso?.preguntas_totales ?? estado.preguntasTotales;
    estado.camposCompletos = resumen.progreso?.campos_obligatorios_completos ?? estado.camposCompletos;
    estado.camposTotales = resumen.progreso?.campos_obligatorios_totales ?? estado.camposTotales;
    estado.progresoPorcentaje = resumen.progreso?.porcentaje ?? estado.progresoPorcentaje;
    if (resumen.ultima_foto?.id) {
        estado.fotoId = resumen.ultima_foto.id;
        estado.estadoFoto = resumen.ultima_foto.estado || estado.estadoFoto;
        estado.fotoOriginalUrl = resumen.ultima_foto.archivo_url || estado.fotoOriginalUrl;
    }
    if (resumen.ultimo_recorte?.id) {
        estado.resultadoId = resumen.ultimo_recorte.id;
        estado.estadoRecorte = resumen.ultimo_recorte.estado || estado.estadoRecorte;
    }
    if (resumen.ultima_figurita?.id) {
        estado.figuritaId = resumen.ultima_figurita.id;
        estado.estadoFigurita = resumen.ultima_figurita.estado || estado.estadoFigurita;
    }
}

function aplicarResultadoRecorte(resultado) {
    if (!resultado) {
        return;
    }
    estado.resultadoId = resultado.id || estado.resultadoId;
    estado.estadoRecorte = resultado.estado || estado.estadoRecorte;
    estado.recorteUrl = resultado.png_transparente_url || estado.recorteUrl;
}

function aplicarResultadoFigurita(figurita) {
    if (!figurita) {
        return;
    }
    estado.figuritaId = figurita.id || estado.figuritaId;
    estado.estadoFigurita = figurita.estado || estado.estadoFigurita;
    estado.figuritaUrl = figurita.imagen_final_url || estado.figuritaUrl;
}

async function solicitar(ruta, { method = "GET", body, headers = {} } = {}) {
    const config = { method, headers: { ...headers } };

    if (body instanceof FormData) {
        config.body = body;
    } else if (body !== undefined) {
        config.headers["Content-Type"] = "application/json";
        config.body = JSON.stringify(body);
    }

    const respuesta = await fetch(ruta, config);
    const texto = await respuesta.text();
    let datos = {};

    try {
        datos = texto ? JSON.parse(texto) : {};
    } catch {
        datos = { bruto: texto };
    }

    if (!respuesta.ok) {
        const mensaje = datos?.error?.mensaje || `Error HTTP ${respuesta.status}`;
        throw new Error(mensaje);
    }

    return datos;
}

async function cargarEquipos() {
    cacheEquipos = await solicitar("/api/catalogos/equipos/");
}

function renderizarCampoPregunta(pregunta, indice) {
    const actual = pregunta.respuesta_actual || {};
    const ayuda = pregunta.ayuda || "Completa este paso para avanzar.";

    if (pregunta.tipo_respuesta === "select_busqueda") {
        const opciones = cacheEquipos
            .map(
                (equipo) => `
                    <option value="${equipo.id}" ${String(actual.equipo_id || "") === String(equipo.id) ? "selected" : ""}>
                        ${equipo.nombre}
                    </option>
                `,
            )
            .join("");

        return `
            <div class="pregunta" data-codigo="${pregunta.codigo}">
                <div class="pregunta__encabezado">
                    <span class="pregunta__indice">Paso ${indice}</span>
                    <p class="pregunta__codigo">${pregunta.codigo}</p>
                    <h3 class="pregunta__titulo">${pregunta.texto}</h3>
                    <p class="pregunta__ayuda">${ayuda}</p>
                </div>
                <label class="campo campo--respuesta">
                    <span class="campo__label">Selecciona un equipo</span>
                    <select data-tipo="equipo" data-pregunta-id="${pregunta.id}">
                        <option value="">Selecciona un equipo</option>
                        ${opciones}
                    </select>
                </label>
            </div>
        `;
    }

    const tipoInput = pregunta.tipo_respuesta === "fecha"
        ? "date"
        : pregunta.tipo_respuesta === "numero"
            ? "number"
            : "text";
    const valor = actual.valor ?? "";

    return `
        <div class="pregunta" data-codigo="${pregunta.codigo}">
            <div class="pregunta__encabezado">
                <span class="pregunta__indice">Paso ${indice}</span>
                <p class="pregunta__codigo">${pregunta.codigo}</p>
                <h3 class="pregunta__titulo">${pregunta.texto}</h3>
                <p class="pregunta__ayuda">${ayuda}</p>
            </div>
            <label class="campo campo--respuesta">
                <span class="campo__label">${pregunta.placeholder || "Tu respuesta"}</span>
                <input
                    data-tipo="${pregunta.tipo_respuesta}"
                    data-pregunta-id="${pregunta.id}"
                    type="${tipoInput}"
                    placeholder="${pregunta.placeholder || ""}"
                    value="${valor}"
                >
            </label>
        </div>
    `;
}

function renderizarCabeceraPreguntas(totalPreguntas) {
    const completadas = estado.preguntasRespondidas || 0;
    return `
        <div class="intro-trivia">
            <span class="intro-trivia__paso">Paso ${Math.min(completadas + 1, totalPreguntas)} de ${totalPreguntas}</span>
            <h3 class="intro-trivia__titulo">Completa la ficha titular</h3>
            <p class="intro-trivia__texto">
                Responde cada bloque para desbloquear la foto oficial y la figurita final.
            </p>
        </div>
    `;
}

async function renderizarTrivia(trivia, preguntas = []) {
    estado.triviaId = trivia.id;
    estado.triviaNombre = trivia.nombre || estado.triviaNombre;
    await cargarEquipos();
    guardarEstado();
    renderizarEstado();

    if (!preguntas.length) {
        elementos.contenedorPreguntas.innerHTML = `
            <div class="estado-vacio">
                <span class="estado-vacio__halo"></span>
                <strong>No hay preguntas activas</strong>
                <p class="texto-suave">Activa preguntas en admin para mostrar el flujo guiado.</p>
            </div>
        `;
        return;
    }

    elementos.contenedorPreguntas.innerHTML = `
        ${renderizarCabeceraPreguntas(preguntas.length)}
        ${preguntas.map((pregunta, indice) => renderizarCampoPregunta(pregunta, indice + 1)).join("")}
    `;
}

function construirPayloadTrivia() {
    const respuestas = [];
    const campos = elementos.contenedorPreguntas.querySelectorAll("[data-pregunta-id]");

    for (const campo of campos) {
        const preguntaId = campo.dataset.preguntaId;
        const tipo = campo.dataset.tipo;

        if (tipo === "equipo") {
            if (!campo.value) {
                throw new Error("Debes seleccionar un equipo antes de continuar.");
            }
            respuestas.push({ pregunta_id: preguntaId, equipo_id: campo.value });
            continue;
        }

        if (!campo.value) {
            throw new Error("Debes completar todas las preguntas antes de continuar.");
        }

        respuestas.push({
            pregunta_id: preguntaId,
            valor: tipo === "numero" ? Number(campo.value) : campo.value,
        });
    }

    return respuestas;
}

async function iniciarOReanudarSesion(forzarNueva = false) {
    const token = forzarNueva ? "" : estado.tokenPublico;

    try {
        const datos = await solicitar("/api/sesiones/iniciar/", {
            method: "POST",
            body: token ? { token_publico: token } : {},
        });
        aplicarResumenSesion(datos.sesion);
        guardarEstado();
        renderizarEstado();
        return datos;
    } catch (error) {
        if (token) {
            Object.assign(estado, { ...estadoInicial });
            guardarEstado();
            return iniciarOReanudarSesion(true);
        }
        throw error;
    }
}

async function recargarPreguntas() {
    if (!estado.tokenPublico) {
        throw new Error("No pudimos crear la sesion de la experiencia.");
    }

    const datos = await solicitar(`/api/sesiones/${estado.tokenPublico}/preguntas/`);
    estado.triviaId = datos.trivia.id;
    estado.triviaNombre = datos.trivia.nombre;
    guardarEstado();
    await renderizarTrivia(
        { id: datos.trivia.id, nombre: datos.trivia.nombre, descripcion: datos.trivia.descripcion },
        datos.preguntas,
    );
}

async function sincronizarSesion() {
    if (!estado.tokenPublico) {
        return;
    }
    const datos = await solicitar(`/api/sesiones/${estado.tokenPublico}/estado/`);
    aplicarResumenSesion(datos);
    guardarEstado();
    renderizarEstado();
    renderizarImagenes();
}

function desplazarA(elemento) {
    if (!elemento) {
        return;
    }
    elemento.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function responderTrivia(evento) {
    evento.preventDefault();
    if (!estado.tokenPublico) {
        throw new Error("No hay una sesion activa.");
    }

    const respuestas = construirPayloadTrivia();
    const datos = await solicitar(`/api/sesiones/${estado.tokenPublico}/responder/`, {
        method: "POST",
        body: { respuestas },
    });

    aplicarResumenSesion(datos.sesion);
    guardarEstado();
    renderizarEstado();

    if (estado.triviaCompletada) {
        mostrarMensaje("Ficha completada. Ya puedes subir la foto oficial.", "exito");
        desplazarA(elementos.moduloImagen);
    } else {
        mostrarMensaje("Guardamos tus respuestas.", "info");
    }
}

async function subirImagen(evento) {
    evento.preventDefault();
    if (!estado.tokenPublico) {
        throw new Error("No hay una sesion activa.");
    }

    const archivo = elementos.inputArchivo.files[0];
    if (!archivo) {
        throw new Error("Selecciona una imagen antes de subir.");
    }

    const formData = new FormData();
    formData.append("archivo", archivo);

    const datos = await solicitar(`/api/sesiones/${estado.tokenPublico}/imagenes/subir/`, {
        method: "POST",
        body: formData,
    });

    estado.fotoId = datos.foto.id;
    estado.estadoFoto = datos.foto.estado || "completado";
    estado.fotoOriginalUrl = URL.createObjectURL(archivo);
    guardarEstado();
    renderizarEstado();
    renderizarImagenes();
    mostrarMensaje("Foto subida correctamente. Ahora puedes procesarla.", "exito");
}

async function consultarResultadoImagen({ silencioso = false } = {}) {
    if (!estado.fotoId) {
        return null;
    }

    const datos = await solicitar(`/api/imagenes/${estado.fotoId}/resultado/`);
    aplicarResultadoRecorte(datos);
    guardarEstado();
    renderizarEstado();
    renderizarImagenes();

    if (!silencioso && datos.estado === "completado") {
        mostrarMensaje("Recorte listo. Ya puedes generar tu figurita.", "exito");
    }

    return datos;
}

async function sondearRecorte(intentos = 0) {
    if (!estado.fotoId || intentos > 30) {
        return;
    }

    try {
        const datos = await consultarResultadoImagen({ silencioso: true });
        if (datos?.estado === "pendiente" || datos?.estado === "procesando") {
            temporizadorRecorte = window.setTimeout(() => sondearRecorte(intentos + 1), 2500);
            return;
        }
        if (datos?.estado === "completado") {
            mostrarMensaje("Recorte finalizado. Sigue con la figurita.", "exito");
            desplazarA(elementos.moduloFigurita);
            return;
        }
        if (datos?.estado === "error") {
            mostrarMensaje("El recorte no pudo completarse. Intenta procesar de nuevo.", "error");
        }
    } catch (error) {
        escribirLog("Sondeo de recorte", error.message || String(error));
    }
}

async function procesarImagen(evento) {
    evento.preventDefault();
    if (!estado.fotoId || !estado.tokenPublico) {
        throw new Error("Primero sube una imagen.");
    }

    const formData = new FormData(evento.currentTarget);
    const plantillaId = String(formData.get("plantilla_id") || "").trim();
    const body = { token_publico: estado.tokenPublico };
    if (plantillaId) {
        body.plantilla_id = plantillaId;
    }

    const datos = await solicitar(`/api/imagenes/${estado.fotoId}/procesar/`, {
        method: "POST",
        body,
    });

    aplicarResultadoRecorte(datos.resultado);
    guardarEstado();
    renderizarEstado();
    renderizarImagenes();

    if (estado.estadoRecorte === "completado") {
        mostrarMensaje("Recorte completado. Ya puedes generar la figurita.", "exito");
        desplazarA(elementos.moduloFigurita);
        return;
    }

    mostrarMensaje("Procesando imagen. Te avisamos cuando el recorte este listo.", "info");
    sondearRecorte();
}

async function consultarFigurita({ silencioso = false } = {}) {
    if (!estado.figuritaId) {
        return null;
    }

    const datos = await solicitar(`/api/figuritas/${estado.figuritaId}/`);
    aplicarResultadoFigurita(datos);
    guardarEstado();
    renderizarEstado();
    renderizarImagenes();

    if (!silencioso && datos.estado === "completado") {
        mostrarMensaje("Figurita lista.", "exito");
    }

    return datos;
}

async function sondearFigurita(intentos = 0) {
    if (!estado.figuritaId || intentos > 30) {
        return;
    }

    try {
        const datos = await consultarFigurita({ silencioso: true });
        if (datos?.estado === "pendiente" || datos?.estado === "procesando") {
            temporizadorFigurita = window.setTimeout(() => sondearFigurita(intentos + 1), 2500);
            return;
        }
        if (datos?.estado === "completado") {
            mostrarMensaje("Tu figurita mundialista ya esta lista.", "exito");
            return;
        }
        if (datos?.estado === "error") {
            mostrarMensaje("No pudimos completar la figurita. Intenta generarla de nuevo.", "error");
        }
    } catch (error) {
        escribirLog("Sondeo de figurita", error.message || String(error));
    }
}

async function generarFigurita(evento) {
    evento.preventDefault();
    if (!estado.tokenPublico) {
        throw new Error("No hay una sesion activa.");
    }

    const formData = new FormData(evento.currentTarget);
    const plantillaId = String(formData.get("plantilla_id") || "").trim();
    const body = {};

    if (estado.resultadoId) {
        body.resultado_recorte_id = estado.resultadoId;
    }
    if (plantillaId) {
        body.plantilla_id = plantillaId;
    }

    const datos = await solicitar(`/api/sesiones/${estado.tokenPublico}/figuritas/generar/`, {
        method: "POST",
        body,
    });

    aplicarResultadoFigurita(datos.figurita);
    guardarEstado();
    renderizarEstado();
    renderizarImagenes();

    if (estado.estadoFigurita === "completado") {
        mostrarMensaje("Tu figurita mundialista ya esta lista.", "exito");
        return;
    }

    mostrarMensaje("Generando figurita. Te avisamos apenas quede lista.", "info");
    sondearFigurita();
}

async function ejecutarSegura(titulo, accion, actividad) {
    try {
        cambiarActividad(true, actividad || titulo);
        await accion();
    } catch (error) {
        escribirLog(`Error en ${titulo}`, error.message || String(error));
        mostrarMensaje(error.message || "Ocurrio un error inesperado.", "error");
    } finally {
        cambiarActividad(false);
    }
}

async function inicializarExperiencia() {
    renderizarPlaceholderPreguntas();
    const habiaToken = Boolean(estado.tokenPublico);
    await iniciarOReanudarSesion();
    await recargarPreguntas();
    await sincronizarSesion();

    if (!habiaToken) {
        mostrarMensaje("Ya puedes empezar a responder las preguntas.", "info");
    }

    if (estado.estadoRecorte === "procesando") {
        sondearRecorte();
    }
    if (estado.estadoFigurita === "procesando") {
        sondearFigurita();
    }
}

function registrarEvento(elemento, evento, callback) {
    if (elemento) {
        elemento.addEventListener(evento, callback);
    }
}

registrarEvento(elementos.botonReiniciar, "click", () => {
    limpiarEstado();
    ejecutarSegura("reiniciar experiencia", () => inicializarExperiencia(), "Reiniciando experiencia");
});

registrarEvento(elementos.inputArchivo, "change", () => {
    const archivo = elementos.inputArchivo.files[0];
    if (!archivo) {
        return;
    }
    estado.fotoOriginalUrl = URL.createObjectURL(archivo);
    renderizarImagenes();
});

registrarEvento(elementos.formularioTrivia, "submit", (evento) => {
    ejecutarSegura("guardar preguntas", () => responderTrivia(evento), "Guardando respuestas");
});

registrarEvento(elementos.formularioSubida, "submit", (evento) => {
    ejecutarSegura("subir foto", () => subirImagen(evento), "Subiendo foto oficial");
});

registrarEvento(elementos.formularioProcesar, "submit", (evento) => {
    ejecutarSegura("procesar imagen", () => procesarImagen(evento), "Gemini esta recortando la silueta");
});

registrarEvento(elementos.formularioFigurita, "submit", (evento) => {
    ejecutarSegura("generar figurita", () => generarFigurita(evento), "Renderizando figurita final");
});

renderizarEstado();
renderizarImagenes();
ejecutarSegura("inicializar experiencia", () => inicializarExperiencia(), "Preparando experiencia");
