from datetime import datetime
from app.base_datos import db
from config.constantes import EstadoEnum


class CicloPrueba(db.Model):
    __tablename__ = 'ciclo_prueba'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False, index=True)
    descripcion = db.Column(db.Text)
    estado = db.Column(db.Enum(EstadoEnum), default=EstadoEnum.NUEVO)

    fecha_inicio = db.Column(db.DateTime, nullable=True)
    fecha_fin = db.Column(db.DateTime, nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    casos_prueba = db.relationship(
        'CasoPrueba',
        secondary='caso_prueba_ciclo',
        back_populates='ciclos_prueba'
    )

    epicas = db.relationship(
        'Epica',
        secondary='epica_ciclo_prueba',
        back_populates='ciclos_prueba'
    )

    resultados = db.relationship('Resultado', back_populates='ciclo_prueba', lazy=True, cascade='all, delete-orphan')
    historiales = db.relationship('Historial', back_populates='ciclo_prueba', lazy=True)

    TRANSICIONES_VALIDAS = {
        EstadoEnum.NUEVO: [EstadoEnum.EN_PROGRESO],
        EstadoEnum.EN_PROGRESO: [EstadoEnum.PASADO, EstadoEnum.FALLIDO, EstadoEnum.NUEVO],
        EstadoEnum.PASADO: [EstadoEnum.EN_PROGRESO],
        EstadoEnum.FALLIDO: [EstadoEnum.EN_PROGRESO],
        EstadoEnum.TERMINADO: [EstadoEnum.EN_PROGRESO],
    }

    def puede_cambiar_a(self, nuevo_estado):
        transiciones = self.TRANSICIONES_VALIDAS.get(self.estado, [])
        return nuevo_estado in transiciones

    def actualizar_estado_desde_resultados(self):
        from config.constantes import EstadoResultadoEnum, EstadoEnum
        
        if not self.resultados:
            return
        
        resultados_por_caso = {}
        for res in self.resultados:
            if res.caso_prueba_id not in resultados_por_caso or res.fecha_creacion > resultados_por_caso[res.caso_prueba_id].fecha_creacion:
                resultados_por_caso[res.caso_prueba_id] = res
        
        if not resultados_por_caso:
            return
        
        todos_tienen_resultados = len(resultados_por_caso) == len(self.casos_prueba)
        
        if todos_tienen_resultados:
            todos_pasaron = all(res.estado == EstadoResultadoEnum.PASADO for res in resultados_por_caso.values())
            
            if todos_pasaron:
                if self.puede_cambiar_a(EstadoEnum.PASADO):
                    self.estado = EstadoEnum.PASADO
            else:
                if self.puede_cambiar_a(EstadoEnum.FALLIDO):
                    self.estado = EstadoEnum.FALLIDO
        elif self.estado == EstadoEnum.NUEVO:
            if self.puede_cambiar_a(EstadoEnum.EN_PROGRESO):
                self.estado = EstadoEnum.EN_PROGRESO

    def tiene_pruebas_automatizadas(self):
        return any(caso.tipo.value == 'automatizado' for caso in self.casos_prueba)

    def tiene_pruebas_manuales(self):
        return any(caso.tipo.value == 'manual' for caso in self.casos_prueba)

    def es_solo_manual(self):
        return all(caso.tipo.value == 'manual' for caso in self.casos_prueba)

    def __repr__(self):
        return f'<CicloPrueba {self.nombre}>'
