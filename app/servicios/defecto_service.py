from app.modelos import Defecto
from app.base_datos import db
from config.constantes import EstadoDefectoEnum, PrioridadEnum


class DefectoService:
    @staticmethod
    def crear_defecto(titulo: str, descripcion: str, caso_prueba_id: int, reportado_por_id: int, **kwargs) -> Defecto:
        defecto = Defecto(
            titulo=titulo,
            descripcion=descripcion,
            pasos_reproduccion=kwargs.get('pasos_reproduccion', ''),
            resultado_esperado=kwargs.get('resultado_esperado', ''),
            resultado_actual=kwargs.get('resultado_actual', ''),
            prioridad=kwargs.get('prioridad', PrioridadEnum.MEDIA),
            estado=EstadoDefectoEnum.NUEVO,
            caso_prueba_id=caso_prueba_id,
            reportado_por_id=reportado_por_id,
            asignado_a_id=kwargs.get('asignado_a_id')
        )
        db.session.add(defecto)
        db.session.commit()
        return defecto

    @staticmethod
    def obtener_defectos_abiertos() -> list[Defecto]:
        return Defecto.query.filter(
            Defecto.estado.in_([EstadoDefectoEnum.NUEVO, EstadoDefectoEnum.REABIERTO])
        ).all()

    @staticmethod
    def obtener_defectos_por_usuario(usuario_id: int) -> list[Defecto]:
        return Defecto.query.filter_by(asignado_a_id=usuario_id).all()

    @staticmethod
    def actualizar_estado_defecto(defecto_id: int, nuevo_estado: EstadoDefectoEnum) -> bool:
        defecto = Defecto.query.get(defecto_id)
        if defecto and defecto.puede_cambiar_a(nuevo_estado):
            defecto.estado = nuevo_estado
            db.session.commit()
            return True
        return False

    @staticmethod
    def asignar_defecto(defecto_id: int, usuario_id: int) -> bool:
        defecto = Defecto.query.get(defecto_id)
        if defecto:
            defecto.asignado_a_id = usuario_id
            db.session.commit()
            return True
        return False

    @staticmethod
    def obtener_defectos_por_prioridad(prioridad: PrioridadEnum) -> list[Defecto]:
        return Defecto.query.filter_by(prioridad=prioridad).all()

    @staticmethod
    def contar_defectos_abiertos() -> int:
        return Defecto.query.filter(
            Defecto.estado.in_([EstadoDefectoEnum.NUEVO, EstadoDefectoEnum.REABIERTO])
        ).count()

    @staticmethod
    def eliminar_defecto(defecto_id: int) -> bool:
        defecto = Defecto.query.get(defecto_id)
        if defecto:
            db.session.delete(defecto)
            db.session.commit()
            return True
        return False
