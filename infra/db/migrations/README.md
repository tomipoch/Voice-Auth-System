# Migraciones

Cada cambio de esquema posterior al baseline (`infra/db/init.sql`) va en un archivo
`NNN_descripcion.sql` con numeración secuencial única (001, 002, ...).

Reglas:

- El runner `infra/db/apply_migrations.py` aplica los archivos en orden lexicográfico
  y registra cada uno en `schema_migrations` con su checksum SHA-256.
- Las migraciones son forward-only: no se editan una vez aplicadas (el runner lo detecta
  y falla). Para revertir, se escribe una migración nueva.
- Cada migración debe ser idempotente cuando tenga sentido (`IF NOT EXISTS`,
  `ON CONFLICT ... DO NOTHING`).
- `legacy/` contiene los scripts ad-hoc anteriores (sin runner); su contenido ya está
  consolidado en `init.sql`. No moverlos de vuelta.

Aplicar:

    python infra/db/apply_migrations.py            # aplica pendientes
    python infra/db/apply_migrations.py --dry-run  # solo muestra qué aplicaría
