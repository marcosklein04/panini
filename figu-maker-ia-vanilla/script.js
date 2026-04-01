const API_BASE_URL = resolverApiBaseUrl();
const CLAVE_STORAGE = "figu-maker-ia-vanilla-backend";
const MAPA_CODIGOS_BACKEND = {
    nombre: "nombre",
    apellido: "apellido",
    fechaNacimiento: "fecha_nacimiento",
    altura: "altura_cm",
    peso: "peso_kg",
    equipo: "equipo",
};

const PASOS_CUESTIONARIO = [
    { id: "nombre", codigo: "NOMBRE", etiqueta: "Cual es tu nombre?", placeholder: "Ej: Lionel", tipo: "texto", ayuda: "Tu nombre va en la figurita final con presencia de portada." },
    { id: "apellido", codigo: "APELLIDO", etiqueta: "Y tu apellido?", placeholder: "Ej: Messi", tipo: "texto", ayuda: "Lo usamos como apellido protagonista en el header de la carta." },
    { id: "fechaNacimiento", codigo: "FECHA", etiqueta: "Cuando naciste?", placeholder: "", tipo: "fecha", ayuda: "La fecha aparece en la franja de estadisticas de la figurita." },
    { id: "altura", codigo: "ALTURA", etiqueta: "Cuanto medis? (cm)", placeholder: "Ej: 178", tipo: "numero", ayuda: "Altura en centimetros, como en una ficha de jugador profesional." },
    { id: "peso", codigo: "PESO", etiqueta: "Cuanto pesas? (kg)", placeholder: "Ej: 72", tipo: "numero", ayuda: "Peso en kilogramos para completar la linea de datos." },
    { id: "equipo", codigo: "EQUIPO", etiqueta: "De que equipo sos?", placeholder: "Elegi tu equipo", tipo: "opcion", ayuda: "Selecciona el club que quieres mostrar en la franja inferior.", opciones: ["Boca Juniors", "River Plate"] },
];

const PASOS_PROCESAMIENTO = [
    { titulo: "Subiendo tu foto", detalle: "Guardando la imagen original en el backend." },
    { titulo: "Gemini analizando la silueta", detalle: "Detectando persona y guiando el recorte." },
    { titulo: "Refinando bordes", detalle: "Generando el PNG transparente final." },
    { titulo: "Componiendo la figurita", detalle: "Pegando el recorte en la plantilla premium." },
    { titulo: "Cerrando el resultado", detalle: "Preparando la imagen final para mostrarla." },
];

const ESTADO_BASE = {
    pantalla: "inicio",
    pasoActual: 0,
    respuestas: {
        nombre: "",
        apellido: "",
        fechaNacimiento: "",
        altura: "",
        peso: "",
        equipo: "",
    },
    tokenPublico: "",
    preguntasBackend: [],
    equipos: [],
    fotoDataUrl: "",
    fotoId: "",
    resultadoId: "",
    recorteUrl: "",
    figuritaId: "",
    figuritaUrl: "",
};

const estado = restaurarEstado();
const referencias = {};
let archivoActual = null;
let accionEnCurso = false;
let backendInicializado = false;

document.addEventListener("DOMContentLoaded", () => {
    cachearReferencias();
    insertarDefinicionGradiente();
    crearParticulas();
    enlazarEventos();
    renderizarResumen();
    renderizarCuestionario();
    renderizarFoto();
    mostrarPantalla(estado.pantalla);
    void arrancarBackend();
});

function resolverApiBaseUrl() {
    if (!window.location.hostname) {
        return "http://127.0.0.1:8000";
    }
    if (window.location.port === "8000") {
        return window.location.origin;
    }
    return `${window.location.protocol}//${window.location.hostname}:8000`;
}

function cachearReferencias() {
    referencias.pantallas = {
        inicio: document.getElementById("pantalla-inicio"),
        cuestionario: document.getElementById("pantalla-cuestionario"),
        foto: document.getElementById("pantalla-foto"),
        procesando: document.getElementById("pantalla-procesando"),
        resultado: document.getElementById("pantalla-resultado"),
    };
    referencias.etiquetaPantalla = document.getElementById("etiqueta-pantalla");
    referencias.listaResumen = document.getElementById("lista-resumen");
    referencias.textoProgreso = document.getElementById("texto-progreso");
    referencias.porcentajeProgreso = document.getElementById("porcentaje-progreso");
    referencias.rellenoProgreso = document.getElementById("relleno-progreso");
    referencias.codigoPregunta = document.getElementById("codigo-pregunta");
    referencias.tituloPregunta = document.getElementById("titulo-pregunta");
    referencias.ayudaPregunta = document.getElementById("ayuda-pregunta");
    referencias.campoPregunta = document.getElementById("campo-pregunta");
    referencias.errorPregunta = document.getElementById("error-pregunta");
    referencias.btnAnterior = document.getElementById("btn-anterior");
    referencias.btnSiguiente = document.getElementById("btn-siguiente");
    referencias.btnEmpezar = document.getElementById("btn-empezar");
    referencias.btnIrPlantilla = document.getElementById("btn-ir-plantilla");
    referencias.videoCamara = document.getElementById("video-camara");
    referencias.previewFoto = document.getElementById("preview-foto");
    referencias.placeholderFoto = document.getElementById("placeholder-foto");
    referencias.inputArchivo = document.getElementById("input-archivo");
    referencias.errorFoto = document.getElementById("error-foto");
    referencias.btnAbrirCamara = document.getElementById("btn-abrir-camara");
    referencias.btnSacarFoto = document.getElementById("btn-sacar-foto");
    referencias.btnSubirArchivo = document.getElementById("btn-subir-archivo");
    referencias.btnRepetirFoto = document.getElementById("btn-repetir-foto");
    referencias.btnConfirmarFoto = document.getElementById("btn-confirmar-foto");
    referencias.btnVolverQuiz = document.getElementById("btn-volver-quiz");
    referencias.listaProcesos = document.getElementById("lista-procesos");
    referencias.circuloProgreso = document.getElementById("circulo-progreso");
    referencias.valorProgreso = document.getElementById("valor-progreso");
    referencias.tituloProcesando = document.getElementById("titulo-procesando");
    referencias.textoProcesando = document.getElementById("texto-procesando");
    referencias.previewProcesandoFoto = document.getElementById("preview-procesando-foto");
    referencias.resultadoFigura = document.getElementById("resultado-figura");
    referencias.imagenFiguritaFinal = document.getElementById("imagen-figurita-final");
    referencias.listaDatosFinales = document.getElementById("lista-datos-finales");
    referencias.btnDescargar = document.getElementById("btn-descargar");
    referencias.btnCompartir = document.getElementById("btn-compartir");
    referencias.btnReiniciar = document.getElementById("btn-reiniciar");
    referencias.toast = document.getElementById("toast");
}

function insertarDefinicionGradiente() {
    const svg = document.querySelector(".anillo-progreso__svg");
    if (!svg) {
        return;
    }
    const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    const gradient = document.createElementNS("http://www.w3.org/2000/svg", "linearGradient");
    gradient.id = "gradiente-progreso";
    gradient.setAttribute("x1", "0%");
    gradient.setAttribute("y1", "0%");
    gradient.setAttribute("x2", "100%");
    gradient.setAttribute("y2", "100%");
    [
        { offset: "0%", color: "#ff4d5e" },
        { offset: "50%", color: "#458cff" },
        { offset: "100%", color: "#20ca7b" },
    ].forEach((item) => {
        const stop = document.createElementNS("http://www.w3.org/2000/svg", "stop");
        stop.setAttribute("offset", item.offset);
        stop.setAttribute("stop-color", item.color);
        gradient.appendChild(stop);
    });
    defs.appendChild(gradient);
    svg.insertBefore(defs, svg.firstChild);
}

function crearParticulas() {
    const contenedor = document.getElementById("particulas");
    if (!contenedor) {
        return;
    }
    contenedor.innerHTML = "";
    for (let i = 0; i < 16; i += 1) {
        const particula = document.createElement("span");
        particula.className = "particula";
        particula.style.left = `${Math.random() * 100}%`;
        particula.style.animationDuration = `${8 + Math.random() * 10}s`;
        particula.style.animationDelay = `${Math.random() * 10}s`;
        particula.style.opacity = `${0.25 + Math.random() * 0.6}`;
        contenedor.appendChild(particula);
    }
}

function enlazarEventos() {
    referencias.btnEmpezar.addEventListener("click", () => mostrarPantalla("cuestionario"));
    referencias.btnIrPlantilla.addEventListener("click", () => {
        document.querySelector(".figurita-showcase")?.scrollIntoView({ behavior: "smooth", block: "center" });
    });
    referencias.btnAnterior.addEventListener("click", () => {
        if (estado.pasoActual === 0) {
            mostrarPantalla("inicio");
            return;
        }
        ocultarErrorPregunta();
        estado.pasoActual -= 1;
        persistirEstado();
        renderizarCuestionario();
    });
    referencias.btnSiguiente.addEventListener("click", () => {
        void ejecutarAccion("Guardando respuesta", avanzarCuestionario);
    });
    referencias.btnAbrirCamara.addEventListener("click", () => {
        void ejecutarAccion("Abriendo camara", abrirCamara);
    });
    referencias.btnSacarFoto.addEventListener("click", tomarFoto);
    referencias.btnSubirArchivo.addEventListener("click", () => referencias.inputArchivo.click());
    referencias.inputArchivo.addEventListener("change", manejarArchivoSeleccionado);
    referencias.btnRepetirFoto.addEventListener("click", limpiarFoto);
    referencias.btnConfirmarFoto.addEventListener("click", () => {
        void ejecutarAccion("Procesando tu foto con Gemini", confirmarFoto);
    });
    referencias.btnVolverQuiz.addEventListener("click", () => {
        cerrarCamara();
        mostrarPantalla("cuestionario");
    });
    referencias.btnDescargar.addEventListener("click", () => {
        void ejecutarAccion("Descargando figurita", descargarFigurita);
    });
    referencias.btnCompartir.addEventListener("click", () => {
        void ejecutarAccion("Compartiendo figurita", compartirFigurita);
    });
    referencias.btnReiniciar.addEventListener("click", reiniciarAplicacion);
    window.addEventListener("beforeunload", cerrarCamara);
}

async function arrancarBackend() {
    try {
        await iniciarSesionBackend();
        await cargarEquiposBackend();
        await cargarPreguntasBackend();
        await sincronizarEstadoBackend();
        backendInicializado = true;
        renderizarCuestionario();
        renderizarFoto();
        renderizarResultado();
        if (estado.pantalla === "procesando" && estado.fotoId) {
            void ejecutarAccion("Retomando proceso pendiente", reanudarProcesamiento);
        }
    } catch (error) {
        backendInicializado = false;
        estado.tokenPublico = "";
        estado.preguntasBackend = [];
        persistirEstado();
        mostrarToast(error.message || "No pudimos conectar con el backend.");
    }
}

async function ejecutarAccion(texto, accion) {
    if (accionEnCurso) {
        return;
    }
    accionEnCurso = true;
    mostrarToast(texto);
    try {
        await accion();
    } catch (error) {
        mostrarToast(error.message || "Ocurrio un error inesperado.");
    } finally {
        accionEnCurso = false;
    }
}

function restaurarEstado() {
    const bruto = sessionStorage.getItem(CLAVE_STORAGE);
    if (!bruto) {
        return { ...ESTADO_BASE };
    }
    try {
        const data = JSON.parse(bruto);
        return {
            ...ESTADO_BASE,
            ...data,
            respuestas: { ...ESTADO_BASE.respuestas, ...(data.respuestas || {}) },
        };
    } catch (_error) {
        return { ...ESTADO_BASE };
    }
}

function persistirEstado() {
    sessionStorage.setItem(
        CLAVE_STORAGE,
        JSON.stringify({
            pantalla: estado.pantalla,
            pasoActual: estado.pasoActual,
            respuestas: estado.respuestas,
            tokenPublico: estado.tokenPublico,
            preguntasBackend: estado.preguntasBackend,
            equipos: estado.equipos,
            fotoDataUrl: estado.fotoDataUrl,
            fotoId: estado.fotoId,
            resultadoId: estado.resultadoId,
            recorteUrl: estado.recorteUrl,
            figuritaId: estado.figuritaId,
            figuritaUrl: estado.figuritaUrl,
        }),
    );
}

function mostrarPantalla(nombre) {
    Object.entries(referencias.pantallas).forEach(([clave, nodo]) => {
        nodo.hidden = clave !== nombre;
    });
    estado.pantalla = nombre;
    referencias.etiquetaPantalla.textContent = nombre.charAt(0).toUpperCase() + nombre.slice(1);
    if (nombre === "cuestionario") {
        renderizarCuestionario();
    }
    if (nombre === "foto") {
        renderizarFoto();
    }
    if (nombre === "procesando") {
        renderizarProcesamiento();
    }
    if (nombre === "resultado") {
        renderizarResultado();
    }
    persistirEstado();
}

function renderizarResumen() {
    referencias.listaResumen.innerHTML = "";
    PASOS_CUESTIONARIO.forEach((paso, indice) => {
        const item = document.createElement("li");
        item.className = "resumen-item";
        if (estado.respuestas[paso.id]) {
            item.classList.add("resumen-item--completo");
        }
        item.innerHTML = `
            <strong>${paso.codigo}<span>Paso ${indice + 1}</span></strong>
            <p>${formatearValorRespuesta(paso.id, estado.respuestas[paso.id]) || "Pendiente"}</p>
        `;
        referencias.listaResumen.appendChild(item);
    });
}

function renderizarCuestionario() {
    const paso = PASOS_CUESTIONARIO[estado.pasoActual];
    if (!paso) {
        return;
    }
    const progreso = Math.round((estado.pasoActual / PASOS_CUESTIONARIO.length) * 100);
    referencias.textoProgreso.textContent = `Paso ${estado.pasoActual + 1} de ${PASOS_CUESTIONARIO.length}`;
    referencias.porcentajeProgreso.textContent = `${progreso}%`;
    referencias.rellenoProgreso.style.width = `${progreso}%`;
    referencias.codigoPregunta.textContent = paso.codigo;
    referencias.tituloPregunta.textContent = paso.etiqueta;
    referencias.ayudaPregunta.textContent = paso.ayuda;
    referencias.campoPregunta.innerHTML = "";
    ocultarErrorPregunta();

    if (paso.tipo === "opcion") {
        renderizarCampoOpciones(paso);
    } else {
        renderizarCampoTexto(paso);
    }

    referencias.btnAnterior.querySelector("span").textContent = estado.pasoActual === 0 ? "Volver" : "Atras";
    referencias.btnSiguiente.querySelector("span").textContent =
        estado.pasoActual === PASOS_CUESTIONARIO.length - 1 ? "Ir a la foto" : "Siguiente";
    referencias.btnSiguiente.disabled = !estado.respuestas[paso.id];
    renderizarResumen();
}

function renderizarCampoTexto(paso) {
    referencias.campoPregunta.innerHTML = `
        <div class="campo-pregunta__stack">
            <input class="campo-control" id="input-paso" type="${paso.tipo === "fecha" ? "date" : paso.tipo === "numero" ? "number" : "text"}" placeholder="${paso.placeholder || ""}" value="${estado.respuestas[paso.id] || ""}">
            <p class="campo-ayuda">${paso.tipo === "fecha"
                ? "Usa una fecha real. El backend valida una edad razonable."
                : paso.tipo === "numero"
                    ? "El valor tiene que pasar validaciones coherentes para una ficha deportiva."
                    : "Escribe el dato como quieres que aparezca en tu figurita."}</p>
        </div>
    `;
    const input = document.getElementById("input-paso");
    const sincronizarInput = (evento) => {
        actualizarRespuestaPaso(paso.id, evento.target.value);
    };
    input.addEventListener("input", sincronizarInput);
    input.addEventListener("change", sincronizarInput);
    input.addEventListener("blur", sincronizarInput);
    input.addEventListener("keydown", (evento) => {
        if (evento.key === "Enter" && !referencias.btnSiguiente.disabled) {
            void ejecutarAccion("Guardando respuesta", avanzarCuestionario);
        }
    });
    input.focus();
}

function renderizarCampoOpciones(paso) {
    const stack = document.createElement("div");
    stack.className = "campo-pregunta__stack";
    const grid = document.createElement("div");
    grid.className = "opciones-grid";

    (paso.opciones || []).forEach((opcion) => {
        const boton = document.createElement("button");
        boton.type = "button";
        boton.className = "opcion-equipo";
        if (estado.respuestas[paso.id] === opcion) {
            boton.classList.add("opcion-equipo--activa");
        }
        boton.textContent = opcion;
        boton.addEventListener("click", () => {
            actualizarRespuestaPaso(paso.id, opcion);
            renderizarCampoOpciones(paso);
        });
        grid.appendChild(boton);
    });

    const ayuda = document.createElement("p");
    ayuda.className = "campo-ayuda";
    ayuda.textContent = "La lista viene del backend y se sincroniza con la sesion anonima.";
    stack.appendChild(grid);
    stack.appendChild(ayuda);
    referencias.campoPregunta.innerHTML = "";
    referencias.campoPregunta.appendChild(stack);
    referencias.btnSiguiente.disabled = !estado.respuestas[paso.id];
}

async function avanzarCuestionario() {
    exigirBackendListo();
    const paso = PASOS_CUESTIONARIO[estado.pasoActual];
    sincronizarValorVisibleDelPaso(paso);
    const validacion = validarPaso(paso, estado.respuestas[paso.id]);
    if (!validacion.valido) {
        mostrarErrorPregunta(validacion.mensaje);
        return;
    }
    await sincronizarPasoConBackend(paso);
    ocultarErrorPregunta();

    if (estado.pasoActual === PASOS_CUESTIONARIO.length - 1) {
        mostrarPantalla("foto");
        mostrarToast("Ficha completada. Ahora vamos con la foto y el recorte de Gemini.");
        void sincronizarEstadoBackend().catch((error) => {
            mostrarToast(error.message || "No pudimos refrescar el estado de la sesion.");
        });
        return;
    }

    estado.pasoActual += 1;
    persistirEstado();
    renderizarCuestionario();
}

function validarPaso(paso, valorBruto) {
    const valor = (valorBruto || "").toString().trim();
    if (!valor) {
        return { valido: false, mensaje: "Completa este dato para seguir." };
    }
    if ((paso.id === "nombre" || paso.id === "apellido") && (valor.length < 2 || valor.length > 32)) {
        return { valido: false, mensaje: "Este dato debe tener entre 2 y 32 caracteres." };
    }
    if (paso.id === "fechaNacimiento") {
        const fecha = new Date(valor);
        if (Number.isNaN(fecha.getTime())) {
            return { valido: false, mensaje: "Ingresa una fecha valida." };
        }
    }
    if (paso.id === "altura") {
        const numero = Number(valor);
        if (!Number.isFinite(numero) || numero < 80 || numero > 250) {
            return { valido: false, mensaje: "La altura debe estar entre 80 y 250 cm." };
        }
    }
    if (paso.id === "peso") {
        const numero = Number(valor);
        if (!Number.isFinite(numero) || numero < 20 || numero > 250) {
            return { valido: false, mensaje: "El peso debe estar entre 20 y 250 kg." };
        }
    }
    return { valido: true };
}

function mostrarErrorPregunta(mensaje) {
    referencias.errorPregunta.hidden = false;
    referencias.errorPregunta.textContent = mensaje;
}

function ocultarErrorPregunta() {
    referencias.errorPregunta.hidden = true;
    referencias.errorPregunta.textContent = "";
}

function actualizarRespuestaPaso(pasoId, valor) {
    estado.respuestas[pasoId] = valor;
    referencias.btnSiguiente.disabled = !String(valor ?? "").trim();
    renderizarResumen();
    persistirEstado();
}

function sincronizarValorVisibleDelPaso(paso) {
    if (!paso || paso.tipo === "opcion") {
        return;
    }
    const input = document.getElementById("input-paso");
    if (!input) {
        return;
    }
    actualizarRespuestaPaso(paso.id, input.value);
}

function renderizarFoto() {
    const hayFoto = Boolean(estado.fotoDataUrl);
    const camaraActiva = Boolean(estado.stream);
    const backendDisponible = backendInicializado && Boolean(estado.tokenPublico);
    referencias.previewFoto.hidden = !hayFoto;
    referencias.previewFoto.src = hayFoto ? estado.fotoDataUrl : "";
    referencias.placeholderFoto.hidden = hayFoto || camaraActiva;
    referencias.videoCamara.hidden = !camaraActiva;
    referencias.btnAbrirCamara.hidden = hayFoto || camaraActiva;
    referencias.btnSacarFoto.hidden = !camaraActiva;
    referencias.btnSubirArchivo.hidden = camaraActiva;
    referencias.btnRepetirFoto.hidden = !hayFoto;
    referencias.btnConfirmarFoto.hidden = !hayFoto;
    referencias.btnConfirmarFoto.disabled = !hayFoto || !backendDisponible;
    referencias.errorFoto.hidden = backendDisponible;
    referencias.errorFoto.textContent = backendDisponible
        ? ""
        : `Backend desconectado. Levanta Django en ${API_BASE_URL} para subir y procesar la foto.`;
}

async function abrirCamara() {
    if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("Tu navegador no permite abrir camara aqui. Usa la opcion de subir imagen.");
    }
    cerrarCamara();
    estado.stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 720 }, height: { ideal: 960 } },
        audio: false,
    });
    referencias.videoCamara.srcObject = estado.stream;
    await referencias.videoCamara.play();
    renderizarFoto();
}

function cerrarCamara() {
    if (estado.stream) {
        estado.stream.getTracks().forEach((track) => track.stop());
        estado.stream = null;
    }
    referencias.videoCamara.srcObject = null;
    renderizarFoto();
}

function tomarFoto() {
    if (!referencias.videoCamara.videoWidth || !referencias.videoCamara.videoHeight) {
        mostrarToast("La camara todavia no esta lista.");
        return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = referencias.videoCamara.videoWidth;
    canvas.height = referencias.videoCamara.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(referencias.videoCamara, 0, 0);
    estado.fotoDataUrl = canvas.toDataURL("image/jpeg", 0.92);
    archivoActual = dataUrlAArchivo(estado.fotoDataUrl, "captura.jpg", "image/jpeg");
    cerrarCamara();
    persistirEstado();
    renderizarFoto();
}

function manejarArchivoSeleccionado(evento) {
    const archivo = evento.target.files?.[0];
    if (!archivo) {
        return;
    }
    void ejecutarAccion("Preparando tu imagen", async () => {
        if (!archivo.type.startsWith("image/")) {
            throw new Error("Selecciona un archivo de imagen valido.");
        }
        const imagenNormalizada = await normalizarArchivoImagen(archivo);
        archivoActual = imagenNormalizada.archivo;
        estado.fotoDataUrl = imagenNormalizada.dataUrl;
        persistirEstado();
        renderizarFoto();
        mostrarToast(
            `Imagen lista para subir (${Math.round(imagenNormalizada.archivo.size / 1024)} KB).`
        );
    });
    evento.target.value = "";
}

function limpiarFoto() {
    archivoActual = null;
    estado.fotoDataUrl = "";
    estado.fotoId = "";
    estado.resultadoId = "";
    estado.recorteUrl = "";
    estado.figuritaId = "";
    estado.figuritaUrl = "";
    renderizarFoto();
    renderizarResultado();
    persistirEstado();
}

async function confirmarFoto() {
    exigirBackendListo();
    if (!estado.fotoDataUrl) {
        throw new Error("Primero captura o sube una foto.");
    }
    if (!archivoActual) {
        archivoActual = dataUrlAArchivo(estado.fotoDataUrl, "foto.jpg", "image/jpeg");
    }
    mostrarPantalla("procesando");
    renderizarProcesamiento();
    await subirFotoBackend();
    await procesarFotoBackend();
    await esperarRecorteBackend();
    await generarFiguritaBackend();
    await esperarFiguritaBackend();
    mostrarPantalla("resultado");
    mostrarToast("La figurita final ya se genero con el backend.");
}

function renderizarProcesamiento() {
    referencias.listaProcesos.innerHTML = "";
    PASOS_PROCESAMIENTO.forEach((paso, indice) => {
        const item = document.createElement("li");
        item.className = "paso-proceso";
        item.innerHTML = `
            <span class="paso-proceso__indice">${indice + 1}</span>
            <div class="paso-proceso__texto">
                <strong>${paso.titulo}</strong>
                <span>${paso.detalle}</span>
            </div>
            <span class="paso-proceso__estado">pendiente</span>
        `;
        referencias.listaProcesos.appendChild(item);
    });
    actualizarProgresoProcesamiento(0, 0, PASOS_PROCESAMIENTO[0].titulo, PASOS_PROCESAMIENTO[0].detalle);
    referencias.previewProcesandoFoto.src = estado.fotoDataUrl || "assets/img/plantilla-figurita.png";
}

function actualizarProgresoProcesamiento(porcentaje, indiceActivo, titulo, detalle) {
    const circunferencia = 2 * Math.PI * 92;
    referencias.circuloProgreso.style.strokeDashoffset = String(circunferencia * (1 - porcentaje / 100));
    referencias.valorProgreso.textContent = `${Math.round(porcentaje)}%`;
    referencias.tituloProcesando.textContent = titulo;
    referencias.textoProcesando.textContent = detalle;
    [...referencias.listaProcesos.children].forEach((item, indice) => {
        item.classList.remove("paso-proceso--activo", "paso-proceso--completo");
        const estadoTexto = item.querySelector(".paso-proceso__estado");
        if (indice < indiceActivo) {
            item.classList.add("paso-proceso--completo");
            estadoTexto.textContent = "listo";
        } else if (indice === indiceActivo) {
            item.classList.add("paso-proceso--activo");
            estadoTexto.textContent = "activo";
        } else {
            estadoTexto.textContent = "pendiente";
        }
    });
}

function renderizarResultado() {
    renderizarDatosFinales();
    const hayFigurita = Boolean(estado.figuritaUrl);
    referencias.resultadoFigura.dataset.vacio = hayFigurita ? "false" : "true";
    referencias.imagenFiguritaFinal.src = hayFigurita ? estado.figuritaUrl : "";
    referencias.btnDescargar.disabled = !hayFigurita;
    referencias.btnCompartir.disabled = !hayFigurita;
}

function renderizarDatosFinales() {
    const items = [
        ["Nombre", estado.respuestas.nombre || "--"],
        ["Apellido", estado.respuestas.apellido || "--"],
        ["Fecha de nacimiento", formatearFecha(estado.respuestas.fechaNacimiento) || "--"],
        ["Altura", estado.respuestas.altura ? `${estado.respuestas.altura} cm` : "--"],
        ["Peso", estado.respuestas.peso ? `${estado.respuestas.peso} kg` : "--"],
        ["Equipo", estado.respuestas.equipo || "--"],
    ];
    referencias.listaDatosFinales.innerHTML = "";
    items.forEach(([titulo, valor]) => {
        const item = document.createElement("div");
        item.className = "lista-datos__item";
        item.innerHTML = `<dt>${titulo}</dt><dd>${valor}</dd>`;
        referencias.listaDatosFinales.appendChild(item);
    });
}

async function iniciarSesionBackend() {
    const datos = await solicitar("/api/sesiones/iniciar/", {
        method: "POST",
        body: estado.tokenPublico ? { token_publico: estado.tokenPublico } : {},
    });
    estado.tokenPublico = datos.sesion.token_publico;
    persistirEstado();
}

async function cargarEquiposBackend() {
    const equipos = await solicitar("/api/catalogos/equipos/");
    estado.equipos = equipos;
    PASOS_CUESTIONARIO.find((paso) => paso.id === "equipo").opciones = equipos.map((equipo) => equipo.nombre);
    persistirEstado();
}

async function cargarPreguntasBackend() {
    exigirTokenPublico();
    const datos = await solicitar(`/api/sesiones/${estado.tokenPublico}/preguntas/`);
    estado.preguntasBackend = datos.preguntas || [];
    sincronizarRespuestasDesdeBackend(datos.preguntas || []);
    persistirEstado();
}

function sincronizarRespuestasDesdeBackend(preguntas) {
    preguntas.forEach((pregunta) => {
        const localId = Object.keys(MAPA_CODIGOS_BACKEND).find((clave) => MAPA_CODIGOS_BACKEND[clave] === pregunta.codigo);
        if (!localId || !pregunta.respuesta_actual) {
            return;
        }
        estado.respuestas[localId] = pregunta.respuesta_actual.valor || "";
    });
}

async function sincronizarEstadoBackend() {
    exigirTokenPublico();
    const sesion = await solicitar(`/api/sesiones/${estado.tokenPublico}/estado/`);
    if (sesion.ultima_foto?.id) {
        estado.fotoId = sesion.ultima_foto.id;
    }
    if (sesion.ultimo_recorte?.id && estado.fotoId) {
        await consultarRecorteBackend();
    }
    if (sesion.ultima_figurita?.id) {
        estado.figuritaId = sesion.ultima_figurita.id;
        await consultarFiguritaBackend();
    }
    persistirEstado();
}

async function sincronizarPasoConBackend(paso) {
    exigirTokenPublico();
    const pregunta = obtenerPreguntaBackend(paso.id);
    if (!pregunta) {
        throw new Error("El cuestionario todavia no se sincronizo con el backend. Recarga la pagina.");
    }
    const valor = estado.respuestas[paso.id];
    const body = { pregunta_id: pregunta.id };
    if (paso.id === "equipo") {
        const equipo = estado.equipos.find((item) => item.nombre === valor);
        if (!equipo) {
            throw new Error("Ese equipo no esta disponible en el backend actual.");
        }
        body.equipo_id = equipo.id;
    } else {
        body.valor = paso.tipo === "numero" ? Number(valor) : valor;
    }
    await solicitar(`/api/sesiones/${estado.tokenPublico}/responder/`, {
        method: "POST",
        body,
    });
}

function obtenerPreguntaBackend(localId) {
    return estado.preguntasBackend.find((pregunta) => pregunta.codigo === MAPA_CODIGOS_BACKEND[localId]);
}

async function subirFotoBackend() {
    exigirTokenPublico();
    actualizarProgresoProcesamiento(12, 0, PASOS_PROCESAMIENTO[0].titulo, PASOS_PROCESAMIENTO[0].detalle);
    const formData = new FormData();
    formData.append("archivo", archivoActual, archivoActual.name || "foto.jpg");
    const datos = await solicitar(`/api/sesiones/${estado.tokenPublico}/imagenes/subir/`, {
        method: "POST",
        body: formData,
        timeoutMs: 45000,
    });
    estado.fotoId = datos.foto.id;
    persistirEstado();
    actualizarProgresoProcesamiento(24, 1, PASOS_PROCESAMIENTO[1].titulo, PASOS_PROCESAMIENTO[1].detalle);
}

async function procesarFotoBackend() {
    actualizarProgresoProcesamiento(30, 1, PASOS_PROCESAMIENTO[1].titulo, PASOS_PROCESAMIENTO[1].detalle);
    exigirTokenPublico();
    const datos = await solicitar(`/api/imagenes/${estado.fotoId}/procesar/`, {
        method: "POST",
        body: { token_publico: estado.tokenPublico },
        timeoutMs: 180000,
    });
    estado.resultadoId = datos.resultado.id;
    persistirEstado();
}

async function esperarRecorteBackend() {
    let porcentaje = 28;
    for (let intento = 0; intento < 50; intento += 1) {
        await esperar(1800);
        porcentaje = Math.min(70, porcentaje + 3);
        actualizarProgresoProcesamiento(porcentaje, 1, PASOS_PROCESAMIENTO[1].titulo, PASOS_PROCESAMIENTO[1].detalle);
        const resultado = await consultarRecorteBackend();
        if (resultado?.estado === "completado") {
            actualizarProgresoProcesamiento(74, 2, PASOS_PROCESAMIENTO[2].titulo, PASOS_PROCESAMIENTO[2].detalle);
            return;
        }
        if (resultado?.estado === "error") {
            throw new Error("El backend no pudo completar el recorte de la imagen.");
        }
    }
    throw new Error("El recorte tardo demasiado en completarse.");
}

async function consultarRecorteBackend() {
    const resultado = await solicitar(`/api/imagenes/${estado.fotoId}/resultado/`);
    estado.resultadoId = resultado.id;
    estado.recorteUrl = absolutizarUrl(resultado.png_transparente_url || "");
    persistirEstado();
    return resultado;
}

async function generarFiguritaBackend() {
    exigirTokenPublico();
    actualizarProgresoProcesamiento(82, 3, PASOS_PROCESAMIENTO[3].titulo, PASOS_PROCESAMIENTO[3].detalle);
    await sincronizarEstadoBackend();
    if (estado.figuritaId) {
        return;
    }
    if (!estado.resultadoId) {
        throw new Error("Todavia no hay un recorte completado para componer la figurita.");
    }
    const respuesta = await solicitar(`/api/sesiones/${estado.tokenPublico}/figuritas/generar/`, {
        method: "POST",
        body: { resultado_recorte_id: estado.resultadoId },
    });
    estado.figuritaId = respuesta.figurita.id;
    estado.figuritaUrl = absolutizarUrl(
        respuesta.figurita.imagen_final_url || respuesta.figurita.imagen_preview_url || ""
    );
    persistirEstado();
}

async function esperarFiguritaBackend() {
    if (estado.figuritaId && estado.figuritaUrl) {
        actualizarProgresoProcesamiento(100, 4, PASOS_PROCESAMIENTO[4].titulo, PASOS_PROCESAMIENTO[4].detalle);
        renderizarResultado();
        return;
    }
    let porcentaje = 86;
    for (let intento = 0; intento < 45; intento += 1) {
        await esperar(1600);
        porcentaje = Math.min(98, porcentaje + 2);
        actualizarProgresoProcesamiento(
            porcentaje,
            4,
            PASOS_PROCESAMIENTO[4].titulo,
            PASOS_PROCESAMIENTO[4].detalle
        );
        const figurita = await consultarFiguritaBackend();
        if (figurita?.estado === "completado") {
            actualizarProgresoProcesamiento(100, 4, PASOS_PROCESAMIENTO[4].titulo, "Figurita lista para descargar.");
            renderizarResultado();
            return;
        }
        if (figurita?.estado === "error") {
            throw new Error(figurita.mensaje_error || "La generacion final de la figurita fallo.");
        }
    }
    throw new Error("La figurita tardo demasiado en terminar de generarse.");
}

async function consultarFiguritaBackend() {
    if (!estado.figuritaId) {
        await sincronizarEstadoBackend();
    }
    if (!estado.figuritaId) {
        return null;
    }
    const figurita = await solicitar(`/api/figuritas/${estado.figuritaId}/`);
    estado.figuritaUrl = absolutizarUrl(
        figurita.imagen_final_url || figurita.imagen_preview_url || ""
    );
    persistirEstado();
    renderizarResultado();
    return figurita;
}

async function reanudarProcesamiento() {
    mostrarPantalla("procesando");
    renderizarProcesamiento();
    await sincronizarEstadoBackend();

    if (estado.figuritaId) {
        const figurita = await consultarFiguritaBackend();
        if (figurita?.estado === "completado" && estado.figuritaUrl) {
            mostrarPantalla("resultado");
            mostrarToast("Encontramos una figurita ya terminada para esta sesion.");
            return;
        }
        await esperarFiguritaBackend();
        mostrarPantalla("resultado");
        return;
    }

    if (!estado.fotoId) {
        mostrarPantalla("foto");
        return;
    }

    const recorte = await consultarRecorteBackend().catch(() => null);
    if (recorte?.estado === "completado") {
        await generarFiguritaBackend();
        await esperarFiguritaBackend();
        mostrarPantalla("resultado");
        return;
    }

    await esperarRecorteBackend();
    await generarFiguritaBackend();
    await esperarFiguritaBackend();
    mostrarPantalla("resultado");
}

async function descargarFigurita() {
    if (!estado.figuritaUrl) {
        throw new Error("Todavia no hay una figurita final para descargar.");
    }
    const respuesta = await fetch(estado.figuritaUrl);
    if (!respuesta.ok) {
        throw new Error("No pudimos descargar la imagen final.");
    }
    const blob = await respuesta.blob();
    const url = URL.createObjectURL(blob);
    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = construirNombreArchivo();
    document.body.appendChild(enlace);
    enlace.click();
    enlace.remove();
    URL.revokeObjectURL(url);
    mostrarToast("Descarga iniciada.");
}

async function compartirFigurita() {
    if (!estado.figuritaUrl) {
        throw new Error("Todavia no hay una figurita lista para compartir.");
    }
    if (!navigator.share) {
        await navigator.clipboard.writeText(estado.figuritaUrl);
        mostrarToast("Tu navegador no comparte archivos aqui. Copiamos el enlace final.");
        return;
    }

    const respuesta = await fetch(estado.figuritaUrl);
    if (!respuesta.ok) {
        throw new Error("No pudimos preparar la figurita para compartir.");
    }
    const blob = await respuesta.blob();
    const archivo = new File([blob], construirNombreArchivo(), { type: blob.type || "image/png" });
    const payload = {
        title: "Mi figurita mundialista",
        text: "Mira la figurita que arme con Figu Maker IA.",
    };
    if (navigator.canShare?.({ files: [archivo] })) {
        payload.files = [archivo];
    } else {
        payload.url = estado.figuritaUrl;
    }
    await navigator.share(payload);
}

function reiniciarAplicacion() {
    cerrarCamara();
    sessionStorage.removeItem(CLAVE_STORAGE);
    Object.assign(estado, restaurarEstado());
    archivoActual = null;
    renderizarResumen();
    renderizarCuestionario();
    renderizarFoto();
    renderizarResultado();
    mostrarPantalla("inicio");
    void arrancarBackend();
}

function exigirBackendListo() {
    if (!backendInicializado || !estado.tokenPublico) {
        throw new Error(
            `El backend no esta disponible en ${API_BASE_URL}. Levanta Django en el puerto 8000 y recarga la pagina.`
        );
    }
}

function exigirTokenPublico() {
    if (!estado.tokenPublico) {
        throw new Error(
            `No existe una sesion activa. Verifica que el backend responda en ${API_BASE_URL} y vuelve a cargar la pagina.`
        );
    }
}

let temporizadorToast = null;

function mostrarToast(mensaje) {
    if (!mensaje) {
        return;
    }
    referencias.toast.textContent = mensaje;
    referencias.toast.hidden = false;
    if (temporizadorToast) {
        window.clearTimeout(temporizadorToast);
    }
    temporizadorToast = window.setTimeout(() => {
        referencias.toast.hidden = true;
    }, 2800);
}

async function solicitar(ruta, opciones = {}) {
    const config = {
        method: opciones.method || "GET",
        headers: {},
    };
    if (opciones.body instanceof FormData) {
        config.body = opciones.body;
    } else if (opciones.body !== undefined) {
        config.headers["Content-Type"] = "application/json";
        config.body = JSON.stringify(opciones.body);
    }

    const controller = new AbortController();
    const timeoutMs = opciones.timeoutMs || 20000;
    const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
    config.signal = controller.signal;

    let respuesta;
    try {
        respuesta = await fetch(`${API_BASE_URL}${ruta}`, config);
    } catch (error) {
        window.clearTimeout(timeoutId);
        if (error.name === "AbortError") {
            throw new Error(
                `La solicitud al backend tardo demasiado (${Math.round(timeoutMs / 1000)}s). Intenta con una imagen mas liviana o vuelve a probar.`
            );
        }
        throw new Error(
            `No pudimos conectar con el backend en ${API_BASE_URL}. Asegurate de tener Django corriendo en el puerto 8000.`
        );
    }
    window.clearTimeout(timeoutId);
    const esJson = (respuesta.headers.get("content-type") || "").includes("application/json");
    const payload = esJson ? await respuesta.json() : null;

    if (!respuesta.ok) {
        const mensaje =
            payload?.error?.mensaje ||
            payload?.detail ||
            payload?.mensaje ||
            `La solicitud fallo con estado ${respuesta.status}.`;
        throw new Error(mensaje);
    }
    return payload;
}

function absolutizarUrl(url) {
    if (!url) {
        return "";
    }
    if (/^https?:\/\//i.test(url)) {
        return url;
    }
    return new URL(url, API_BASE_URL).toString();
}

function dataUrlAArchivo(dataUrl, nombre, mimeType) {
    const [cabecera, contenido] = dataUrl.split(",");
    const mime = mimeType || cabecera.match(/data:(.*?);base64/)?.[1] || "image/jpeg";
    const binario = window.atob(contenido);
    const bytes = new Uint8Array(binario.length);
    for (let indice = 0; indice < binario.length; indice += 1) {
        bytes[indice] = binario.charCodeAt(indice);
    }
    return new File([bytes], nombre, { type: mime });
}

async function normalizarArchivoImagen(archivo) {
    const dataUrlOriginal = await leerArchivoComoDataUrl(archivo);
    const imagen = await cargarImagen(dataUrlOriginal);
    const maxDimension = 1600;
    const { width, height } = calcularDimensionEscalada(
        imagen.naturalWidth || imagen.width,
        imagen.naturalHeight || imagen.height,
        maxDimension
    );

    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const contexto = canvas.getContext("2d", { alpha: false });
    contexto.fillStyle = "#ffffff";
    contexto.fillRect(0, 0, width, height);
    contexto.drawImage(imagen, 0, 0, width, height);

    const dataUrlNormalizada = canvas.toDataURL("image/jpeg", 0.9);
    const nombreBase = (archivo.name || "foto")
        .replace(/\.[^.]+$/, "")
        .replace(/\s+/g, "-")
        .toLowerCase();
    return {
        dataUrl: dataUrlNormalizada,
        archivo: dataUrlAArchivo(dataUrlNormalizada, `${nombreBase || "foto"}.jpg`, "image/jpeg"),
    };
}

function leerArchivoComoDataUrl(archivo) {
    return new Promise((resolve, reject) => {
        const lector = new FileReader();
        lector.onload = () => resolve(lector.result);
        lector.onerror = () => reject(new Error("No pudimos leer la imagen seleccionada."));
        lector.readAsDataURL(archivo);
    });
}

function cargarImagen(src) {
    return new Promise((resolve, reject) => {
        const imagen = new Image();
        imagen.onload = () => resolve(imagen);
        imagen.onerror = () => reject(new Error("No pudimos procesar la imagen elegida."));
        imagen.src = src;
    });
}

function calcularDimensionEscalada(ancho, alto, maxDimension) {
    if (Math.max(ancho, alto) <= maxDimension) {
        return { width: ancho, height: alto };
    }
    const proporcion = maxDimension / Math.max(ancho, alto);
    return {
        width: Math.max(1, Math.round(ancho * proporcion)),
        height: Math.max(1, Math.round(alto * proporcion)),
    };
}

function esperar(ms) {
    return new Promise((resolve) => {
        window.setTimeout(resolve, ms);
    });
}

function formatearValorRespuesta(id, valor) {
    if (!valor) {
        return "";
    }
    if (id === "fechaNacimiento") {
        return formatearFecha(valor);
    }
    if (id === "altura") {
        return `${valor} cm`;
    }
    if (id === "peso") {
        return `${valor} kg`;
    }
    return String(valor);
}

function formatearFecha(valor) {
    if (!valor) {
        return "";
    }
    const fecha = new Date(valor);
    if (Number.isNaN(fecha.getTime())) {
        return String(valor);
    }
    return fecha.toLocaleDateString("es-AR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
    });
}

function construirNombreArchivo() {
    const partes = [estado.respuestas.nombre, estado.respuestas.apellido]
        .map((valor) => (valor || "").trim().toLowerCase().replace(/\s+/g, "-"))
        .filter(Boolean);
    const base = partes.length ? partes.join("_") : "mi_figurita";
    return `${base}_panini.png`;
}
