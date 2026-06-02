# Mini Jira - Sistema de Gestión de Pruebas

Sistema completo de gestión de pruebas de software construido con Flask y SQLAlchemy, con integración con Jenkins para ejecución automatizada de pruebas.

## 📋 Características

- **Gestión de Proyectos**: Crear y administrar múltiples proyectos
- **Épicas e Historias**: Organizar trabajo en épicas y historias de usuario
- **Casos de Prueba**: Definir y gestionar casos de prueba manuales y automatizados (Gherkin)
- **Ciclos de Prueba**: Agrupar casos en ciclos de prueba
- **Ejecución Automatizada**: Integración con Jenkins para ejecución de pruebas automatizadas
- **Resultados**: Registrar resultados de ejecución de pruebas con logs de Jenkins
- **Defectos**: Reportar y rastrear defectos encontrados
- **Reportes**: Dashboard y reportes de calidad
- **Gestión de Usuarios**: Sistema de roles y permisos (admin, miembro, visitante)

## 🚀 Instalación

### Requisitos Previos
- Docker y Docker Compose
- (Opcional) Python 3.12+ para desarrollo local

### Instalación con Docker (Recomendado)

1. **Clonar el repositorio**
```bash
git clone https://github.com/tu_usuario/Mini-Jira.git
cd Mini-Jira
```

2. **Levantar los contenedores**
```bash
docker compose up -d
```

3. **Inicializar la base de datos**
```bash
docker compose exec app python seed_database.py
```

La aplicación estará disponible en `http://localhost:5000`
Jenkins estará disponible en `http://localhost:8080`

### Instalación Local

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

4. **Inicializar la base de datos**
```bash
python seed_database.py
```

5. **Ejecutar la aplicación**
```bash
python run.py
```

La aplicación estará disponible en `http://localhost:5000`


## 🔐 Sistemas de Seguridad

### Autenticación
- Sesiones Flask con almacenamiento en filesystem
- Contraseñas hasheadas con bcrypt
- CSRF protection en formularios

### Autorización
- Sistema basado en roles (admin, miembro, visitante)
- Decoradores para proteger rutas
- Verificación de permisos en operaciones

### Validación
- Validación de entrada en todas las rutas
- Validación de estado en transiciones
- Checks de integridad relacional

## 🤖 Integración con Jenkins

El sistema incluye integración completa con Jenkins para ejecución automatizada de pruebas:

- **Ejecución de Ciclos**: Ejecuta múltiples casos de prueba automatizados en un ciclo
- **Ejecución Individual**: Ejecuta un solo caso de prueba automatizado
- **Polling en Tiempo Real**: Actualización del estado de ejecución en el frontend
- **Logs de Jenkins**: Descarga y visualización de logs de consola
- **Callbacks**: Jenkins envía resultados automáticamente al backend

### Configuración de Jenkins

Jenkins se ejecuta en un contenedor Docker y se configura automáticamente con:
- Plugins necesarios para ejecución de pruebas
- Certificado SSL para comunicación con el backend
- Pipeline para ejecución de scripts Gherkin con Behave

## 📁 Estructura del Proyecto

```
MiniJira/
├── app/
│   ├── modelos/          # Modelos de SQLAlchemy
│   ├── rutas/            # Blueprints de Flask
│   ├── servicios/        # Lógica de negocio
│   ├── plantillas/       # Templates Jinja2
│   ├── estaticos/        # CSS, JS, imágenes
│   └── app.py            # Factory de la aplicación Flask
├── test_runner/          # Scripts de ejecución de pruebas
├── config/               # Configuración y constantes
├── docker-compose.yml    # Configuración de Docker Compose
├── Dockerfile            # Imagen Docker de la app
├── Dockerfile.jenkins    # Imagen Docker de Jenkins
├── requirements.txt      # Dependencias Python
├── seed_database.py      # Script de inicialización de BD
└── run.py               # Punto de entrada local
```

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

## 🔧 Comandos Útiles

### Docker
```bash
# Levantar contenedores
docker compose up -d

# Ver logs
docker compose logs -f app

# Detener contenedores
docker compose down

# Reconstruir contenedores
docker compose up -d --build

# Ejecutar comando en contenedor
docker compose exec app python seed_database.py
```

### Base de Datos
```bash
# Inicializar base de datos con datos de prueba
python seed_database.py

# Limpiar resultados antiguos
python limpiar_resultados.py
```

## 👥 Usuarios por Defecto

Después de ejecutar `seed_database.py`, se crean los siguientes usuarios:

- **admin/admin123**: Rol admin - Acceso total
- **miembro/miembro123**: Rol miembro - Puede crear y editar
- **visitante/visitante123**: Rol visitante - Solo lectura

## 🤝 Contribuir

1. Fork el repositorio
2. Crear rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📜 Licencia

Distribuido bajo licencia MIT. Ver `LICENSE` para más información.

## 📧 Contacto

Autor: Ahmad El Azhari  
Email: ahmadk18elazhari@gmail.com
