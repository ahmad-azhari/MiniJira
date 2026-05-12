from app.modelos import Epica, Proyecto
from app.base_datos import db
from config.constantes import TipoEnum, EstadoEnum


class EpicaService:
    @staticmethod
    def crear_epica(nombre: str, descripcion: str, proyecto_id: int, usuario_creacion_id: int, **kwargs) -> Epica:
        epica = Epica(
            nombre=nombre,
            descripcion=descripcion,
            tipo=TipoEnum.EPIC,
            estado=EstadoEnum.NUEVO,
            proyecto_id=proyecto_id,
            usuario_creacion_id=usuario_creacion_id,
            prioridad=kwargs.get('prioridad', None)
        )
        db.session.add(epica)
        db.session.commit()
        return epica

    @staticmethod
    def crear_historia(nombre: str, descripcion: str, epica_padre_id: int, proyecto_id: int,
                      usuario_creacion_id: int, **kwargs) -> Epica:
        historia = Epica(
            nombre=nombre,
            descripcion=descripcion,
            tipo=TipoEnum.STORY,
            estado=EstadoEnum.NUEVO,
            epica_padre_id=epica_padre_id,
            proyecto_id=proyecto_id,
            usuario_creacion_id=usuario_creacion_id,
            prioridad=kwargs.get('prioridad', None)
        )
        db.session.add(historia)
        db.session.commit()
        return historia

    @staticmethod
    def obtener_epicas_por_proyecto(proyecto_id: int, tipo: TipoEnum = None) -> list[Epica]:
        query = Epica.query.filter_by(proyecto_id=proyecto_id)
        if tipo:
            query = query.filter_by(tipo=tipo)
        return query.all()

    @staticmethod
    def obtener_historias_por_epica(epica_id: int) -> list[Epica]:
        return Epica.query.filter_by(epica_padre_id=epica_id, tipo=TipoEnum.STORY).all()

    @staticmethod
    def actualizar_estado_epica(epica_id: int, nuevo_estado: EstadoEnum) -> bool:
        epica = Epica.query.get(epica_id)
        if epica and epica.puede_cambiar_a(nuevo_estado):
            epica.estado = nuevo_estado
            db.session.commit()
            return True
        return False

    @staticmethod
    def eliminar_epica(epica_id: int) -> bool:
        epica = Epica.query.get(epica_id)
        if epica:
            db.session.delete(epica)
            db.session.commit()
            return True
        return False

    @staticmethod
    def obtener_progreso_epica(epica_id: int) -> dict:
        epica = Epica.query.get(epica_id)
        if not epica:
            return {}

        historias = Epica.query.filter_by(epica_padre_id=epica_id).all()
        if not historias:
            return {'total': 0, 'completadas': 0, 'porcentaje': 0}

        completadas = sum(1 for h in historias if h.estado == EstadoEnum.COMPLETADO)
        total = len(historias)

        return {
            'total': total,
            'completadas': completadas,
            'porcentaje': (completadas / total * 100) if total > 0 else 0
        }
