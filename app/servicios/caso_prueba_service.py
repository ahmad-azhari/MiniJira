from app.modelos import CasoPrueba, Resultado
from app.base_datos import db
from config.constantes import TipoTestEnum, EstadoEnum, EstadoResultadoEnum


class CasoPruebaService:
    @staticmethod
    def crear_caso(nombre: str, objetivo: str, usuario_creacion_id: int, **kwargs) -> CasoPrueba:
        caso = CasoPrueba(
            nombre=nombre,
            objetivo=objetivo,
            precondicion=kwargs.get('precondicion', ''),
            descripcion=kwargs.get('descripcion', ''),
            resultado_esperado=kwargs.get('resultado_esperado', ''),
            tipo=kwargs.get('tipo', TipoTestEnum.MANUAL),
            prioridad=kwargs.get('prioridad', None),
            estado=EstadoEnum.NUEVO,
            usuario_creacion_id=usuario_creacion_id
        )
        db.session.add(caso)
        db.session.commit()
        return caso

    @staticmethod
    def obtener_casos_por_ciclo(ciclo_id: int) -> list[CasoPrueba]:
        from app.modelos import CicloPrueba
        ciclo = CicloPrueba.query.get(ciclo_id)
        return ciclo.casos_prueba if ciclo else []

    @staticmethod
    def actualizar_estado_caso(caso_id: int, nuevo_estado: EstadoEnum) -> bool:
        caso = CasoPrueba.query.get(caso_id)
        if caso and caso.puede_cambiar_a(nuevo_estado):
            caso.estado = nuevo_estado
            db.session.commit()
            return True
        return False

    @staticmethod
    def obtener_resultados_caso(caso_id: int) -> list[Resultado]:
        return Resultado.query.filter_by(caso_prueba_id=caso_id).all()

    @staticmethod
    def calcular_tasa_exito_caso(caso_id: int) -> float:
        resultados = CasoPruebaService.obtener_resultados_caso(caso_id)
        if not resultados:
            return 0.0

        pasados = sum(1 for r in resultados if r.estado == EstadoResultadoEnum.PASADO)
        return (pasados / len(resultados)) * 100

    @staticmethod
    def eliminar_caso(caso_id: int) -> bool:
        caso = CasoPrueba.query.get(caso_id)
        if caso:
            db.session.delete(caso)
            db.session.commit()
            return True
        return False
