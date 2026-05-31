import enum


class EstadoEnum(str, enum.Enum):
    NUEVO = "nuevo"
    EN_PROGRESO = "en_progreso"
    TERMINADO = "terminado"


class EstadoDefectoEnum(str, enum.Enum):
    ABIERTO = "abierto"
    EN_PROGRESO = "en_progreso"
    CERRADO = "cerrado"


class EstadoResultadoEnum(str, enum.Enum):
    PASADO = "pasado"
    FALLIDO = "fallido"
    BLOQUEADO = "bloqueado"
    EN_PROGRESO = "en_progreso"


class PrioridadEnum(str, enum.Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


class TipoEnum(str, enum.Enum):
    EPIC = "epic"
    STORY = "story"


class TipoTestEnum(str, enum.Enum):
    MANUAL = "manual"
    AUTOMATIZADO = "automatizado"


class RolEnum(str, enum.Enum):
    ADMIN = "admin"
    MIEMBRO = "miembro"
    VIEWER = "viewer"


class EstadoProyectoEnum(str, enum.Enum):
    ACTIVO = "activo"
    EN_PAUSA = "en_pausa"
    CERRADO = "cerrado"


class ModoEjecucionEnum(str, enum.Enum):
    MANUAL = "manual"
    AUTOMATIZADO = "automatizado"


class EstadoEjecucionEnum(str, enum.Enum):
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADO = "completado"
    ERROR = "error"
