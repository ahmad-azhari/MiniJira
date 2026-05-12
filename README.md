# Mini Jira - Sistema de Gestión de Pruebas

Sistema completo de gestión de pruebas de software construido con Flask y SQLAlchemy.

## 📋 Características

- **Gestión de Proyectos**: Crear y administrar múltiples proyectos
- **Épicas e Historias**: Organizar trabajo en épicas y historias de usuario
- **Casos de Prueba**: Definir y gestionar casos de prueba manuales y automatizados
- **Ciclos de Prueba**: Agrupar casos en ciclos de prueba
- **Resultados**: Registrar resultados de ejecución de pruebas
- **Defectos**: Reportar y rastrear defectos encontrados
- **Reportes**: Dashboard y reportes de calidad
- **Gestión de Usuarios**: Sistema de roles y permisos

## 🏗️ Estructura del Proyecto

```
Mini-Jira/
├── app/
│   ├── __init__.py
│   ├── app.py                 # Configuración principal de Flask
│   ├── base_datos.py          # Inicialización de SQLAlchemy
│   ├── modelos/
│   │   ├── __init__.py
│   │   ├── usuario.py         # Modelo de Usuario
│   │   ├── rol.py             # Modelo de Rol
│   │   ├── proyecto.py        # Modelo de Proyecto
│   │   ├── epica.py           # Modelo de Épica
│   │   ├── caso_prueba.py     # Modelo de Caso de Prueba
│   │   ├── ciclo_prueba.py    # Modelo de Ciclo de Prueba
│   │   ├── resultado.py       # Modelo de Resultado
│   │   ├── defecto.py         # Modelo de Defecto
│   │   └── historial.py       # Modelo de Historial
│   ├── rutas/
│   │   ├── __init__.py
│   │   ├── auth.py            # Rutas de autenticación
│   │   ├── proyectos.py       # Rutas de proyectos
│   │   ├── epicas.py          # Rutas de épicas
│   │   ├── casos_prueba.py    # Rutas de casos de prueba
│   │   ├── ciclos_prueba.py   # Rutas de ciclos de prueba
│   │   ├── resultados.py      # Rutas de resultados
│   │   ├── defectos.py        # Rutas de defectos
│   │   ├── reportes.py        # Rutas de reportes
│   │   └── usuarios.py        # Rutas de gestión de usuarios
│   ├── servicios/
│   │   ├── __init__.py
│   │   ├── auth_service.py    # Servicio de autenticación
│   │   ├── epica_service.py   # Servicio de épicas
│   │   ├── caso_prueba_service.py  # Servicio de casos
│   │   └── defecto_service.py # Servicio de defectos
│   └── plantillas/            # Templates HTML (por crear)
├── config/
│   ├── __init__.py
│   ├── settings.py            # Configuración según ambiente
│   ├── constantes.py          # Constantes y enumeraciones
│   └── base_datos.py          # Configuración de BD
├── scripts/
│   ├── __init__.py
│   └── init_db.py             # Script para inicializar BD
├── tests/                      # Tests unitarios (por crear)
├── logs/                       # Logs de la aplicación
├── .env.example               # Ejemplo de variables de entorno
├── .gitignore
├── requirements.txt           # Dependencias de Python
├── run.py                     # Punto de entrada de la aplicación
└── README.md
```

## 🚀 Instalación

### Requisitos Previos
- Python 3.9+
- pip
- virtualenv (recomendado)

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/tu_usuario/Mini-Jira.git
cd Mini-Jira
```

2. **Crear entorno virtual**
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus valores
```

5. **Inicializar la base de datos**
```bash
python scripts/init_db.py
```

6. **Ejecutar la aplicación**
```bash
python run.py
```

La aplicación estará disponible en `http://localhost:5000`

## 👤 Credenciales de Prueba

Después de ejecutar `init_db.py`:

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| admin | admin123 | Administrador |
| miembro | miembro123 | Miembro |
| viewer | viewer123 | Viewer |

## 📚 Modelos de Datos

### Usuario
- ID único
- Nombre de usuario (único)
- Email
- Contraseña (hasheada con bcrypt)
- Roles (relación muchos a muchos)
- Activo/Inactivo

### Proyecto
- ID único
- Nombre
- Descripción
- Estado (ACTIVO, PAUSADO, COMPLETADO)
- Usuario creador
- Épicas

### Épica
- ID único
- Nombre
- Tipo (EPIC, STORY, TASK)
- Descripción
- Prioridad (BAJA, MEDIA, ALTA, CRÍTICA)
- Estado (NUEVO, EN_PROGRESO, BLOQUEADO, COMPLETADO)
- Proyecto
- Épica padre (para historias)
- Usuario de creación

### Caso de Prueba
- ID único
- Nombre
- Objetivo
- Precondición
- Descripción
- Resultado esperado
- Tipo (MANUAL, AUTOMATIZADO)
- Prioridad
- Estado
- Usuario de creación

### Ciclo de Prueba
- ID único
- Nombre
- Descripción
- Estado
- Casos de prueba (relación muchos a muchos)

### Resultado
- ID único
- Caso de prueba
- Estado (PASADO, FALLIDO, BLOQUEADO, SALTADO)
- Observaciones
- Usuario de ejecución
- Ciclo de prueba
- Fecha/hora

### Defecto
- ID único
- Título
- Descripción
- Pasos de reproducción
- Resultado esperado
- Resultado actual
- Prioridad
- Estado (NUEVO, CONFIRMADO, ASIGNADO, REABIERTO, RESUELTO, CERRADO)
- Caso de prueba que lo originó
- Usuario que lo reportó
- Usuario asignado
- Fecha/hora

## 🔐 Sistemas de Seguridad

### Autenticación
- Sesiones Flask con almacenamiento en filesystem
- Contraseñas hasheadas con bcrypt
- CSRF protection en formularios

### Autorización
- Sistema basado en roles
- Decoradores para proteger rutas
- Verificación de permisos en operaciones

### Validación
- Validación de entrada en todas las rutas
- Validación de estado en transiciones
- Checks de integridad relacional

## 📊 Endpoints Principales

### Autenticación
- `GET/POST /auth/login` - Login de usuario
- `GET /auth/logout` - Logout

### Proyectos
- `GET /proyectos/` - Listar proyectos
- `GET /proyectos/<id>` - Detalle de proyecto
- `POST /proyectos/nuevo` - Crear proyecto
- `POST /proyectos/<id>/editar` - Editar proyecto
- `POST /proyectos/<id>/eliminar` - Eliminar proyecto

### Épicas
- `GET /epicas/<id>` - Detalle de épica
- `POST /epicas/nuevo/<proyecto_id>` - Crear épica
- `POST /epicas/<id>/historia/nuevo` - Crear historia
- `POST /epicas/<id>/editar` - Editar épica
- `POST /epicas/<id>/eliminar` - Eliminar épica

### Casos de Prueba
- `GET /casos-prueba/` - Listar casos
- `GET /casos-prueba/<id>` - Detalle de caso
- `POST /casos-prueba/nuevo` - Crear caso
- `POST /casos-prueba/<id>/editar` - Editar caso
- `POST /casos-prueba/<id>/eliminar` - Eliminar caso

### Ciclos de Prueba
- `GET /ciclos-prueba/` - Listar ciclos
- `GET /ciclos-prueba/<id>` - Detalle de ciclo
- `POST /ciclos-prueba/nuevo` - Crear ciclo
- `POST /ciclos-prueba/<id>/agregar-caso` - Agregar caso a ciclo
- `POST /ciclos-prueba/<id>/quitar-caso/<caso_id>` - Quitar caso de ciclo

### Resultados
- `GET /resultados/` - Listar resultados
- `GET /resultados/<id>` - Detalle de resultado
- `POST /resultados/nuevo/<caso_id>` - Registrar resultado

### Defectos
- `GET /defectos/` - Listar defectos
- `GET /defectos/<id>` - Detalle de defecto
- `POST /defectos/nuevo/<caso_id>` - Reportar defecto
- `POST /defectos/<id>/editar` - Editar defecto
- `POST /defectos/<id>/eliminar` - Eliminar defecto

### Reportes
- `GET /reportes/dashboard` - Dashboard principal
- `GET /reportes/proyectos` - Reporte de proyectos
- `GET /reportes/calidad` - Reporte de calidad
- `GET /reportes/defectos` - Reporte de defectos

### Usuarios
- `GET /usuarios/` - Listar usuarios (admin)
- `GET /usuarios/<id>` - Perfil de usuario
- `POST /usuarios/nuevo` - Crear usuario (admin)
- `POST /usuarios/<id>/editar` - Editar usuario
- `POST /usuarios/<id>/desactivar` - Desactivar usuario (admin)

## 🧪 Testing

```bash
# Ejecutar tests
python -m pytest

# Con coverage
python -m pytest --cov=app tests/
```

## 📝 Configuración

### Ambientes

La aplicación soporta tres ambientes:

- **development**: Modo debug activado, BD SQLite local
- **testing**: BD en memoria, sin debug
- **production**: Sin debug, requiere BD externa

Cambiar ambiente:
```bash
export FLASK_ENV=production  # Linux/Mac
set FLASK_ENV=production     # Windows
```

## 🤝 Contribuir

1. Fork el repositorio
2. Crear rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📜 Licencia

Distribuido bajo licencia MIT. Ver `LICENSE` para más información.

## 📧 Contacto

Autor: Tu Nombre  
Email: tu.email@ejemplo.com  
Proyecto Link: [https://github.com/tu_usuario/Mini-Jira](https://github.com/tu_usuario/Mini-Jira)

## 🎯 Próximas Mejoras

- [ ] Interfaz web mejorada con Bootstrap/Tailwind
- [ ] Sistema de notificaciones por email
- [ ] Exportación a PDF/Excel
- [ ] Integración con Git
- [ ] API REST completa
- [ ] Búsqueda avanzada
- [ ] Filtros por fecha y estado
- [ ] Gráficos de progreso
- [ ] Comentarios en items
- [ ] Sistema de etiquetas

---

Hecho con ❤️ para testers y QA engineers
