# Sistema de Guardias - Aplicación Flask

Aplicación web para la gestión de turnos de guardia con exportación a Excel.

## 📁 Estructura del Proyecto

```
guardias/
├── app.py                      # Punto de entrada principal (Factory Pattern)
├── requirements.txt            # Dependencias del proyecto
├── README.md                   # Este archivo
│
├── models/                     # Capa de Modelos
│   ├── __init__.py
│   └── models.py               # Modelos SQLAlchemy (Persona, Guardia, Novedad, etc.)
│
├── services/                   # Capa de Servicios (Lógica de Negocio)
│   ├── __init__.py
│   ├── consultas.py            # Servicios de consulta (lectura)
│   ├── guardias_service.py     # Lógica de generación de guardias
│   └── excel_service.py        # Exportación a Excel
│
├── routes/                     # Capa de Rutas API (Blueprints)
│   ├── __init__.py
│   ├── personas_routes.py      # API /api/personas
│   ├── guardias_routes.py      # API /api/guardias
│   ├── novedades_routes.py     # API /api/novedades
│   └── export_routes.py        # API /api/exportar, /api/acumulados
│
├── static/                     # Archivos Estáticos
│   ├── css/
│   │   └── styles.css          # Estilos personalizados
│   └── js/
│       ├── calendario.js       # Módulo de calendario
│       ├── personas.js         # Módulo de personas
│       ├── novedades.js        # Módulo de novedades
│       ├── reasignar.js        # Módulo de reasignación
│       ├── importar.js         # Módulo de importación manual
│       └── acumulados.js       # Módulo de acumulados
│
└── templates/                  # Plantillas HTML
    └── index.html              # Página principal
```

## 🏗️ Arquitectura

### Patrón MVC Modificado
- **Model**: `models/` - Modelos de base de datos
- **View**: `templates/` - Plantillas HTML + `static/` - CSS/JS
- **Controller**: `routes/` + `services/` - Rutas API y lógica de negocio

### Factory Pattern
```python
def create_app():
    """Factory de aplicación"""
    app = Flask(__name__)
    # Configuración
    db.init_app(app)
    app.register_blueprint(...)
    return app
```

### Módulos JavaScript (Patrón Module)
```javascript
const CalendarioModule = (function() {
    // Private
    let fechaReasignar = null;
    
    // Public
    return {
        init,
        cargarCalendario,
        generarGuardias,
        exportarExcel
    };
})();
```

## 🚀 Instalación

```bash
pip install -r requirements.txt
python app.py
```

Acceder a: http://localhost:5050

## 📝 Endpoints API

### Personas
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | /api/personas | Listar personas |
| POST | /api/personas | Crear persona |
| PUT | /api/personas/<id> | Actualizar persona |
| DELETE | /api/personas/<id> | Eliminar persona |

### Guardias
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | /api/guardias/generar | Generar mes completo |
| GET | /api/guardias/<mes>/<anio> | Obtener guardias del mes |
| POST | /api/guardias/reasignar | Reasignar manualmente |
| POST | /api/guardias/reasignar-random | Reasignar aleatoriamente |
| POST | /api/guardias/asignar | Asignar día específico |

### Novedades
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | /api/novedades | Listar novedades |
| POST | /api/novedades | Crear novedad |
| DELETE | /api/novedades/<id> | Eliminar novedad |

### Exportación
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | /api/exportar/<mes>/<anio> | Descargar Excel |
| GET | /api/acumulados | Ver acumulados |

## 🎯 Características

- ✅ Generación automática balanceada (2-3 guardias/mes por persona)
- ✅ Reasignación manual y aleatoria
- ✅ Importación manual día por día
- ✅ Exportación a Excel con resumen
- ✅ Gestión de novedades (vacaciones, bajas)
- ✅ Sistema de acumulados entre meses (compensa exceso/falta)
- ✅ Rotación equitativa de Retén
- ✅ Calendario visual interactivo
- ✅ Regla especial: misma persona en 24, 25 y 31 de diciembre
- ✅ Restricción: no repetir persona en Navidad (25/12) y Año Nuevo (01/01)

## 🧪 Test de balanceo (por año)

Para probar el balanceo de guardias en un año determinado:

```bash
python test_balanceo.py --anio 2026
```

Esto:

1. Limpia guardias + acumulados
2. Genera mes a mes con balanceo
3. Imprime un resumen anual con el reparto por persona

## 📊 Excel Exportado

El Excel incluye dos hojas:

1. **Guardias del Mes**: Fecha, Día, Mes, Informático de Guardia, Retén
2. **Resumen Retén**: Estadísticas por persona (Retén, Guardias, Total)

## 🔧 Mantenimiento

### Agregar nueva ruta API
1. Crear archivo en `routes/nueva_ruta.py`
2. Definir Blueprint
3. Registrar en `routes/__init__.py`
4. Registrar en `app.py`

### Agregar nuevo servicio
1. Crear archivo en `services/nuevo_service.py`
2. Importar en `services/__init__.py`

### Agregar nuevo módulo JS
1. Crear archivo en `static/js/nuevo_modulo.js`
2. Seguir patrón Module
3. Incluir en `index.html`

## 📄 Licencia

Uso interno.
