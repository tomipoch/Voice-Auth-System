# Proyecto Backend - Sistema Biométrico de Voz

## 📁 Estructura del Proyecto

```
Backend/
├── 📂 src/                                 # Código fuente principal
│   ├── 📂 api/                            # Controladores REST y manejo de errores
│   │   ├── auth_controller.py
│   │   ├── admin_controller.py
│   │   ├── challenge_controller.py
│   │   ├── enrollment_controller.py
│   │   ├── phrase_controller.py
│   │   ├── verification_controller_v2.py
│   │   └── error_handlers.py             # Manejadores de errores centralizados
│   ├── 📂 application/                    # Lógica de aplicación y servicios
│   │   ├── enrollment_service.py
│   │   ├── verification_service_v2.py
│   │   ├── services/
│   │   │   └── BiometricValidator.py     # Servicio de validación biométrica
│   │   └── dto/                          # Data Transfer Objects
│   ├── 📂 domain/                        # Lógica de negocio y modelos
│   │   ├── model/
│   │   ├── repositories/                 # Interfaces de repositorios
│   │   └── services/
│   ├── 📂 infrastructure/                # Implementaciones de infraestructura
│   │   ├── biometrics/                   # Adaptadores para el motor biométrico
│   │   ├── config/
│   │   ├── persistence/                  # Implementaciones de repositorios
│   │   └── security/
│   │       └── encryption.py             # Lógica de encriptación
│   └── 📂 shared/                        # Código compartido
│       ├── constants/
│       └── types/
├── 📂 tests/                            # Pruebas
│   ├── 📂 unit/                         # Pruebas unitarias
│   │   └── 📂 application/
│   │       ├── test_enrollment_service.py
│   │       └── 📂 services/
│   │           └── test_BiometricValidator.py
│   └── 📂 integration/                  # Pruebas de integración
├── 📂 scripts/                          # Scripts de utilidad
├── 📂 models/                           # Modelos de machine learning
├── 📂 docs/                             # Documentación
├── 📂 logs/                             # Logs de la aplicación
├── 📂 monitoring/                       # Configuración de monitoreo
└── 📄 Archivos de configuración
    ├── requirements.txt
    ├── requirements-dev.txt
    ├── docker-compose.yml
    ├── Dockerfile
    └── README.md
```

## 📚 Documentación

- `docs/` - Documentación técnica del proyecto.
- `README.md` - Documentación principal del backend.

## 🧪 Testing

- **Pruebas Unitarias**: `tests/unit/`
  - Prueban componentes individuales de la aplicación de forma aislada.
- **Pruebas de Integración**: `tests/integration/`
  - Prueban la interacción entre diferentes componentes del sistema.