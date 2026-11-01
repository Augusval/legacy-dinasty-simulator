from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import random

# ==============================================================================
# ENTIDADES DEL JUEGO (DATA CLASSES)
# ==============================================================================

@dataclass
class Empresa:
    """Representa una empresa fundada por el jugador."""
    nombre: str
    tipo: str  # Consultora, Tech, Inmobiliaria, Banco
    nivel: int = 1
    progreso_nivel: int = 0
    dividendo_base: int = 0
    empleados: int = 10
    escandalo_asociado: int = 0

    def calcular_dividendo_real(self, habilidad_negocios: float) -> int:
        """Calcula el dividendo mensual basado en el nivel y la habilidad."""
        multiplicador = 1 + (self.nivel - 1) * 0.5
        factor_habilidad = habilidad_negocios / 100.0
        return int(self.dividendo_base * multiplicador * max(0.5, factor_habilidad))


@dataclass
class Hijo:
    """Representa a un heredero de la dinastía."""
    nombre: str
    edad: int = 0
    inteligencia: int = field(default_factory=lambda: random.randint(40, 80))
    carisma: int = field(default_factory=lambda: random.randint(40, 80))
    ambicion: int = field(default_factory=lambda: random.randint(40, 80))
    nivel_educacion: str = "Ninguna" # Primaria, Secundaria, Universidad, MBA, Militar
    relacion: int = 50 # 0 a 100

    def calcular_potencial_heredero(self) -> int:
        """Puntaje de 0 a 100 que define qué tan bueno será como sucesor."""
        return (self.inteligencia + self.carisma + self.ambicion) // 3


@dataclass
class Ministro:
    """Representa un miembro del gabinete presidencial."""
    nombre: str
    area: str # Economia, Defensa, Interior, Relaciones Exteriores
    lealtad: int = 50
    eficiencia: int = 50
    corrupcion: int = 10
    faccion_afin: str = "Independiente"
    sueldo_mensual: int = 20000
    tiene_secreto: bool = False


@dataclass
class Medio:
    """Representa un medio de comunicación."""
    nombre: str
    postura: str # Liberal, Progresista, Centrista
    apoyo: int = 50 # -100 a 100

    def get_titular(self, es_positivo: bool) -> str:
        """Genera un titular genérico basado en su postura."""
        if es_positivo:
            return f"{self.nombre} elogia la gestión actual."
        return f"{self.nombre} lanza duras críticas al gobierno."


@dataclass
class Rival:
    """Representa un oponente político."""
    nombre: str
    cargo: str
    poder: int = 30
    secretos: List[str] = field(default_factory=list)
    relacion: int = 20 # -100 a 100

    def generar_secreto(self):
        """Asigna un secreto aleatorio al rival."""
        secretos_posibles = [
            "Tiene cuentas bancarias en el extranjero",
            "Mantuvo un romance con un aliado clave",
            "Recibió financiamiento ilegal en su última campaña",
            "Ocultó información sobre un escándalo de corrupción",
            "Tiene vínculos con el narcotráfico"
        ]
        if not self.secretos:
            self.secretos.append(random.choice(secretos_posibles))


@dataclass
class Ley:
    """Representa una reforma o ley que se puede proponer."""
    nombre: str
    descripcion: str
    costo_politico: int # Cuanta aprobación pública cuesta
    costo_economico: int # Cuanto cuesta al tesoro (puede ser negativo si genera dinero)
    efectos_facciones: Dict[str, int] = field(default_factory=dict)
    requisitos_ideologia: List[str] = field(default_factory=list) # Ej: ["Liberal", "Conservador"]


# ==============================================================================
# FÁBRICAS DE OBJETOS (Para generar datos aleatorios fácilmente)
# ==============================================================================

NOMBRES_ARGENTINOS = ["Juan", "María", "Carlos", "Ana", "Pedro", "Laura", "Diego", "Sofía", "Martín", "Valentina"]
APELLIDOS_ARGENTINOS = ["González", "Rodríguez", "Gómez", "Fernández", "López", "Martínez", "Sánchez", "Pérez"]

def generar_rival_aleatorio(cargo: str = "Diputado") -> Rival:
    nombre = f"{random.choice(NOMBRES_ARGENTINOS)} {random.choice(APELLIDOS_ARGENTINOS)}"
    rival = Rival(nombre=nombre, cargo=cargo, poder=random.randint(20, 60))
    rival.generar_secreto()
    return rival

def generar_ministro_aleatorio(area: str) -> Ministro:
    nombre = f"{random.choice(NOMBRES_ARGENTINOS)} {random.choice(APELLIDOS_ARGENTINOS)}"
    facciones = ["Militares", "Sindicatos", "Iglesia", "Empresarios", "Independiente"]
    return Ministro(
        nombre=nombre, 
        area=area, 
        eficiencia=random.randint(30, 90),
        corrupcion=random.randint(0, 50),
        faccion_afin=random.choice(facciones)
    )