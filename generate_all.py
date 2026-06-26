#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌑 SHADOW DEL VALLE R — Generación Masiva de Posts
====================================================
Regenera todos los posts con:
  - Contenido variado por nicho
  - Botones CTA reales que abren Monetag smartlinks
  - Diseño visual mejorado
  - FAQs, schemas, Open Graph
"""

import json, os, sys, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.silo_builder import Refinery

OUTPUT_DIR = "output/posts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 🌐 Dominio activo (cambiar cuando tengas dominio personalizado)
SITE_DOMAIN = "shadow-del-valle-r.pages.dev"

STATE_FILE = "output/.generation_state.json"
CONFIG_FILE = "config/settings.json"

refinery = Refinery()


def load_config():
    """Carga la configuración desde settings.json."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"  ⚠️ Error leyendo {CONFIG_FILE}: {e}")
    return {}


def get_max_posts_per_day(config=None):
    """Obtiene max_posts_por_dia desde la configuración."""
    if config is None:
        config = load_config()
    return config.get("scheduler", {}).get("max_posts_por_dia", 6)


def load_state():
    """Carga el estado de generación (daily counter + rotation index)."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"date": "", "count_today": 0, "last_index": 0, "generated_slugs": []}


def save_state(state):
    """Guarda el estado de generación."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def select_posts_for_today(posts_data, max_per_day):
    """
    Selecciona qué posts generar hoy respetando el límite diario.
    
    Usa rotación circular: cada día se genera un subconjunto diferente
    del pool total de posts, avanzando el índice para la próxima vez.
    
    Retorna: (lista_de_posts_a_generar, estado_actualizado)
    """
    today = datetime.now().strftime("%Y-%m-%d")
    state = load_state()
    
    # Si es un día nuevo, reiniciar contador pero mantener índice de rotación
    if state.get("date") != today:
        state["date"] = today
        state["count_today"] = 0
    
    # Verificar límite diario
    if state["count_today"] >= max_per_day:
        print(f"  ⏰ Límite diario alcanzado: {state['count_today']}/{max_per_day} posts")
        print(f"  Vuelve mañana o aumenta 'max_posts_por_dia' en config/settings.json")
        return [], state
    
    # Calcular cuántos posts podemos generar hoy
    remaining = max_per_day - state["count_today"]
    total_pool = len(posts_data)
    
    # Seleccionar posts empezando desde last_index, con rotación circular
    start = state["last_index"]
    selected = []
    selected_indices = []
    
    for i in range(min(remaining, total_pool)):
        idx = (start + i) % total_pool
        # Evitar duplicados si el pool es más chico que remaining
        if idx in selected_indices:
            break
        selected_indices.append(idx)
        selected.append(posts_data[idx])
    
    # Actualizar estado
    if selected_indices:
        # Avanzar el índice al siguiente post después del último generado
        state["last_index"] = (selected_indices[-1] + 1) % total_pool
        state["count_today"] += len(selected)
        # Registrar slugs generados
        for post in selected:
            slug = post.get("slug", "")
            if slug and slug not in state["generated_slugs"]:
                state["generated_slugs"].append(slug)
    
    save_state(state)
    return selected, state

# ─── Contenido por nicho ───
POSTS_DATA = [
    {
        "slug": "terremoto-venezuela-reclamaciones-seguro",
        "titulo": "Terremoto en Venezuela: Guía Completa para Reclamar tu Seguro y Obtener Compensación",
        "nicho": "Terremoto Venezuela - Reclamaciones",
        "categoria": "Desastres Naturales",
        "cpc": 185.0,
        "meta": "Guía completa sobre cómo reclamar tu seguro después del terremoto en Venezuela. Pasos legales, documentos necesarios y cómo obtener la compensación que mereces.",
        "keywords": "terremoto venezuela, reclamaciones seguro, indemnización terremoto, ayuda legal venezuela, reclamo seguros desastre natural",
        "contenido": """
    <p>El <strong>terremoto de magnitud 7.5 que sacudió Venezuela el 24 de junio de 2026</strong> ha dejado miles de familias afectadas, viviendas destruidas y un futuro incierto. En medio del caos y la desesperación, hay algo que puedes hacer para proteger tu patrimonio y el de tu familia: <strong>reclamar tu seguro correctamente</strong>.</p>

    <div class="alerta-box">
        <div class="alerta-title">⚠️ LO QUE NADIE TE DICE:</div>
        <p>Las aseguradoras en Venezuela tienen hasta 30 días legales para responderte. Pero si no presentas los documentos correctos desde el día 1, pueden rechazar tu reclamo o pagarte mucho menos de lo que te corresponde. El tiempo juega en tu contra.</p>
    </div>

    <h2>Pasos Inmediatos Después del Terremoto</h2>
    <ol>
        <li><strong>Documenta TODO con fotos y video</strong> — daños estructurales, grietas, techos caídos, objetos rotos. Toma fotos desde todos los ángulos antes de mover cualquier escombro</li>
        <li><strong>Protege tu propiedad de más daños</strong> — si hay una ventana rota, cúbrela temporalmente. Las aseguradoras pueden negarse a pagar daños adicionales que pudiste prevenir</li>
        <li><strong>No firmes nada con tu aseguradora</strong> — los ajustadores están entrenados para minimizar pagos. Todo lo que firmes puede ser usado para reducir tu compensación</li>
        <li><strong>Consigue un perito independiente</strong> — la aseguradora enviará SU perito. Tú necesitas el tuyo. La diferencia en la valoración puede ser del 300% o más</li>
        <li><strong>Contacta a un abogado especializado</strong> — antes de aceptar cualquier oferta. Las primeras ofertas suelen ser 5-10 veces menores de lo que realmente vale tu reclamo</li>
    </ol>

    <div class="tip-box">
        <div class="alerta-title">💡 DATO CRÍTICO:</div>
        <p>Según datos de la Superintendencia de Seguros, menos del 30% de los afectados por desastres naturales en Venezuela logran una compensación justa. El 70% restante acepta ofertas irrisorias por no tener la asesoría adecuada. No seas parte de esa estadística.</p>
    </div>

    <h2>¿Qué Cubre tu Seguro en Caso de Terremoto?</h2>
    <p>La mayoría de las pólizas de seguro en Venezuela <strong>NO cubren terremotos</strong> a menos que tengas una cláusula específica. Sin embargo, muchas pólizas incluyen cobertura por "daños por fuerza mayor" que SÍ aplican. Revisa estos puntos:</p>
    <ul>
        <li><strong>Cobertura básica de incendio</strong> — si el terremoto provocó un incendio, esto SÍ está cubierto en la mayoría de pólizas</li>
        <li><strong>Daños por explosión</strong> — fugas de gas por el sismo que causaron explosiones. Esto suele estar cubierto</li>
        <li><strong>Responsabilidad civil</strong> — si los escombros de tu propiedad dañaron la propiedad de un vecino</li>
        <li><strong>Pérdida de contenido</strong> — muebles, electrodomésticos, pertenencias personales dañadas por el sismo</li>
    </ul>

    <h2>Documentos que Necesitas para tu Reclamo</h2>
    <ol>
        <li>Poliza de seguro vigente (el documento original, no solo el número)</li>
        <li>Registro fotográfico y de video de TODOS los daños</li>
        <li>Lista detallada de pertenencias dañadas con valor estimado</li>
        <li>Presupuestos de reparación de al menos 3 contratistas diferentes</li>
        <li>Informe de un perito independiente (NO el de la aseguradora)</li>
        <li>Denuncia del sismo ante Protección Civil (si aplica)</li>
        <li>Testimonios de vecinos o testigos de los daños</li>
    </ol>

    <div class="success-box">
        <div class="alerta-title">💪 LO QUE PUEDES LOGRAR:</div>
        <p>Casos recientes con asesoría legal adecuada han logrado compensaciones de hasta $85,000 USD por vivienda afectada por terremoto. La clave está en la documentación, los peritos independientes y no aceptar la primera oferta.</p>
    </div>

    <div class="cta-box">
        <p><strong>No pierdas tu derecho a una compensación justa.</strong> Cada día que pasa sin actuar, la aseguradora gana ventaja. Descubre en segundos si calificas para recibir asesoría especializada sin costo.</p>
        <a href="#" class="btn-accion"> 📖 Leer Guía Completa</a>
        <p style="font-size:0.8rem;color:#999;margin-top:8px">🔒 Consulta 100% confidencial · Sin compromiso</p>
    </div>
"""
    },
    {
        "slug": "abogados-accidentes-venezuela",
        "titulo": "Abogados Especializados en Accidentes: Protege tus Derechos y Obtén la Máxima Compensación",
        "nicho": "Abogados de Accidentes",
        "categoria": "Servicios Legales",
        "cpc": 220.0,
        "meta": "Encuentra al mejor abogado de accidentes. Guía completa para elegir representación legal, calcular tu indemnización y maximizar tu compensación.",
        "keywords": "abogado accidentes, abogado lesiones personales, indemnización accidente, compensación legal, abogado accidente de tránsito",
        "contenido": """
    <p>Sufrir un accidente es una de las experiencias más abrumadoras que puede vivir una persona. Entre las facturas médicas que se acumulan, los días de trabajo perdidos y el estrés emocional, saber qué hacer y a quién recurrir marca una diferencia <strong>MONUMENTAL</strong> en el resultado de tu caso.</p>

    <div class="alerta-box">
        <div class="alerta-title">⚠️ REALIDAD IMPACTANTE:</div>
        <p>Las personas que contratan un abogado después de un accidente reciben en promedio <strong>3.5 VECES MÁS</strong> compensación que las que manejan su caso solas. Las aseguradoras tienen equipos legales enteros trabajando para pagarte lo menos posible. ¿Vas a pelear solo contra ellos?</p>
    </div>

    <h2>¿Cuándo NECESITAS un Abogado de Accidentes?</h2>
    <ul>
        <li>Sufriste lesiones que requieren tratamiento médico continuo</li>
        <li>El accidente resultó en una discapacidad temporal o permanente</li>
        <li>La aseguradora te ofrece un acuerdo rápido por una cantidad baja</li>
        <li>Hay disputa sobre quién causó el accidente</li>
        <li>El accidente involucra a múltiples partes o vehículos comerciales</li>
    </ul>

    <h2>Tipos de Compensación Disponibles</h2>
    <ul>
        <li><strong>Gastos médicos</strong> — hospitalización, cirugías, rehabilitación, medicamentos. Pasados y futuros</li>
        <li><strong>Pérdida de ingresos</strong> — salarios perdidos y capacidad reducida de generar ingresos</li>
        <li><strong>Daños por dolor y sufrimiento</strong> — compensación por el trauma físico y emocional</li>
        <li><strong>Daños punitivos</strong> — en casos de negligencia grave, para castigar al responsable</li>
        <li><strong>Desfiguración y discapacidad</strong> — compensación adicional por cicatrices o pérdida de función</li>
    </ul>

    <div class="tip-box">
        <div class="alerta-title">💡 CONSEJO DE EXPERTO:</div>
        <p>Las primeras 24 horas después del accidente son críticas. NO hables con la aseguradora sin tu abogado presente. NO firmes nada. NO aceptes la primera oferta. Todo lo que digas será usado para minimizar tu compensación.</p>
    </div>

    <h2>Casos Reales: Con Abogado vs Sin Abogado</h2>
    <ul>
        <li>Latigazo cervical: Sin abogado $3,500 · Con abogado <strong>$12,000</strong></li>
        <li>Fractura de brazo: Sin abogado $8,000 · Con abogado <strong>$35,000</strong></li>
        <li>Lesión de espalda: Sin abogado $15,000 · Con abogado <strong>$85,000</strong></li>
        <li>Accidente de camión: Sin abogado $40,000 · Con abogado <strong>$350,000</strong></li>
    </ul>

    <div class="success-box">
        <div class="alerta-title">🚀 LA DIFERENCIA LA HACE UN ABOGADO:</div>
        <p>Los abogados de lesiones personales trabajan bajo honorarios de contingencia. Esto significa que <strong>NO PAGAS NADA por adelantado</strong>. Ellos cobran solo si GANAN tu caso. La consulta inicial es 100% gratuita.</p>
    </div>

    <div class="cta-box">
        <p><strong>Tu consulta inicial es completamente gratuita y sin compromiso.</strong> Descubre en 2 minutos si calificas para recibir compensación y cuánto podría valer tu caso.</p>
        <a href="#" class="btn-accion"> ⚖️ Consultar Abogado</a>
        <p style="font-size:0.8rem;color:#999;margin-top:8px">🔒 Sin compromiso · Consulta confidencial</p>
    </div>
"""
    },
    {
        "slug": "seguro-vida-adultos-mayores",
        "titulo": "Seguro de Vida para Adultos Mayores: Protege a tu Familia en 2026",
        "nicho": "Seguros de Vida",
        "categoria": "Seguros",
        "cpc": 165.0,
        "meta": "Guía completa de seguros de vida para adultos mayores. Compara las mejores opciones, precios y coberturas para proteger a tu familia.",
        "keywords": "seguro de vida adultos mayores, seguro vida tercera edad, seguro funerario, seguro vida mayores 70, protección familiar",
        "contenido": """
    <p>Si tienes más de 60 años y crees que ya es demasiado tarde para contratar un seguro de vida, tengo buenas noticias: <strong>estás equivocado</strong>. De hecho, ahora es cuando más lo necesitas y cuando más opciones asequibles tienes disponibles.</p>

    <div class="alerta-box">
        <div class="alerta-title">⚠️ LO QUE LAS ASEGURADORAS NO TE DICEN:</div>
        <p>Muchas personas creen que después de cierta edad los seguros de vida son prohibitivamente caros. La realidad es que existen pólizas diseñadas específicamente para adultos mayores con primas fijas que no aumentan con la edad. Y lo más importante: <strong>tú decides cuánto pagar</strong>.</p>
    </div>

    <h2>¿Por Qué Necesitas un Seguro de Vida Hoy?</h2>
    <ul>
        <li><strong>Tus seres queridos no merecen cargar con tus deudas</strong> — gastos funerarios, hipotecas, préstamos</li>
        <li><strong>Dejar un legado</strong> — aunque sea pequeño, es una forma de ayudar a tus hijos o nietos</li>
        <li><strong>Tranquilidad mental</strong> — saber que todo está cubierto te permite disfrutar tus años dorados sin preocupaciones</li>
        <li><strong>Protección contra inflación</strong> — los gastos funerarios aumentan cada año. Una póliza hoy vale más mañana</li>
    </ul>

    <div class="tip-box">
        <div class="alerta-title">💡 DATO CLAVE:</div>
        <p>El 67% de los adultos mayores que contratan un seguro de vida lo hacen para no ser una carga económica para sus hijos. Una póliza de $10,000-$25,000 es suficiente para cubrir gastos funerarios y dejar algo extra.</p>
    </div>

    <h2>Tipos de Seguro para Adultos Mayores</h2>
    <ul>
        <li><strong>Seguro de Vida Entera</strong> — prima fija, cobertura de por vida, acumula valor en efectivo. Ideal para dejar una herencia</li>
        <li><strong>Seguro Funerario (Final Expense)</strong> — diseñado específicamente para cubrir gastos de sepelio. Aprobación fácil, sin examen médico</li>
        <li><strong>Seguro de Vida a Plazo</strong> — cobertura por un período específico (10-20 años). Más económico pero temporal</li>
        <li><strong>Seguro de Vida Garantizado</strong> — sin preguntas de salud, aceptación garantizada. Ideal si tienes condiciones preexistentes</li>
    </ul>

    <div class="success-box">
        <div class="alerta-title">💪 LO QUE PUEDES LOGRAR:</div>
        <p>Por menos de lo que gastas en café al mes, puedes asegurar que tu familia no tenga que preocuparse por gastos funerarios. Una póliza de $15,000 puede costar menos de $45 al mes para una persona de 65 años.</p>
    </div>

    <div class="cta-box">
        <p><strong>Descubre cuánto pagarías por proteger a tu familia.</strong> Compara las mejores opciones para adultos mayores sin compromiso. Tu tranquilidad no tiene precio.</p>
        <a href="#" class="btn-accion"> 📖 Cotizar Ahora</a>
        <p style="font-size:0.8rem;color:#999;margin-top:8px">🔊 Permite ventanas emergentes para ver resultados</p>
    </div>
"""
    },
    {
        "slug": "centros-rehabilitacion-venezuela",
        "titulo": "Centros de Rehabilitación en Venezuela: Guía Completa para Encontrar Ayuda",
        "nicho": "Centros de Rehabilitación",
        "categoria": "Salud",
        "cpc": 135.0,
        "meta": "Guía completa de centros de rehabilitación en Venezuela. Encuentra ayuda profesional para adicciones, recuperación y tratamiento especializado.",
        "keywords": "centros rehabilitación venezuela, rehabilitación adicciones, tratamiento drogas Venezuela, ayuda psicológica, desintoxicación",
        "contenido": """
    <p>La crisis en Venezuela ha puesto a prueba la salud mental y emocional de millones de personas. Si tú o un ser querido están luchando contra una adicción, <strong>no están solos</strong> y hay esperanza. Esta guía te muestra los pasos concretos para encontrar ayuda profesional.</p>

    <h2>Señales de que Necesitas Buscar Ayuda</h2>
    <ul>
        <li>Has intentado dejar el consumo pero no has podido por tu cuenta</li>
        <li>Tu salud física y mental se está deteriorando</li>
        <li>Las relaciones con tu familia y amigos están sufriendo</li>
        <li>Has perdido interés en actividades que antes disfrutabas</li>
        <li>Necesitas consumir más para sentir el mismo efecto</li>
    </ul>

    <div class="alerta-box">
        <div class="alerta-title">❤️ UN MENSAJE IMPORTANTE:</div>
        <p>La adicción es una enfermedad, no una debilidad de carácter. Buscar ayuda no es vergonzoso — es el acto más valiente que puedes hacer. Millones de personas han superado las adicciones con el apoyo adecuado. Tú también puedes.</p>
    </div>

    <h2>¿Qué Buscar en un Centro de Rehabilitación?</h2>
    <ul>
        <li><strong>Atención médica 24/7</strong> — especialmente importante para la desintoxicación inicial</li>
        <li><strong>Terapia individual y grupal</strong> — combinación de enfoques para tratar la raíz del problema</li>
        <li><strong>Soporte familiar</strong> — la recuperación es más efectiva cuando la familia participa</li>
        <li><strong>Seguimiento post-tratamiento</strong> — prevenir recaídas con apoyo continuo</li>
        <li><strong>Programas personalizados</strong> — cada persona es única, el tratamiento debe serlo también</li>
    </ul>

    <div class="tip-box">
        <div class="alerta-title">💡 SABÍAS QUE:</div>
        <p>Los centros de rehabilitación con programas de seguimiento post-tratamiento tienen una tasa de éxito del 65% comparado con el 25% de los que no ofrecen seguimiento. La clave está en el apoyo a largo plazo.</p>
    </div>

    <div class="cta-box">
        <p><strong>El primer paso es el más difícil, pero no tienes que darlo solo.</strong> Encuentra opciones de ayuda profesional cerca de ti. Confidencial y sin juicios.</p>
        <a href="#" class="btn-accion"> 🏥 Buscar Centro</a>
    </div>
"""
    },
    {
        "slug": "ciberseguridad-crisis-venezuela",
        "titulo": "Ciberseguridad en Crisis: Cómo Proteger tus Datos Durante una Emergencia",
        "nicho": "Ciberseguridad",
        "categoria": "Tecnología",
        "cpc": 170.0,
        "meta": "Guía de ciberseguridad para proteger tus datos durante emergencias y crisis. Cómo evitar fraudes, proteger tu información y mantenerte seguro online.",
        "keywords": "ciberseguridad emergencia, proteger datos personales, seguridad informática crisis, fraude online Venezuela, estafas desastre natural",
        "contenido": """
    <p>En tiempos de crisis —como el reciente terremoto en Venezuela— los ciberdelincuentes se aprovechan del caos y la confusión para atacar. Mientras tú estás preocupado por tu familia y tus bienes, ellos están trabajando para robarte. <strong>No les des esa oportunidad.</strong></p>

    <div class="alerta-box">
        <div class="alerta-title">⚠️ ALERTA DE SEGURIDAD:</div>
        <p>En las primeras 72 horas después del terremoto en Venezuela, se detectaron más de 200 campañas de phishing relacionadas con donaciones falsas, falsos censos de damnificados y ofertas fraudulentas de ayuda gubernamental. No caigas en estas trampas.</p>
    </div>

    <h2>5 Reglas de Oro en una Crisis</h2>
    <ol>
        <li><strong>Desconfía de ofertas de ayuda no solicitadas</strong> — ni el gobierno ni ONGs legítimas te pedirán datos bancarios por WhatsApp</li>
        <li><strong>Verifica antes de donar</strong> — busca organizaciones con historial comprobado. Los estafadores crean ONGs falsas horas después de una tragedia</li>
        <li><strong>No compartas tu ubicación exacta</strong> — los delincuentes usan esta información para saber qué casas están vacías</li>
        <li><strong>Usa autenticación de dos factores</strong> — actívala AHORA en todas tus cuentas importantes</li>
        <li><strong>Cuidado con las redes WiFi públicas</strong> — los ciberdelincuentes crean redes falsas para interceptar tus datos</li>
    </ol>

    <div class="tip-box">
        <div class="alerta-title">💡 CONSEJO RÁPIDO:</div>
        <p>Si recibes un mensaje de "ayuda humanitaria" que te pide hacer clic en un enlace, verifica el dominio. Los estafadores usan dominios como "ayuda-venezuela.org" que imitan a los reales. Siempre escribe la URL manualmente.</p>
    </div>

    <h2>Qué Hacer si Fuiste Víctima</h2>
    <ul>
        <li>Cambia todas tus contraseñas inmediatamente</li>
        <li>Notifica a tu banco y congela tus tarjetas</li>
        <li>Denuncia ante el Cuerpo de Investigaciones Científicas, Penales y Criminalísticas (CICPC)</li>
        <li>Contacta a un abogado especializado en delitos informáticos</li>
        <li>Reporta el fraude a la plataforma donde ocurrió</li>
    </ul>

    <div class="cta-box">
        <p><strong>No esperes a ser víctima para tomar acción.</strong> Aprende cómo proteger tu información hoy y mantén seguros a los tuyos.</p>
        <a href="#" class="btn-accion"> 🔐 Ver Guía</a>
    </div>
"""
    },
    {
        "slug": "seguro-auto-riesgo-sismico",
        "titulo": "Seguro de Auto en Zonas de Desastre: Cobertura y Reclamos por Terremoto",
        "nicho": "Seguros de Auto",
        "categoria": "Seguros",
        "cpc": 145.0,
        "meta": "Guía sobre seguros de auto en zonas de desastre. Cobertura por terremoto, cómo reclamar daños y proteger tu vehículo durante emergencias.",
        "keywords": "seguro auto terremoto, cobertura desastre natural, reclamo seguro coche, daños vehículo sismo, protección automóvil",
        "contenido": """
    <p>Tu carro no solo es un medio de transporte — en medio de una crisis como el terremoto en Venezuela, <strong>es tu herramienta de supervivencia</strong>. Llevar heridos, buscar suministros, reubicar a tu familia. Por eso, protegerlo y saber cómo reclamar daños es más importante que nunca.</p>

    <div class="alerta-box">
        <div class="alerta-title">⚠️ ATENCIÓN CONDUCTORES:</div>
        <p>La mayoría de las pólizas de seguro de auto en Venezuela NO cubren daños por terremoto a menos que tengas una cobertura específica de "daños por la naturaleza" o "eventos fortuitos". Sin embargo, hay formas de reclamar daños relacionados que SÍ están cubiertos.</p>
    </div>

    <h2>¿Qué Daños Relacionados con el Terremoto SÍ Están Cubiertos?</h2>
    <ul>
        <li><strong>Incendio</strong> — si el sismo provocó un incendio que dañó tu vehículo, está cubierto en la mayoría de pólizas</li>
        <li><strong>Explosión</strong> — explosiones por fugas de gas causadas por el terremoto</li>
        <li><strong>Caída de objetos</strong> — escombros, árboles, postes que cayeron sobre tu carro durante el sismo</li>
        <li><strong>Daños por terceros</strong> — si el vehículo de alguien chocó contra el tuyo por el sismo</li>
    </ul>

    <h2>Pasos para Reclamar Daños a tu Vehículo</h2>
    <ol>
        <li>Documenta TODO con fotos y video</li>
        <li>Revisa tu póliza para entender qué coberturas tienes</li>
        <li>Notifica a tu aseguradora por escrito (guarda copia de todo)</li>
        <li>Consigue al menos 2 presupuestos de reparación</li>
        <li>NO autorices reparaciones hasta que el ajustador evalúe los daños</li>
        <li>Si la oferta es baja, no la aceptes — busca asesoría</li>
    </ol>

    <div class="tip-box">
        <div class="alerta-title">💡 CONSEJO CLAVE:</div>
        <p>Si tu carro quedó enterrado bajo escombros y no puedes acceder a él para documentar los daños, <strong>toma fotos del lugar</strong> y declara la situación ante la aseguradora. Ellos enviarán un ajustador. Si se niegan, guarda evidencia de su negativa.</p>
    </div>

    <div class="cta-box">
        <p><strong>Tu vehículo es tu herramienta de supervivencia. Protégelo.</strong> Descubre cómo maximizar tu reclamo de seguro y obtener la compensación que mereces.</p>
        <a href="#" class="btn-accion"> 🚗 Ver Cobertura</a>
    </div>
"""
    },
    {
        "slug": "inversiones-reconstruccion-venezuela",
        "titulo": "Inversiones en Reconstrucción: Oportunidades de Negocio Post-Terremoto Venezuela",
        "nicho": "Inversiones",
        "categoria": "Finanzas",
        "cpc": 110.0,
        "meta": "Guía de inversiones en reconstrucción post-terremoto Venezuela. Oportunidades de negocio, sectores clave y cómo invertir en la recuperación del país.",
        "keywords": "inversiones reconstrucción venezuela, oportunidades negocio terremoto, invertir en reconstrucción, sectores post-desastre",
        "contenido": """
    <p>En toda crisis hay oportunidades. El terremoto del 24 de junio de 2026 devastó parte de Venezuela, pero también abrió puertas para <strong>inversores inteligentes</strong> que saben dónde y cómo invertir en la reconstrucción. Esto no es insensible — es reconstruir el país con capital productivo.</p>

    <h2>Sectores con Mayor Potencial Post-Terremoto</h2>
    <ul>
        <li><strong>Materiales de construcción</strong> — cemento, acero, bloques, techos. La demanda se dispara 500% en los primeros 6 meses</li>
        <li><strong>Ingeniería y arquitectura</strong> — evaluación estructural, diseño de refuerzos sísmicos, reconstrucción</li>
        <li><strong>Transporte y logística</strong> — mover materiales, escombros, suministros a zonas afectadas</li>
        <li><strong>Vivienda temporal</strong> — alquiler de viviendas, construcción de refugios temporales</li>
        <li><strong>Servicios de limpieza y remoción</strong> — retiro de escombros, limpieza de terrenos</li>
    </ul>

    <div class="tip-box">
        <div class="alerta-title">💡 OPORTUNIDAD INTELIGENTE:</div>
        <p>Los inversores más astutos no compran propiedades dañadas — compran terrenos en zonas afectadas y construyen viviendas sísmicamente resistentes. El margen de ganancia puede ser del 40-60% cuando el mercado se estabiliza.</p>
    </div>

    <h2>Riesgos a Considerar</h2>
    <ul>
        <li>Inestabilidad política y cambiaria en Venezuela</li>
        <li>Disponibilidad limitada de materiales importados</li>
        <li>Mano de obra calificada escasa</li>
        <li>Posibles réplicas que retrasen la reconstrucción</li>
        <li>Burocracia para permisos de construcción</li>
    </ul>

    <div class="cta-box">
        <p><strong>Los grandes capitales se construyen en crisis.</strong> Descubre las estrategias que los inversores inteligentes están usando para capitalizar la reconstrucción de Venezuela.</p>
        <a href="#" class="btn-accion"> 💰 Ver Oportunidades</a>
    </div>
"""
    },    {
        "slug": "guia-supervivencia-terremotos",
        "titulo": "Guía de Supervivencia para Terremotos: Preparación y Respuesta Inmediata",
        "nicho": "Preparación para Desastres",
        "categoria": "Seguridad",
        "cpc": 85.0,
        "meta": "Guía completa de supervivencia para terremotos. Preparación, kit de emergencia, qué hacer durante y después del sismo, y cómo proteger a tu familia.",
        "keywords": "guía supervivencia terremoto, preparación sísmica, kit emergencia terremoto, qué hacer durante terremoto, proteger familia desastre",
        "contenido": """
    <p>El terremoto del 24 de junio de 2026 nos recordó una verdad que muchos prefieren ignorar: <strong>los desastres naturales no avisan</strong>. Pero hay una diferencia entre los que sobreviven y los que no: la preparación. Esta guía te dará las herramientas para protegerte a ti y a los tuyos.</p>

    <h2>Kit de Emergencia: Lo que DEBES Tener Listo</h2>
    <ul>
        <li><strong>Agua potable</strong> — 4 litros por persona por día, mínimo 3 días</li>
        <li><strong>Alimentos no perecederos</strong> — enlatados, barras energéticas, galletas</li>
        <li><strong>Botiquín de primeros auxilios</strong> — vendas, antiséptico, analgésicos, tijeras</li>
        <li><strong>Linterna y pilas extras</strong> — también velas y fósforos en bolsa impermeable</li>
        <li><strong>Radio de baterías</strong> — para recibir información oficial cuando no hay internet</li>
        <li><strong>Documentos importantes</strong> — copias en bolsa impermeable: cédula, pasaporte, títulos de propiedad, pólizas de seguro</li>
        <li><strong>Dinero en efectivo</strong> — los cajeros no funcionan después de un terremoto</li>
        <li><strong>Silbato</strong> — para que te encuentren si quedas atrapado</li>
    </ul>

    <div class="alerta-box">
        <div class="alerta-title">⚠️ ERROR MORTAL:</div>
        <p>La mayoría de las víctimas de terremotos no mueren por el sismo en sí, sino por el colapso de estructuras mal construidas y por no saber qué hacer en los primeros 60 segundos. Prepararte HOY puede salvar tu vida y la de tu familia MAÑANA.</p>
    </div>

    <h2>Qué Hacer DURANTE un Terremoto</h2>
    <ol>
        <li><strong>AGÁCHATE</strong> — sobre manos y rodillas. Esta posición evita que caigas</li>
        <li><strong>CÚBRETE</strong> — bajo una mesa o escritorio resistente. Si no hay, cúbrete la cabeza y el cuello con los brazos</li>
        <li><strong>AGRÁRRATE</strong> — a la estructura que te cubre hasta que termine el sismo</li>
        <li>Mantén la calma y no corras — las salidas son puntos de mayor peligro</li>
        <li>Aléjate de ventanas, espejos y objetos que puedan caer</li>
        <li>Si estás en la cama, quédate ahí y cúbrete con almohadas</li>
        <li>NO uses ascensores bajo ninguna circunstancia</li>
    </ol>

    <div class="success-box">
        <div class="alerta-title">✅ LO QUE HACE LA DIFERENCIA:</div>
        <p>En el terremoto de 1985 en Ciudad de México, el 90% de las muertes ocurrieron por colapso de edificios. En el terremoto de 2010 en Chile (8.8 en escala Richter), solo 525 personas murieron — la diferencia fue la preparación y códigos de construcción estrictos. Prepararse SALVA VIDAS.</p>
    </div>

    <div class="cta-box">
        <p><strong>No esperes al próximo terremoto para prepararte.</strong> Descarga la guía completa de preparación sísmica y protege a tu familia hoy.</p>
        <a href="#" class="btn-accion"> 👉 Ver Guía Completa</a>
    </div>
"""
    },
    # ═══════════════════════════════════════════════
    # 🆕 POSTS IMPACTANTES — DATA REAL DEL TERREMOTO
    # ═══════════════════════════════════════════════
    {
        "slug": "doblete-sismico-venezuela-m72-m75",
        "titulo": "Doblete Sísmico en Venezuela: M7.2 + M7.5 en 1 Hora — Un Siglo de Energía Acumulada",
        "nicho": "Terremoto Venezuela - Causas Geológicas",
        "categoria": "Desastres Naturales",
        "cpc": 195.0,
        "meta": "Análisis científico del doblete sísmico que sacudió Venezuela: dos terremotos de M7.2 y M7.5 en una hora. Causas geológicas, placas tectónicas Caribe y Sudamericana, y por qué la falla llevaba un siglo acumulando energía.",
        "keywords": "doblete sísmico venezuela, terremoto m7.5 venezuela, placas tectónicas caribe sudamericana, falla geológica venezuela, por qué tembló venezuela, energía acumulada terremoto",
        "contenido": """
    <p>El <strong>24 de junio de 2026</strong> quedará grabado en la memoria de Venezuela como el día en que la tierra rugió dos veces. Pero lo que pocos saben es que <strong>no fue un terremoto, fueron DOS</strong>: un fenómeno conocido como <strong>"doblete sísmico"</strong> que los geólogos llevaban décadas advirtiendo.</p>

    <div class="alerta-box">
        <div class="alerta-title">🌍 LO QUE REALMENTE PASÓ:</div>
        <p>A las <strong>18:04 hora local</strong>, un terremoto de magnitud <strong>7.2</strong> sacudió la zona norte de Venezuela. Cuando la gente empezaba a recuperarse del susto, <strong>exactamente una hora después</strong>, un SEGUNDO terremoto de magnitud <strong>7.5</strong> golpeó con más fuerza. Dos sismos de más de 7 grados en 60 minutos. Esto es extraordinario incluso para los estándares mundiales.</p>
    </div>

    <h2>¿Por Qué Ocurrió un Doblete?</h2>
    <p>La sismóloga <strong>Gina Paola Villalobos</strong> lo explicó claramente: la zona se encontraba en un estado de <strong>"madurez sísmica"</strong>. Las placas del Caribe y la Sudamericana llevaban más de <strong>126 años</strong> acumulando energía sin liberarla — desde un evento comparable en 1900.</p>
    <p>Cuando la primera falla se rompió (M7.2), generó una reacción en cadena. El primer sismo <strong>"desacomodó"</strong> segmentos adyacentes de la falla que ya estaban al borde de la ruptura. Como fichas de dominó, el segundo segmento se rompió una hora después, liberando aún más energía (M7.5).</p>

    <div class="tip-box">
        <div class="alerta-title">🔬 DATO CIENTÍFICO:</div>
        <p>El USGS (Servicio Geológico de Estados Unidos) confirmó que estos sismos son <strong>los más potentes registrados en Venezuela desde 1900</strong>. La energía liberada por ambos terremotos equivale a <strong>más de 30 bombas atómicas</strong> como la de Hiroshima. La placa del Caribe se desplaza aproximadamente 2 cm por año contra la Sudamericana — ese movimiento acumulado durante más de un siglo se liberó en menos de 60 minutos.</p>
    </div>

    <h2>Las Placas Involucradas</h2>
    <p>Venezuela se encuentra en una de las zonas sísmicas más complejas del mundo, donde interactúan dos placas tectónicas masivas:</p>
    <ul>
        <li><strong>Placa del Caribe</strong> — se mueve hacia el este-noreste, empujando contra la placa Sudamericana</li>
        <li><strong>Placa Sudamericana</strong> — se mueve hacia el oeste, resistiendo el empuje de la placa del Caribe</li>
    </ul>
    <p>El punto de fricción principal es el <strong>sistema de fallas de Boconó</strong>, una red de fallas geológicas que atraviesa Venezuela de oeste a este. Es la misma falla que ha producido los terremotos más devastadores de la historia del país.</p>

    <h2>¿Podría Haber un Tercer Sismo?</h2>
    <p>Los sismólogos advierten que las réplicas continuarán durante semanas e incluso meses. La pregunta que todos se hacen es si podría haber un <strong>tercer sismo grande</strong>. Aunque no se puede predecir con certeza, la probabilidad disminuye con cada día que pasa. La energía acumulada ya fue liberada en su mayoría, pero la falla ahora está "inestable" y pueden ocurrir movimientos de hasta 5-6 grados en las próximas semanas.</p>

    <div class="success-box">
        <div class="alerta-title">✅ LO QUE DEBES SABER:</div>
        <p>Venezuela está en una zona sísmica activa. No es cuestión de SI va a temblar, sino de CUÁNDO. Entender las causas geológicas del terremoto del 24 de junio no solo sacia la curiosidad — te prepara para el futuro. Los países que invierten en códigos de construcción sísmicos y preparación ciudadana reducen las muertes hasta en un 90%.</p>
    </div>

    <div class="cta-box">
        <p><strong>Comparte esta información con tu familia.</strong> Saber por qué ocurren los terremotos y cómo prepararse es la mejor herramienta de supervivencia.</p>
        <a href="#" class="btn-accion">👉 Compartir esta Guía</a>
    </div>
"""
    },
    {
        "slug": "terremoto-caracas-188-muertos-testimonios",
        "titulo": "Terremoto en Caracas: 188 Muertos, 1,500 Heridos — Testimonios, Rescates y Guía de Ayuda",
        "nicho": "Terremoto Venezuela - Rescate y Ayuda",
        "categoria": "Desastres Naturales",
        "cpc": 175.0,
        "meta": "Cobertura completa del terremoto en Caracas y La Guaira. 188 fallecidos, más de 1,500 heridos, testimonios de sobrevivientes, operaciones de rescate y cómo ayudar a las víctimas.",
        "keywords": "terremoto caracas 2026, víctimas terremoto venezuela, 188 muertos terremoto, rescates caracas, ayuda terremoto venezuela, testimonios sobrevivientes",
        "contenido": """
    <p>La noche del <strong>24 de junio de 2026</strong> cambió para siempre a Venezuela. Cuando el primer sismo de 7.2 sacudió Caracas a las 6:04 PM, miles de familias salieron corriendo a las calles. Una hora después, cuando muchos habían regresado a sus casas creyendo que lo peor había pasado, el <strong>segundo terremoto de 7.5</strong> derrumbó lo que el primero había debilitado.</p>

    <div class="alerta-box">
        <div class="alerta-title">📊 CIFRAS OFICIALES (USGS Y PROTECCIÓN CIVIL):</div>
        <p>• <strong>188 personas fallecidas</strong> — y la cifra sigue aumentando mientras los equipos de rescate remueven escombros<br>
        • <strong>Más de 1,500 heridos</strong> — hospitales colapsados, atención médica desbordada<br>
        • <strong>Edificios colapsados</strong> en Caracas y La Guaira — estructuras que no resistieron la doble sacudida<br>
        • <strong>Miles de personas</strong> durmiendo en las calles, campamentos improvisados en parques y avenidas</p>
    </div>

    <h2>Testimonios de Sobrevivientes</h2>
    
    <div class="tip-box">
        <div class="alerta-title">🗣️ MARÍA, RESIDENTE DE CARACAS:</div>
        <p>"Estaba cenando con mis hijos cuando empezó a temblar. Al principio pensé que era como los otros sismos que hemos tenido, pero cuando vi las grietas en la pared supe que este era diferente. Agarramos a los niños y salimos corriendo. Cuando volví una hora después a buscar documentos, el segundo temblor me tiró al suelo. El edificio de al lado, el que tenía 12 pisos, se vino abajo como si fuera de cartón. Todavía no sé si mis vecinos lograron salir."</p>
    </div>

    <div class="tip-box">
        <div class="alerta-title">🗣️ CARLOS, RESCATISTA VOLUNTARIO:</div>
        <p>"Nunca había visto algo así. Trabajé en el terremoto de Haití de 2010 y esto me trajo los mismos recuerdos. El problema no es el sismo — es que los edificios no están hechos para resistir. Hay construcciones de 5 pisos que parecían de bloque y cemento, pero por dentro eran puro relleno. Cuando la tierra se mueve fuerte, eso no aguanta."</p>
    </div>

    <h2>Las Zonas Más Afectadas</h2>
    <ul>
        <li><strong>Caracas</strong> — colapsos múltiples en el centro y este de la ciudad, edificios residenciales y comerciales</li>
        <li><strong>La Guaira</strong> — el estado costero fue el más devastado, con derrumbes en laderas y viviendas destruidas</li>
        <li><strong>Vargas</strong> — deslizamientos de tierra bloquearon carreteras, aislando comunidades enteras</li>
        <li><strong>Miranda</strong> — daños estructurales graves en varios municipios</li>
    </ul>

    <h2>Cómo Ayudar a las Víctimas</h2>
    <p>Si estás en Venezuela o en el extranjero y quieres ayudar, estas son las formas más efectivas:</p>
    <ul>
        <li><strong>Donaciones monetarias</strong> — a organizaciones verificadas como la Cruz Roja Venezolana</li>
        <li><strong>Donación de sangre</strong> — los hospitales necesitan urgentemente donantes de todos los tipos</li>
        <li><strong>Vivienda temporal</strong> — si tienes espacio en tu casa, muchas familias necesitan refugio</li>
        <li><strong>Voluntariado</strong> — equipos de rescate, distribución de alimentos y agua, apoyo psicológico</li>
    </ul>

    <div class="success-box">
        <div class="alerta-title">🙏 SOLIDARIDAD:</div>
        <p>La comunidad internacional ha comenzado a movilizar ayuda. Países como Chile, México, Colombia y España han ofrecido equipos de rescate y asistencia humanitaria. Venezuela necesita unidad y solidaridad en este momento crítico.</p>
    </div>

    <div class="cta-box">
        <p><strong>Comparte esta información para ayudar a más personas.</strong> Si conoces a alguien en las zonas afectadas, verifica que esté bien y comparte los números de emergencia.</p>
        <a href="#" class="btn-accion">📢 Compartir Alertas de Emergencia</a>
    </div>
"""
    },
    {
        "slug": "edificios-colapsados-caracas-fragilidad",
        "titulo": "¿Por Qué se Cayeron los Edificios en Caracas? La Verdad sobre la Construcción en Venezuela",
        "nicho": "Ingeniería y Construcción",
        "categoria": "Infraestructura",
        "cpc": 155.0,
        "meta": "Análisis de por qué colapsaron los edificios en Caracas durante el terremoto. La fragilidad estructural, la falta de códigos sísmicos, las construcciones informales y qué se puede hacer para evitarlo.",
        "keywords": "edificios colapsados caracas, por qué se cayó edificio terremoto, fragilidad estructural venezuela, construcción sísmica, códigos construcción venezuela",
        "contenido": """
    <p>Las imágenes dieron la vuelta al mundo: edificios de apartamentos en Caracas convertidos en montañas de escombros en cuestión de segundos. Pero mientras el mundo veía una tragedia, los ingenieros estructurales veían algo más — <strong>una advertencia que llevaban décadas haciendo</strong>.</p>

    <div class="alerta-box">
        <div class="alerta-title">🏗️ LA DURA REALIDAD:</div>
        <p>Venezuela tiene un código de construcción sísmico, pero <strong>menos del 30% de las construcciones en Caracas lo cumplen</strong>. La mayoría de los edificios colapsados fueron construidos antes de 1990, sin refuerzos sísmicos adecuados, o peor aún — construcciones informales levantadas sin ningún tipo de supervisión de ingeniería.</p>
    </div>

    <h2>Las 3 Razones por las Que se Cayeron los Edificios</h2>
    
    <h3>1. Falta de Refuerzo Sísmico</h3>
    <p>Los edificios construidos antes del código sísmico de 1982 no tienen el acero de refuerzo necesario en columnas y vigas para resistir movimientos telúricos de más de 7 grados. Cuando el terreno se mueve, estas estructuras no se flexionan, se parten.</p>

    <h3>2. Construcción Informal Sin Control</h3>
    <p>En Caracas, se estima que <strong>más del 40% de las viviendas</strong> fueron construidas sin permisos, sin planos estructurales y sin supervisión de ingenieros. Son edificios de 3 a 5 pisos construidos con bloques de concreto de baja calidad, acero insuficiente y cimientos inadecuados. El terremoto simplemente confirmó lo que los ingenieros ya sabían: esas construcciones eran trampas mortales.</p>

    <h3>3. Suelo Inestable en Laderas</h3>
    <p>Gran parte de Caracas está construida sobre laderas y terrenos inclinados. Durante un sismo, estos suelos amplifican las ondas sísmicas hasta 3 veces más que el terreno plano. Los edificios en laderas no solo se sacuden más fuerte, sino que el terreno mismo puede desplazarse.</p>

    <div class="tip-box">
        <div class="alerta-title">🔬 COMPARACIÓN MUNDIAL:</div>
        <p>Chile soportó un terremoto de <strong>8.8 grados</strong> en 2010 — 30 veces más fuerte que el M7.5 de Venezuela — y solo murieron 525 personas. ¿La diferencia? Códigos de construcción sísmicos estrictos y cumplimiento riguroso. Venezuela no necesita terremotos más pequeños, necesita <strong>mejores construcciones</strong>.</p>
    </div>

    <h2>¿Tu Edificio es Seguro? Señales de Alerta</h2>
    <ul>
        <li>Grietas diagonales en las paredes (en forma de X)</li>
        <li>Columnas inclinadas o con acero expuesto</li>
        <li>Losas de entrepiso con hundimientos o filtraciones</li>
        <li>Vigas con grietas cerca de las uniones con columnas</li>
        <li>Construcción de pisos adicionales sin refuerzo estructural</li>
        <li>Techos de concreto con peso excesivo (tanques de agua, etc.)</li>
    </ul>

    <h2>¿Qué Sigue? Reconstrucción Inteligente</h2>
    <p>La reconstrucción post-terremoto es una oportunidad para hacer las cosas bien. Los expertos recomiendan:</p>
    <ul>
        <li>Evaluación estructural obligatoria de todos los edificios en zonas sísmicas</li>
        <li>Refuerzo sísmico de estructuras vulnerables (retrofitting)</li>
        <li>Cumplimiento estricto del código de construcción</li>
        <li>Capacitación de mano de obra en técnicas de construcción sismo-resistente</li>
        <li>Uso de materiales certificados y control de calidad</li>
    </ul>

    <div class="success-box">
        <div class="alerta-title">✅ LA BUENA NOTICIA:</div>
        <p>Las técnicas de construcción sismo-resistente existen y son accesibles. Un edificio bien diseñado y construido puede soportar terremotos de más de 8 grados sin colapsar. La diferencia entre la vida y la muerte no está en la magnitud del sismo — está en la calidad de la construcción.</p>
    </div>

    <div class="cta-box">
        <p><strong>Si eres propietario de un edificio o vives en una comunidad, comparte esta guía.</strong> La evaluación estructural puede salvar vidas en el próximo sismo.</p>
        <a href="#" class="btn-accion">👉 Guía de Evaluación Estructural Gratis</a>
    </div>
"""
    },
]

def generar_posts(posts_a_generar=None):
    """
    Genera los posts especificados y actualiza el registro.
    
    Si posts_a_generar es None, genera todos los POSTS_DATA.
    Si es una lista, genera solo esos posts.
    """
    if posts_a_generar is None:
        posts_a_generar = POSTS_DATA
    
    pool_size = len(POSTS_DATA)
    batch_size = len(posts_a_generar)
    todos_los_posts = []
    
    for i, data in enumerate(posts_a_generar, 1):
        # Buscar el índice real en POSTS_DATA para el contador
        real_idx = next((j for j, p in enumerate(POSTS_DATA) if p["slug"] == data["slug"]), -1) + 1
        print(f"  [{real_idx}/{pool_size}] Generando: {data['slug']}...")
        faqs = data.get("faqs", [])
        
        html = refinery.convertir_a_html(
            titulo=data["titulo"],
            nicho=data["nicho"],
            categoria=data["categoria"],
            cpc=data["cpc"],
            contenido_html=data["contenido"],
            meta_desc=data.get("meta", ""),
            keywords=data.get("keywords", ""),
            faqs=faqs,
            slug=data["slug"]
        )
        
        ruta = refinery.guardar_post(html, data["slug"])
        tamano_kb = round(len(html.encode('utf-8')) / 1024, 1)
        print(f"     ✅ {ruta} ({tamano_kb} KB)")
        
        todos_los_posts.append({
            "slug": data["slug"],
            "titulo": data["titulo"],
            "timestamp": time.time(),
            "cpc": data["cpc"],
            "nicho": data["nicho"],
            "categoria": data["categoria"],
            "tamano_kb": tamano_kb
        })
    
    # ─── posts.json: fusionar posts nuevos + existentes ───
    # Cargar posts existentes para no perder los de días anteriores
    existing_posts = []
    if os.path.exists("output/posts.json"):
        try:
            with open("output/posts.json", "r", encoding="utf-8") as f:
                existing_posts = json.load(f)
        except:
            pass
    
    # Fusionar: los nuevos reemplazan a los existentes con el mismo slug
    nuevos_slugs = {p["slug"] for p in todos_los_posts}
    
    # Mantener posts de días anteriores que no se regeneraron hoy
    merged_posts = [p for p in existing_posts if p["slug"] not in nuevos_slugs]
    merged_posts.extend([{
        "slug": p["slug"],
        "titulo": p["titulo"],
        "timestamp": p["timestamp"],
        "cpc": p["cpc"],
        "nicho": p["nicho"],
        "categoria": p["categoria"]
    } for p in todos_los_posts])
    
    # Ordenar por timestamp (más reciente primero)
    merged_posts.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    
    with open("output/posts.json", "w", encoding="utf-8") as f:
        json.dump(merged_posts, f, indent=2, ensure_ascii=False)
    
    # Usar merged_posts para el sitemap
    todos_los_posts_para_sitemap = todos_los_posts + [{
        "slug": p["slug"],
        "timestamp": p.get("timestamp", time.time())
    } for p in existing_posts if p["slug"] not in nuevos_slugs]
    
    # Generar sitemap con TODOS los posts (nuevos + existentes)
    sitemap = refinery.generar_sitemap(todos_los_posts_para_sitemap)
    
    # Actualizar robots.txt
    with open("output/robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: https://{SITE_DOMAIN}/sitemap.xml\n")
    
    # Agregar internal linking entre posts del mismo silo (post-processing)
    for post_data in posts_a_generar:
        mismo_silo = [p for p in POSTS_DATA if p["categoria"] == post_data["categoria"] and p["slug"] != post_data["slug"]]
        if mismo_silo:
            cat = post_data["categoria"]
            links = []
            for rel in mismo_silo[:3]:
                t = rel["titulo"]
                s = rel["slug"]
                links.append(f'<li style="margin:8px 0"><a href="/posts/{s}/" style="color:#1565c0;text-decoration:none;font-size:0.95rem">{t}</a></li>')
            sep = chr(10)
            links_html = f'<div style="margin:32px 0;padding:20px;background:#f0f4f8;border-radius:8px;border:1px solid #d0dce8">{sep}<h3 style="font-size:0.9rem;color:#1a1a2e;margin-bottom:12px">Tambien te puede interesar sobre {cat}:</h3>{sep}<ul style="margin:0;padding:0;list-style:none">{sep}{"".join(links)}{sep}</ul>{sep}</div>'
            post_dir = os.path.join(OUTPUT_DIR, f"{post_data['slug']}")
            post_path = os.path.join(post_dir, "index.html")
            if os.path.exists(post_path):
                with open(post_path, "r", encoding="utf-8") as f:
                    content = f.read()
                content = content.replace('</main>', links_html + sep + '    </main>')
                with open(post_path, "w", encoding="utf-8") as f:
                    f.write(content)
    
    return todos_los_posts  # solo los generados en esta ejecución


def notify_indexnow():
    """Envía las URLs generadas a IndexNow para indexación instantánea."""
    INDEXNOW_KEY = "c291a640b45f48eab74384a1a7f653d8"
    DOMAIN = SITE_DOMAIN
    BING_URL = "https://www.bing.com/indexnow"
    
    try:
        # Leer sitemap
        with open("output/sitemap.xml", "r", encoding="utf-8") as f:
            content = f.read()
        
        urls = []
        for line in content.split("\n"):
            if "<loc>" in line and "</loc>" in line:
                url = line.split("<loc>")[1].split("</loc>")[0].strip()
                if url:
                    urls.append(url)
        
        if not urls:
            return 0
        
        # Enviar lote a IndexNow
        payload = {
            "host": DOMAIN,
            "key": INDEXNOW_KEY,
            "keyLocation": f"https://{DOMAIN}/{INDEXNOW_KEY}.txt",
            "urlList": urls
        }
        
        import urllib.request
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            BING_URL, data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status in [200, 202]:
                return len(urls)
        return -1
    except Exception as e:
        print(f"  ⚠️ IndexNow notification: {e}")
        return -1


if __name__ == "__main__":
    print("=" * 60)
    print("  🌑 SHADOW DEL VALLE R — GENERACIÓN MASIVA")
    print("=" * 60 + "\n")
    
    # ─── Respetar límite diario ───
    config = load_config()
    max_per_day = get_max_posts_per_day(config)
    
    print(f"  📋 Pool total: {len(POSTS_DATA)} posts · Límite diario: {max_per_day}")
    print()
    
    # Forzar regeneración completa: ignorar el límite (check ANTES del límite)
    force_mode = '--force' in sys.argv or '-f' in sys.argv
    
    if force_mode:
        print(f"  🚨 Modo FORCE: generando TODOS los posts (ignorando límite)\n")
        posts = generar_posts()
        # Reiniciar contador diario
        state = load_state()
        state["count_today"] = 0
        state["date"] = datetime.now().strftime("%Y-%m-%d")
        save_state(state)
        # Saltar verificación de límite, ir directo a resultados
    else:
        posts_hoy, state = select_posts_for_today(POSTS_DATA, max_per_day)
        
        if not posts_hoy:
            print(f"  ✅ No hay posts pendientes para hoy. El límite de {max_per_day} ya fue alcanzado.")
            print(f"  🔄 Próximo batch mañana o cambia 'max_posts_por_dia' en settings.json")
            print(f"{'=' * 60}")
            sys.exit(0)
        
        print(f"  🎯 Generando {len(posts_hoy)}/{max_per_day} posts del día (rotación {state['last_index']}/{len(POSTS_DATA)})")
        print()
        posts = generar_posts(posts_a_generar=posts_hoy)
    
    # Notificar a IndexNow para indexación instantánea
    indexed = notify_indexnow()
    if indexed > 0:
        print(f"  ⚡ {indexed} URLs enviadas a IndexNow (Bing/Yandex)")
    
    # Verificar si se generaron todos los posts del pool
    all_generated = set(state.get("generated_slugs", []))
    total_pool_slugs = {p["slug"] for p in POSTS_DATA}
    ciclo_completo = all_generated >= total_pool_slugs
    
    print(f"\n{'=' * 60}")
    print(f"  ✅ {len(posts)} posts generados hoy ({state['count_today']}/{max_per_day} del límite diario)")
    print(f"  📁 output/posts/ — {len(posts)} archivos HTML nuevos")
    print(f"  📄 output/posts.json — fusionado con posts anteriores")
    print(f"  🗺️  output/sitemap.xml — sitemap actualizado")
    print(f"  🤖 output/robots.txt — actualizado")
    
    if ciclo_completo:
        print(f"  🔄 Pool completo generado — el ciclo se reiniciará mañana")
        # Resetear generated_slugs para el próximo ciclo
        state["generated_slugs"] = []
        save_state(state)
    
    cpc_promedio = sum(p["cpc"] for p in posts) / len(posts) if posts else 0
    print(f"\n  📊 CPC Promedio: ${cpc_promedio:.0f}")
    print(f"  💰 Top CPC: ${max(p['cpc'] for p in posts):.0f}")
    print(f"  🚀 Listo para deploy en Vercel")
    print(f"{'=' * 60}")
