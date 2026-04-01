const PASOS_CUESTIONARIO = [
    {
        id: "nombre",
        codigo: "NOMBRE",
        etiqueta: "Cual es tu nombre?",
        placeholder: "Ej: Lionel",
        tipo: "texto",
        ayuda: "Tu nombre va en la figurita final con presencia de portada.",
    },
    {
        id: "apellido",
        codigo: "APELLIDO",
        etiqueta: "Y tu apellido?",
        placeholder: "Ej: Messi",
        tipo: "texto",
        ayuda: "Lo usamos como apellido protagonista en el header de la carta.",
    },
    {
        id: "fechaNacimiento",
        codigo: "FECHA",
        etiqueta: "Cuando naciste?",
        placeholder: "",
        tipo: "fecha",
        ayuda: "La fecha aparece en la franja de estadisticas de la figurita.",
    },
    {
        id: "altura",
        codigo: "ALTURA",
        etiqueta: "Cuanto medis? (cm)",
        placeholder: "Ej: 178",
        tipo: "numero",
        ayuda: "Altura en centimetros, como en una ficha de jugador profesional.",
    },
    {
        id: "peso",
        codigo: "PESO",
        etiqueta: "Cuanto pesas? (kg)",
        placeholder: "Ej: 72",
        tipo: "numero",
        ayuda: "Peso en kilogramos para completar la linea de datos.",
    },
    {
        id: "equipo",
        codigo: "EQUIPO",
        etiqueta: "De que equipo sos?",
        placeholder: "Elegi tu equipo",
        tipo: "opcion",
        ayuda: "Selecciona el club que quieres mostrar en la franja inferior.",
        opciones: [
            "Boca Juniors",
            "River Plate",
            "Racing Club",
            "Independiente",
            "San Lorenzo",
            "Huracan",
            "Velez Sarsfield",
            "Argentinos Juniors",
            "Estudiantes LP",
            "Gimnasia LP",
            "Newell's Old Boys",
            "Rosario Central",
            "Talleres",
            "Belgrano",
            "Colon",
            "Union",
            "Banfield",
            "Lanus",
            "Defensa y Justicia",
            "Godoy Cruz",
            "Otro",
        ],
    },
];

const PASOS_PROCESAMIENTO = [
    { id: "subida", titulo: "Subiendo tu foto", detalle: "Armando el paquete visual inicial.", duracion: 1300 },
    { id: "rostro", titulo: "Detectando rostro", detalle: "Buscando la mejor presencia dentro del marco.", duracion: 1700 },
    { id: "analisis", titulo: "Analizando encuadre", detalle: "Ajustando foco, posicion y silueta.", duracion: 1500 },
    { id: "composicion", titulo: "Componiendo figurita", detalle: "Integrando foto, colores y datos.", duracion: 2100 },
    { id: "acabado", titulo: "Aplicando acabado final", detalle: "Brillo, overlays y toque premium.", duracion: 1200 },
];

const estado = {
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
    fotoDataUrl: "",
    stream: null,
    procesando: false,
    temporizadores: [],
    resultadoDataUrl: "",
};

const referencias = {};

document.addEventListener("DOMContentLoaded", iniciarAplicacion);

function iniciarAplicacion() {
    cachearReferencias();
    insertarDefinicionGradiente();
    crearParticulas();
    enlazarEventos();
    restaurarEstado();
    renderizarResumen();
    renderizarCuestionario();
    renderizarFoto();
    mostrarPantalla(estado.pantalla);
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
    referencias.canvasFigurita = document.getElementById("canvas-figurita");
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

function enlazarEventos() {
    referencias.btnEmpezar.addEventListener("click", () => {
        estado.pantalla = "cuestionario";
        guardarEstado();
        mostrarPantalla("cuestionario");
    });

    referencias.btnIrPlantilla.addEventListener("click", () => {
        const tarjeta = document.querySelector(".figurita-showcase");
        if (tarjeta) {
            tarjeta.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    });

    referencias.btnAnterior.addEventListener("click", manejarAnterior);
    referencias.btnSiguiente.addEventListener("click", avanzarCuestionario);
    referencias.btnAbrirCamara.addEventListener("click", abrirCamara);
    referencias.btnSacarFoto.addEventListener("click", tomarFoto);
    referencias.btnSubirArchivo.addEventListener("click", () => referencias.inputArchivo.click());
    referencias.inputArchivo.addEventListener("change", manejarArchivoSeleccionado);
    referencias.btnRepetirFoto.addEventListener("click", limpiarFoto);
    referencias.btnConfirmarFoto.addEventListener("click", confirmarFoto);
    referencias.btnVolverQuiz.addEventListener("click", () => {
        cerrarCamara();
        estado.pantalla = "cuestionario";
        guardarEstado();
        mostrarPantalla("cuestionario");
    });
    referencias.btnDescargar.addEventListener("click", descargarFigurita);
    referencias.btnCompartir.addEventListener("click", compartirFigurita);
    referencias.btnReiniciar.addEventListener("click", reiniciarAplicacion);

    window.addEventListener("beforeunload", cerrarCamara);
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

function restaurarEstado() {
    const bruto = sessionStorage.getItem("figu-maker-ia-estado");
    if (!bruto) {
        return;
    }
    try {
        const data = JSON.parse(bruto);
        if (data && typeof data === "object") {
            estado.pantalla = data.pantalla || "inicio";
            estado.pasoActual = Number.isInteger(data.pasoActual) ? data.pasoActual : 0;
            estado.respuestas = { ...estado.respuestas, ...(data.respuestas || {}) };
            estado.fotoDataUrl = data.fotoDataUrl || "";
            estado.resultadoDataUrl = data.resultadoDataUrl || "";
        }
    } catch (_error) {
        sessionStorage.removeItem("figu-maker-ia-estado");
    }

    if (!estado.fotoDataUrl && (estado.pantalla === "procesando" || estado.pantalla === "resultado")) {
        estado.pantalla = "cuestionario";
    }
    if (estado.pasoActual >= PASOS_CUESTIONARIO.length) {
        estado.pasoActual = PASOS_CUESTIONARIO.length - 1;
    }
}

function guardarEstado() {
    sessionStorage.setItem(
        "figu-maker-ia-estado",
        JSON.stringify({
            pantalla: estado.pantalla,
            pasoActual: estado.pasoActual,
            respuestas: estado.respuestas,
            fotoDataUrl: estado.fotoDataUrl,
            resultadoDataUrl: estado.resultadoDataUrl,
        }),
    );
}

function mostrarPantalla(nombre) {
    limpiarTemporizadores();
    Object.entries(referencias.pantallas).forEach(([clave, nodo]) => {
        if (nodo) {
            nodo.hidden = clave !== nombre;
        }
    });

    estado.pantalla = nombre;
    referencias.etiquetaPantalla.textContent = formatearPantalla(nombre);

    if (nombre === "cuestionario") {
        renderizarCuestionario();
    }
    if (nombre === "foto") {
        renderizarFoto();
    }
    if (nombre === "procesando") {
        renderizarProcesamiento();
        ejecutarProcesamiento();
    }
    if (nombre === "resultado") {
        renderizarResultado();
    }
    guardarEstado();
}

function formatearPantalla(nombre) {
    const mapa = {
        inicio: "Inicio",
        cuestionario: "Cuestionario",
        foto: "Foto",
        procesando: "Procesando",
        resultado: "Resultado",
    };
    return mapa[nombre] || "Pantalla";
}

function manejarAnterior() {
    ocultarErrorPregunta();
    if (estado.pasoActual === 0) {
        estado.pantalla = "inicio";
        guardarEstado();
        mostrarPantalla("inicio");
        return;
    }
    estado.pasoActual -= 1;
    guardarEstado();
    renderizarCuestionario();
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
    referencias.btnSiguiente.disabled = !puedeAvanzarEnPaso(paso, estado.respuestas[paso.id]);
    renderizarResumen();
}

function renderizarCampoTexto(paso) {
    const stack = document.createElement("div");
    stack.className = "campo-pregunta__stack";

    const input = document.createElement("input");
    input.className = "campo-control";
    input.type = paso.tipo === "fecha" ? "date" : paso.tipo === "numero" ? "number" : "text";
    input.placeholder = paso.placeholder;
    input.value = estado.respuestas[paso.id] || "";
    if (paso.tipo === "numero") {
        input.inputMode = "numeric";
        input.step = "1";
    }

    const ayuda = document.createElement("p");
    ayuda.className = "campo-ayuda";
    ayuda.textContent = paso.tipo === "fecha"
        ? "Usa una fecha real. La validamos para mantener una edad razonable."
        : paso.tipo === "numero"
            ? "El valor debe estar dentro de un rango coherente para una ficha deportiva."
            : "Escribe el dato tal como quieres que aparezca en la experiencia.";

    input.addEventListener("input", (evento) => {
        estado.respuestas[paso.id] = evento.target.value;
        referencias.btnSiguiente.disabled = !puedeAvanzarEnPaso(paso, estado.respuestas[paso.id]);
        renderizarResumen();
        guardarEstado();
    });

    input.addEventListener("keydown", (evento) => {
        if (evento.key === "Enter" && !referencias.btnSiguiente.disabled) {
            avanzarCuestionario();
        }
    });

    stack.appendChild(input);
    stack.appendChild(ayuda);
    referencias.campoPregunta.appendChild(stack);
    input.focus();
}

function renderizarCampoOpciones(paso) {
    const stack = document.createElement("div");
    stack.className = "campo-pregunta__stack";

    const grid = document.createElement("div");
    grid.className = "opciones-grid";

    paso.opciones.forEach((opcion) => {
        const boton = document.createElement("button");
        boton.type = "button";
        boton.className = "opcion-equipo";
        boton.textContent = opcion;
        if (estado.respuestas[paso.id] === opcion) {
            boton.classList.add("opcion-equipo--activa");
        }
        boton.addEventListener("click", () => {
            estado.respuestas[paso.id] = opcion;
            guardarEstado();
            renderizarResumen();
            renderizarCampoOpciones(paso);
            setTimeout(() => {
                avanzarCuestionario();
            }, 220);
        });
        grid.appendChild(boton);
    });

    const ayuda = document.createElement("p");
    ayuda.className = "campo-ayuda";
    ayuda.textContent = "Pulsa sobre un equipo y avanzamos automaticamente al siguiente paso.";

    stack.appendChild(grid);
    stack.appendChild(ayuda);
    referencias.campoPregunta.innerHTML = "";
    referencias.campoPregunta.appendChild(stack);
    referencias.btnSiguiente.disabled = !puedeAvanzarEnPaso(paso, estado.respuestas[paso.id]);
}

function puedeAvanzarEnPaso(paso, valor) {
    if (paso.tipo === "opcion") {
        return Boolean((valor || "").trim());
    }
    return Boolean((valor || "").toString().trim());
}

function avanzarCuestionario() {
    const paso = PASOS_CUESTIONARIO[estado.pasoActual];
    const valor = estado.respuestas[paso.id];
    const validacion = validarPaso(paso, valor);

    if (!validacion.valido) {
        mostrarErrorPregunta(validacion.mensaje);
        return;
    }

    ocultarErrorPregunta();

    if (estado.pasoActual === PASOS_CUESTIONARIO.length - 1) {
        estado.pantalla = "foto";
        guardarEstado();
        mostrarPantalla("foto");
        return;
    }

    estado.pasoActual += 1;
    guardarEstado();
    renderizarCuestionario();
}

function validarPaso(paso, valorBruto) {
    const valor = (valorBruto || "").toString().trim();
    if (!valor) {
        return { valido: false, mensaje: "Completa este dato para seguir." };
    }

    if (paso.id === "nombre" || paso.id === "apellido") {
        if (valor.length < 2) {
            return { valido: false, mensaje: "Necesitamos al menos 2 letras para que luzca bien en la figurita." };
        }
        if (valor.length > 32) {
            return { valido: false, mensaje: "Este texto es demasiado largo para la composicion final." };
        }
    }

    if (paso.id === "fechaNacimiento") {
        const fecha = new Date(valor);
        if (Number.isNaN(fecha.getTime())) {
            return { valido: false, mensaje: "Ingresa una fecha valida." };
        }
        const hoy = new Date();
        let edad = hoy.getFullYear() - fecha.getFullYear();
        const mes = hoy.getMonth() - fecha.getMonth();
        if (mes < 0 || (mes === 0 && hoy.getDate() < fecha.getDate())) {
            edad -= 1;
        }
        if (edad < 5 || edad > 100) {
            return { valido: false, mensaje: "La edad debe estar entre 5 y 100 anos." };
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

function renderizarResumen() {
    referencias.listaResumen.innerHTML = "";
    PASOS_CUESTIONARIO.forEach((paso, indice) => {
        const item = document.createElement("li");
        item.className = "resumen-item";
        if (estado.respuestas[paso.id]) {
            item.classList.add("resumen-item--completo");
        }

        const titulo = document.createElement("strong");
        const textoPaso = document.createElement("span");
        textoPaso.textContent = `Paso ${indice + 1}`;
        titulo.textContent = paso.codigo;
        titulo.appendChild(textoPaso);

        const valor = document.createElement("p");
        valor.textContent = formatearValorRespuesta(paso.id, estado.respuestas[paso.id]) || "Pendiente";

        item.appendChild(titulo);
        item.appendChild(valor);
        referencias.listaResumen.appendChild(item);
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
    return valor;
}

function renderizarFoto() {
    const hayFoto = Boolean(estado.fotoDataUrl);
    const camaraActiva = Boolean(estado.stream);

    referencias.previewFoto.hidden = !hayFoto;
    referencias.previewFoto.src = hayFoto ? estado.fotoDataUrl : "";
    referencias.placeholderFoto.hidden = hayFoto || camaraActiva;
    referencias.videoCamara.hidden = !camaraActiva;
    referencias.btnAbrirCamara.hidden = hayFoto || camaraActiva;
    referencias.btnSacarFoto.hidden = !camaraActiva;
    referencias.btnSubirArchivo.hidden = camaraActiva;
    referencias.btnRepetirFoto.hidden = !hayFoto;
    referencias.btnConfirmarFoto.hidden = !hayFoto;

    if (hayFoto) {
        referencias.previewProcesandoFoto.src = estado.fotoDataUrl;
    }
    guardarEstado();
}

async function abrirCamara() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        mostrarErrorFoto("Este navegador no permite acceder a la camara aqui. Usa la opcion de subir imagen.");
        return;
    }

    try {
        cerrarCamara();
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: "user",
                width: { ideal: 720 },
                height: { ideal: 960 },
            },
            audio: false,
        });
        estado.stream = stream;
        referencias.videoCamara.srcObject = stream;
        referencias.videoCamara.play().catch(() => {});
        ocultarErrorFoto();
        renderizarFoto();
    } catch (_error) {
        mostrarErrorFoto("No se pudo abrir la camara. Si estas en file local o sin permisos, prueba subiendo una foto.");
    }
}

function cerrarCamara() {
    if (estado.stream) {
        estado.stream.getTracks().forEach((track) => track.stop());
        estado.stream = null;
    }
    if (referencias.videoCamara) {
        referencias.videoCamara.srcObject = null;
    }
    renderizarFoto();
}

function tomarFoto() {
    if (!referencias.videoCamara.videoWidth || !referencias.videoCamara.videoHeight) {
        mostrarErrorFoto("La camara aun no esta lista. Espera un instante o sube una imagen.");
        return;
    }

    const lienzo = document.createElement("canvas");
    lienzo.width = referencias.videoCamara.videoWidth;
    lienzo.height = referencias.videoCamara.videoHeight;
    const contexto = lienzo.getContext("2d");
    contexto.drawImage(referencias.videoCamara, 0, 0, lienzo.width, lienzo.height);
    estado.fotoDataUrl = lienzo.toDataURL("image/jpeg", 0.92);
    cerrarCamara();
    ocultarErrorFoto();
    renderizarFoto();
}

function manejarArchivoSeleccionado(evento) {
    const archivo = evento.target.files && evento.target.files[0];
    if (!archivo) {
        return;
    }
    if (!archivo.type.startsWith("image/")) {
        mostrarErrorFoto("Selecciona un archivo de imagen valido.");
        evento.target.value = "";
        return;
    }
    const lector = new FileReader();
    lector.onload = () => {
        estado.fotoDataUrl = lector.result;
        ocultarErrorFoto();
        renderizarFoto();
    };
    lector.onerror = () => {
        mostrarErrorFoto("No pudimos leer ese archivo. Intenta con otra imagen.");
    };
    lector.readAsDataURL(archivo);
    evento.target.value = "";
}

function limpiarFoto() {
    estado.fotoDataUrl = "";
    estado.resultadoDataUrl = "";
    ocultarErrorFoto();
    renderizarFoto();
}

function confirmarFoto() {
    if (!estado.fotoDataUrl) {
        mostrarErrorFoto("Primero elige o captura una foto.");
        return;
    }
    estado.pantalla = "procesando";
    guardarEstado();
    mostrarPantalla("procesando");
}

function mostrarErrorFoto(mensaje) {
    referencias.errorFoto.hidden = false;
    referencias.errorFoto.textContent = mensaje;
}

function ocultarErrorFoto() {
    referencias.errorFoto.hidden = true;
    referencias.errorFoto.textContent = "";
}

function renderizarProcesamiento() {
    referencias.listaProcesos.innerHTML = "";
    PASOS_PROCESAMIENTO.forEach((paso, indice) => {
        const item = document.createElement("li");
        item.className = "paso-proceso";
        item.dataset.index = String(indice);
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
    actualizarAnillo(0);
    referencias.tituloProcesando.textContent = "Preparando tu figurita";
    referencias.textoProcesando.textContent = "Subimos, analizamos y componemos la experiencia como en el demo original.";
    referencias.previewProcesandoFoto.src = estado.fotoDataUrl || "assets/img/plantilla-figurita.png";
}

async function ejecutarProcesamiento() {
    if (estado.procesando) {
        return;
    }

    estado.procesando = true;
    const duracionTotal = PASOS_PROCESAMIENTO.reduce((acumulado, paso) => acumulado + paso.duracion, 0);
    let duracionAcumulada = 0;

    for (let indice = 0; indice < PASOS_PROCESAMIENTO.length; indice += 1) {
        const paso = PASOS_PROCESAMIENTO[indice];
        marcarPasoProceso(indice);
        referencias.tituloProcesando.textContent = paso.titulo;
        referencias.textoProcesando.textContent = paso.detalle;

        await new Promise((resolver) => {
            const inicio = performance.now();
            const intervalo = window.setInterval(() => {
                const transcurrido = performance.now() - inicio;
                const ratio = Math.min(transcurrido / paso.duracion, 1);
                const progreso = ((duracionAcumulada + paso.duracion * ratio) / duracionTotal) * 100;
                actualizarAnillo(progreso);
                if (ratio >= 1) {
                    clearInterval(intervalo);
                    resolver();
                }
            }, 40);
            estado.temporizadores.push(intervalo);
        });

        duracionAcumulada += paso.duracion;
    }

    marcarPasoProceso(PASOS_PROCESAMIENTO.length);
    actualizarAnillo(100);
    await generarFiguritaFinal();
    estado.procesando = false;
    estado.pantalla = "resultado";
    guardarEstado();
    setTimeout(() => {
        mostrarPantalla("resultado");
    }, 280);
}

function marcarPasoProceso(indiceActivo) {
    const items = referencias.listaProcesos.querySelectorAll(".paso-proceso");
    items.forEach((item, indice) => {
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

function actualizarAnillo(valor) {
    const progreso = Math.max(0, Math.min(100, valor));
    const circunferencia = 2 * Math.PI * 92;
    const offset = circunferencia * (1 - progreso / 100);
    referencias.circuloProgreso.style.strokeDashoffset = String(offset);
    referencias.valorProgreso.textContent = `${Math.round(progreso)}%`;
}

async function generarFiguritaFinal() {
    const canvas = referencias.canvasFigurita;
    const ctx = canvas.getContext("2d");
    const ancho = canvas.width;
    const alto = canvas.height;

    const plantilla = await cargarImagen("assets/img/plantilla-figurita.png");
    const foto = estado.fotoDataUrl ? await cargarImagen(estado.fotoDataUrl) : null;

    ctx.clearRect(0, 0, ancho, alto);

    const fondo = ctx.createLinearGradient(0, 0, ancho, alto);
    fondo.addColorStop(0, "#09121f");
    fondo.addColorStop(0.45, "#0f233e");
    fondo.addColorStop(1, "#09111d");
    ctx.fillStyle = fondo;
    ctx.fillRect(0, 0, ancho, alto);

    pintarResplandor(ctx, ancho * 0.18, alto * 0.17, 240, "rgba(255, 77, 94, 0.24)");
    pintarResplandor(ctx, ancho * 0.82, alto * 0.2, 250, "rgba(69, 140, 255, 0.24)");
    pintarResplandor(ctx, ancho * 0.5, alto * 0.85, 260, "rgba(32, 202, 123, 0.18)");

    ctx.save();
    ctx.globalAlpha = 0.16;
    dibujarImagenCubierta(ctx, plantilla, 0, 0, ancho, alto);
    ctx.restore();

    ctx.save();
    ctx.globalAlpha = 0.14;
    ctx.fillStyle = "#ffffff";
    ctx.font = "900 470px Orbitron, sans-serif";
    ctx.fillText("26", 48, 360);
    ctx.restore();

    const xFoto = 118;
    const yFoto = 138;
    const anchoFoto = 664;
    const altoFoto = 708;

    pintarRectanguloRedondeado(ctx, xFoto - 8, yFoto - 8, anchoFoto + 16, altoFoto + 16, 36, "rgba(255,255,255,0.14)");
    pintarRectanguloRedondeado(ctx, xFoto, yFoto, anchoFoto, altoFoto, 32, "rgba(255,255,255,0.08)");

    ctx.save();
    crearRecorteRedondeado(ctx, xFoto, yFoto, anchoFoto, altoFoto, 32);
    ctx.clip();
    if (foto) {
        dibujarImagenCubierta(ctx, foto, xFoto, yFoto, anchoFoto, altoFoto);
    } else {
        const grad = ctx.createLinearGradient(xFoto, yFoto, xFoto, yFoto + altoFoto);
        grad.addColorStop(0, "#18324e");
        grad.addColorStop(1, "#0d192a");
        ctx.fillStyle = grad;
        ctx.fillRect(xFoto, yFoto, anchoFoto, altoFoto);
    }
    const velo = ctx.createLinearGradient(0, yFoto, 0, yFoto + altoFoto);
    velo.addColorStop(0, "rgba(9, 18, 31, 0.08)");
    velo.addColorStop(1, "rgba(9, 18, 31, 0.45)");
    ctx.fillStyle = velo;
    ctx.fillRect(xFoto, yFoto, anchoFoto, altoFoto);
    ctx.restore();

    ctx.save();
    ctx.globalAlpha = 0.12;
    dibujarImagenCubierta(ctx, plantilla, xFoto, yFoto, anchoFoto, altoFoto);
    ctx.restore();

    pintarFranja(ctx, 96, 906, 708, 114, 28, ["#0c566a", "#1594a7"]);
    pintarFranja(ctx, 96, 1040, 566, 86, 24, ["#0c566a", "#1594a7"]);
    pintarFranja(ctx, 680, 1040, 154, 86, 22, ["#ffd83f", "#f3a600"]);

    ctx.save();
    ctx.strokeStyle = "rgba(255,255,255,0.14)";
    ctx.lineWidth = 3;
    ctx.strokeRect(680, 1040, 154, 86);
    ctx.restore();

    ctx.fillStyle = "#ffffff";
    ctx.font = "500 42px Montserrat, sans-serif";
    ctx.fillText((estado.respuestas.nombre || "Jugador").toUpperCase(), 132, 971);
    ctx.font = "800 42px Montserrat, sans-serif";
    const anchoNombre = ctx.measureText((estado.respuestas.nombre || "Jugador").toUpperCase()).width;
    ctx.fillText((estado.respuestas.apellido || "Premium").toUpperCase(), 152 + anchoNombre, 971);

    ctx.font = "500 28px Montserrat, sans-serif";
    const lineaSecundaria = [
        formatearFecha(estado.respuestas.fechaNacimiento),
        `${estado.respuestas.altura || "--"} cm`,
        `${estado.respuestas.peso || "--"} kg`,
    ].join("  |  ");
    ctx.fillText(lineaSecundaria, 130, 1018);

    ctx.font = "800 34px Montserrat, sans-serif";
    ctx.fillText((estado.respuestas.equipo || "Equipo").toUpperCase(), 130, 1096);
    ctx.font = "600 30px Montserrat, sans-serif";
    ctx.fillText("(ARG)", 540, 1096);

    ctx.fillStyle = "#1d1220";
    ctx.font = "900 26px Orbitron, sans-serif";
    ctx.fillText("PANINI", 702, 1095);

    ctx.save();
    ctx.fillStyle = "#ffffff";
    ctx.font = "900 74px Orbitron, sans-serif";
    ctx.textAlign = "right";
    ctx.fillText("26", 840, 122);
    ctx.font = "800 30px Orbitron, sans-serif";
    ctx.fillText("FIFA", 840, 164);
    ctx.restore();

    ctx.save();
    ctx.translate(865, 616);
    ctx.rotate(Math.PI / 2);
    ctx.font = "900 60px Orbitron, sans-serif";
    ctx.strokeStyle = "rgba(255,255,255,0.72)";
    ctx.lineWidth = 5;
    ctx.strokeText("ARG", 0, 0);
    ctx.fillStyle = "rgba(255,255,255,0.16)";
    ctx.fillText("ARG", 0, 0);
    ctx.restore();

    ctx.save();
    ctx.beginPath();
    ctx.arc(780, 760, 58, 0, Math.PI * 2);
    ctx.fillStyle = "#ffffff";
    ctx.fill();
    ctx.clip();
    ctx.fillStyle = "#7bc1ff";
    ctx.fillRect(722, 716, 116, 24);
    ctx.fillRect(722, 780, 116, 24);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(722, 740, 116, 40);
    ctx.fillStyle = "#d0a13f";
    ctx.beginPath();
    ctx.arc(780, 760, 10, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    estado.resultadoDataUrl = canvas.toDataURL("image/png");
    renderizarDatosFinales();
    guardarEstado();
}

function pintarResplandor(ctx, x, y, radio, color) {
    const gradiente = ctx.createRadialGradient(x, y, 0, x, y, radio);
    gradiente.addColorStop(0, color);
    gradiente.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = gradiente;
    ctx.fillRect(x - radio, y - radio, radio * 2, radio * 2);
}

function pintarFranja(ctx, x, y, ancho, alto, radio, colores) {
    const gradiente = ctx.createLinearGradient(x, y, x + ancho, y + alto);
    gradiente.addColorStop(0, colores[0]);
    gradiente.addColorStop(1, colores[1]);
    pintarRectanguloRedondeado(ctx, x, y, ancho, alto, radio, gradiente);
}

function pintarRectanguloRedondeado(ctx, x, y, ancho, alto, radio, relleno) {
    ctx.save();
    crearRecorteRedondeado(ctx, x, y, ancho, alto, radio);
    ctx.fillStyle = relleno;
    ctx.fill();
    ctx.restore();
}

function crearRecorteRedondeado(ctx, x, y, ancho, alto, radio) {
    ctx.beginPath();
    ctx.moveTo(x + radio, y);
    ctx.arcTo(x + ancho, y, x + ancho, y + alto, radio);
    ctx.arcTo(x + ancho, y + alto, x, y + alto, radio);
    ctx.arcTo(x, y + alto, x, y, radio);
    ctx.arcTo(x, y, x + ancho, y, radio);
    ctx.closePath();
}

function dibujarImagenCubierta(ctx, imagen, x, y, ancho, alto) {
    const ratio = Math.max(ancho / imagen.width, alto / imagen.height);
    const anchoDibujo = imagen.width * ratio;
    const altoDibujo = imagen.height * ratio;
    const xDibujo = x + (ancho - anchoDibujo) / 2;
    const yDibujo = y + (alto - altoDibujo) / 2;
    ctx.drawImage(imagen, xDibujo, yDibujo, anchoDibujo, altoDibujo);
}

function renderizarResultado() {
    renderizarDatosFinales();
    if (estado.resultadoDataUrl) {
        referencias.btnDescargar.disabled = false;
        referencias.btnCompartir.disabled = false;
    }
}

function renderizarDatosFinales() {
    const items = [
        ["Nombre", estado.respuestas.nombre || "Jugador"],
        ["Apellido", estado.respuestas.apellido || "Premium"],
        ["Fecha de nacimiento", formatearFecha(estado.respuestas.fechaNacimiento) || "--"],
        ["Altura", estado.respuestas.altura ? `${estado.respuestas.altura} cm` : "--"],
        ["Peso", estado.respuestas.peso ? `${estado.respuestas.peso} kg` : "--"],
        ["Equipo", estado.respuestas.equipo || "--"],
    ];
    referencias.listaDatosFinales.innerHTML = "";
    items.forEach(([termino, definicion]) => {
        const wrapper = document.createElement("div");
        wrapper.className = "lista-datos__item";
        const dt = document.createElement("dt");
        dt.textContent = termino;
        const dd = document.createElement("dd");
        dd.textContent = definicion;
        wrapper.appendChild(dt);
        wrapper.appendChild(dd);
        referencias.listaDatosFinales.appendChild(wrapper);
    });
}

function descargarFigurita() {
    if (!estado.resultadoDataUrl) {
        mostrarToast("Todavia no tenemos una figurita generada para descargar.");
        return;
    }
    const enlace = document.createElement("a");
    enlace.href = estado.resultadoDataUrl;
    enlace.download = construirNombreArchivo();
    document.body.appendChild(enlace);
    enlace.click();
    enlace.remove();
    mostrarToast("Descarga iniciada.");
}

async function compartirFigurita() {
    if (!estado.resultadoDataUrl) {
        mostrarToast("Genera primero la figurita final.");
        return;
    }

    if (!navigator.share) {
        mostrarToast("Tu navegador no soporta compartir archivos. Usa Descargar PNG.");
        return;
    }

    try {
        const archivo = await convertirDataUrlEnArchivo(estado.resultadoDataUrl, construirNombreArchivo());
        await navigator.share({
            title: "Mi figurita mundialista",
            text: "Mira mi figurita premium generada en la version vanilla.",
            files: [archivo],
        });
    } catch (_error) {
        mostrarToast("No pudimos abrir el panel de compartir. Descarga el PNG como alternativa.");
    }
}

function reiniciarAplicacion() {
    limpiarTemporizadores();
    cerrarCamara();
    estado.pantalla = "inicio";
    estado.pasoActual = 0;
    estado.respuestas = {
        nombre: "",
        apellido: "",
        fechaNacimiento: "",
        altura: "",
        peso: "",
        equipo: "",
    };
    estado.fotoDataUrl = "";
    estado.procesando = false;
    estado.resultadoDataUrl = "";
    sessionStorage.removeItem("figu-maker-ia-estado");
    renderizarResumen();
    renderizarCuestionario();
    renderizarFoto();
    mostrarPantalla("inicio");
    mostrarToast("Listo, volvimos al inicio para crear otra figurita.");
}

function limpiarTemporizadores() {
    estado.temporizadores.forEach((id) => clearInterval(id));
    estado.temporizadores = [];
    estado.procesando = false;
}

function mostrarToast(mensaje) {
    referencias.toast.hidden = false;
    referencias.toast.textContent = mensaje;
    clearTimeout(mostrarToast.timer);
    mostrarToast.timer = setTimeout(() => {
        referencias.toast.hidden = true;
    }, 2600);
}

function formatearFecha(valor) {
    if (!valor) {
        return "";
    }
    const fecha = new Date(valor);
    if (Number.isNaN(fecha.getTime())) {
        return valor;
    }
    const dia = String(fecha.getDate()).padStart(2, "0");
    const mes = String(fecha.getMonth() + 1).padStart(2, "0");
    const ano = fecha.getFullYear();
    return `${dia}-${mes}-${ano}`;
}

function construirNombreArchivo() {
    const nombre = (estado.respuestas.nombre || "jugador").toLowerCase().replace(/\s+/g, "-");
    const apellido = (estado.respuestas.apellido || "figurita").toLowerCase().replace(/\s+/g, "-");
    return `figurita-${nombre}-${apellido}.png`;
}

function convertirDataUrlEnArchivo(dataUrl, nombreArchivo) {
    return fetch(dataUrl)
        .then((respuesta) => respuesta.blob())
        .then((blob) => new File([blob], nombreArchivo, { type: "image/png" }));
}

function cargarImagen(origen) {
    return new Promise((resolver, rechazar) => {
        const imagen = new Image();
        imagen.onload = () => resolver(imagen);
        imagen.onerror = () => rechazar(new Error(`No se pudo cargar ${origen}`));
        imagen.src = origen;
    });
}
