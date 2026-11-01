# Constants de datos del juego LEGACY
# Extraídos de mechanics.py para mantener el código limpio y modular

NOMBRES_PILA = [
    "Martina", "Benicio", "Valentina", "Salvador", "Emma", "Bautista",
    "Catalina", "Fausto", "Alma", "Dante", "Perla", "Nilo",
    "Inés", "Teo", "Julieta", "Bruno"
]

POOL_RIVALES = [
    ("Senador Ortiz", "Senador"),
    ("Gobernadora Vidal", "Gobernadora"),
    ("Diputado Morales", "Diputado"),
    ("Intendente Castro", "Intendente"),
    ("Senadora Ríos", "Senadora"),
    ("Intendenta Fuentes", "Intendenta"),
]

LEYES = [
    {
        "nombre": "Matrimonio Igualitario",
        "afinidad": "Izquierda",
        "efecto": ("opinion_publica", 10), "costo": ("Iglesia", 20)
    },
    {
        "nombre": "Reforma Laboral",
        "afinidad": "Derecha",
        "efecto": ("estabilidad_pais", 10), "costo": ("Sindicatos", 20)
    },
    {
        "nombre": "Impuesto a las Grandes Fortunas",
        "afinidad": "Izquierda",
        "efecto": ("tesoro_nacional", 3000000), "costo": ("Empresarios", 25)
    },
    {
        "nombre": "Baja de Retenciones al Campo",
        "afinidad": "Derecha",
        "efecto": ("produccion_industrial", 10), "costo": ("Sindicatos", 10)
    },
    {
        "nombre": "Ley de Alquileres",
        "afinidad": "Centro",
        "efecto": ("opinion_publica", 8), "costo": ("Empresarios", 15)
    },
    {
        "nombre": "Voto Joven a los 16",
        "afinidad": "Izquierda",
        "efecto": ("reputacion", 8), "costo": ("Iglesia", 10)
    },
    {
        "nombre": "Ley de Medios Digitales",
        "afinidad": "Centro",
        "efecto": ("opinion_publica", 6), "costo": ("Empresarios", 10)
    },
    {
        "nombre": "Reforma Militar Profesional",
        "afinidad": "Derecha",
        "efecto": ("estabilidad_pais", 8), "costo": ("Sindicatos", 10)
    },
    {
        "nombre": "Ley de Educación Bilingüe",
        "afinidad": "Centro",
        "efecto": ("reputacion", 6), "costo": ("Iglesia", 10)
    },
]

MEGAOBRAS = [
    {"nombre": "Tren Bala", "costo": 5000000, "turnos": 12, "efecto": "Industria"},
    {"nombre": "Central Nuclear", "costo": 8000000, "turnos": 24, "efecto": "Inflacion"},
    {"nombre": "Plan de Viviendas", "costo": 3000000, "turnos": 6, "efecto": "Aprobacion"},
    {"nombre": "Subte Federal", "costo": 4000000, "turnos": 10, "efecto": "Aprobacion"},
    {"nombre": "Planta de Litio", "costo": 6000000, "turnos": 18, "efecto": "Industria"},
    {"nombre": "Autopista Federal", "costo": 4500000, "turnos": 9, "efecto": "Industria"},
    {"nombre": "Hospital Central", "costo": 3500000, "turnos": 8, "efecto": "Aprobacion"},
    {"nombre": "Represa Binacional", "costo": 9000000, "turnos": 30, "efecto": "Inflacion"},
    {"nombre": "Parque Eólico Patagónico", "costo": 5500000, "turnos": 14, "efecto": "Industria"},
]

TEMAS_DEBATE = [
    {
        "tema": "Economía",
        "posturas": [
            {"nombre": "Dura", "desc": "Ajuste fiscal agresivo", "efecto": {"Empresarios": 15, "Sindicatos": -15, "opinion_publica": -5}},
            {"nombre": "Moderada", "desc": "Reformas graduales", "efecto": {"Empresarios": 5, "Sindicatos": 5, "opinion_publica": 5}},
            {"nombre": "Blanda", "desc": "Protección social", "efecto": {"Empresarios": -10, "Sindicatos": 15, "opinion_publica": 10}}
        ]
    },
    {
        "tema": "Seguridad",
        "posturas": [
            {"nombre": "Dura", "desc": "Mano dura contra el crimen", "efecto": {"Militares": 15, "opinion_publica": 10, "reputacion": -5}},
            {"nombre": "Moderada", "desc": "Prevención y policía comunitaria", "efecto": {"Militares": 5, "opinion_publica": 5, "reputacion": 5}},
            {"nombre": "Blanda", "desc": "Derechos humanos primero", "efecto": {"Militares": -15, "opinion_publica": -5, "reputacion": 10}}
        ]
    },
    {
        "tema": "Derechos Sociales",
        "posturas": [
            {"nombre": "Conservador", "desc": "Valores tradicionales", "efecto": {"Iglesia": 15, "opinion_publica": -5, "reputacion": -5}},
            {"nombre": "Moderado", "desc": "Equilibrio entre tradición y progreso", "efecto": {"Iglesia": 5, "opinion_publica": 5, "reputacion": 5}},
            {"nombre": "Progresista", "desc": "Ampliación de derechos", "efecto": {"Iglesia": -15, "opinion_publica": 10, "reputacion": 10}}
        ]
    }
]

CRISIS_DECISIONES = {
    "financiera": [
        {
            "turno": 1,
            "desc": "Los bancos están en pánico. ¿Qué medida de emergencia tomás?",
            "opciones": [
                {"texto": "Congelar depósitos", "efecto": {"estabilidad_pais": -15, "tesoro_nacional": 5000000}},
                {"texto": "Inyectar liquidez", "efecto": {"tesoro_nacional": -2000000, "estabilidad_pais": 10}},
                {"texto": "Dejar que el mercado se regule", "efecto": {"estabilidad_pais": -10, "opinion_publica": -10}}
            ]
        },
        {
            "turno": 2,
            "desc": "Complicación: Fuga de capitales masiva. ¿Cómo respondés?",
            "opciones": [
                {"texto": "Control de cambios estricto", "efecto": {"Empresarios": -20, "estabilidad_pais": 5}},
                {"texto": "Aumentar tasas de interés", "efecto": {"inflacion": -5, "Empresarios": -10}},
                {"texto": "Pedir ayuda al FMI", "efecto": {"EE.UU.": 10}}
            ]
        },
        {
            "turno": 3,
            "desc": "Decisión final: ¿Rescate total, parcial o dejar caer?",
            "opciones": [
                {"texto": "Rescate total ($5M)", "efecto": {"tesoro_nacional": -5000000, "aprobacion_publica": 15}},
                {"texto": "Rescate parcial ($2M)", "efecto": {"tesoro_nacional": -2000000, "aprobacion_publica": 5}},
                {"texto": "Dejar caer", "efecto": {"estabilidad_pais": -25, "aprobacion_publica": -20}}
            ]
        }
    ],
    "seguridad": [
        {
            "turno": 1,
            "desc": "Escándalo masivo. ¿Qué haces?",
            "opciones": [
                {"texto": "Soborno", "efecto": {"corrupcion": 20, "dinero_personal": -50000}},
                {"texto": "Aceptar", "efecto": {"corrupcion": 15, "dinero_personal": -50000}},
                {"texto": "Rechazar", "efecto": {"corrupcion": 0, "dinero_personal": 0}}
            ]
        },
        {
            "turno": 2,
            "desc": "Crisis nacional. ¿Qué haces?",
            "opciones": [
                {"texto": "Aceptar", "efecto": {"estabilidad_pais": -15, "aprobacion_publica": 10}},
                {"texto": "Rechazar", "efecto": {"estabilidad_pais": -10, "aprobacion_publica": -10}}
            ]
        }
    ],
    "derechos_sociales": [
        {
            "turno": 1,
            "desc": "Crisis social. ¿Qué haces?",
            "opciones": [
                {"texto": "Apoyo popular", "efecto": {"opinion_publica": 10, "reputacion": 5}},
                {"texto": "Represión", "efecto": {"opinion_publica": -10, "reputacion": -5}}
            ]
        }
    ]
}
