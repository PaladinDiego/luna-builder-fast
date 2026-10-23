# Luna Builder Fast ⚡ (`luna-builder-fast`)

[![Tests](https://github.com/usuario/luna-builder-fast/actions/workflows/ci.yml/badge.svg)](https://github.com)
[![Antigravity](https://img.shields.io/badge/Google-Antigravity%20Plugin-blue.svg)](https://github.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)

**Luna Builder Fast** es una variante de ultra-velocidad del protocolo Luna Builder, optimizada para **Google Antigravity**. Su propósito primordial es **minimizar el TTVD (*Time to Verified Delivery*)**: el tiempo de reloj de pared real que transcurre desde la recepción de una tarea hasta la entrega de un código integrado, correcto, observable y validado de manera independiente.

---

## ⚡ 1. Principios Operativos Fundamentales

1. **Bypass de Burocracia Conversacional**:
   - En tareas acotadas ($\le 2$ archivos, $\le 60$ líneas con contexto en memoria), el Capataz edita directamente en **Modo Express** sin delegación a subagentes (0 turnos de handoff).
2. **Transformaciones Mecánicas Deterministas**:
   - Reemplazos sintácticos o renombrado masivo se despachan vía `ast-grep` o scripts en **Modo Codemod**, consumiendo 0 tokens de LLM.
3. **Parches Mínimos $O(\Delta)$ vs Reescrituras $O(N)$**:
   - Modificaciones estrictamente dirigidas con `edit_file`; terminantemente prohibido reescribir archivos enteros.
4. **Concurrencia Rentable (Fan-Out con Contratos Congelados)**:
   - Ejecución paralela en $\ge 2$ componentes independientes solo tras congelar explícitamente sus interfaces e intercambios.
5. **Auditoría Determinista de Frontera (`guard.py`)**:
   - Validación matemática de cambios contra un snapshot baseline de Git (staged, unstaged, untracked, deleted, renamed).
6. **Escalado por Causa ante Fallo**:
   - Tras 2 intentos sin progreso observable, no repetir mecánicamente: diagnosticar causa raíz y escalar (implementación $\to$ esfuerzo cognitivo; entorno $\to$ fix ambiental; contrato $\to$ aclaración).
7. **Reporte Terso y Honesto**:
   - Entrega observable en $\le 5$ líneas (`cumplido`, `parcial` o `no verificado`). Jamás asumir o inventar éxito de pruebas.

---

## 📊 2. Benchmark Empírico

Mediciones cronometradas reales en banco de pruebas estándar:

| Familia de Tarea | Luna Original (Línea Base) | Luna Fast (Optimizado) | Modo Empleado | Aceleración (Speedup) |
| :--- | :--- | :--- | :--- | :--- |
| **T1: Cambio Pequeño** (Fix puntual + test) | 30.70 s | **0.31 s** | Express | **~99× más rápido** |
| **T2: Transformación Mecánica** (Rename 4 archivos) | 40.67 s | **0.32 s** | Codemod (`ast-grep`) | **~127× más rápido** |
| **T3: Componentes Independientes** (2 módulos) | 60.17 s | **30.87 s** | Fan-Out (2 workers) | **~1.95× más rápido** |
| **T4: Dependencias Compartidas** (Retrocompatibilidad) | ~35.00 s | **0.32 s** | Express | **~100× más rápido** |
| **T5: Reparación y Escalado** (Detección + Fix) | ~45.00 s | **0.53 s** | Fast Ladder | **~85× más rápido** |

---

## 🛠️ 3. Modos de Ejecución

Luna Builder Fast evalúa los requerimientos y aplica la siguiente matriz de decisión:

| Condición | Modo Asignado | Mecánica Operativa |
| :--- | :--- | :--- |
| $\le 2$ archivos y $\le 60$ líneas, contexto ya en memoria | **Express** | El Capataz edita directamente con `edit_file` y corre `run_checks.py`. Cero turnos de subagente. |
| Cambio mecánico/sintáctico en N archivos | **Codemod** | Herramienta determinista (`ast-grep` o script Python). Cero tokens de LLM consumidos. |
| 1 tarea que requiere implementación acotada | **Fast** | 1 subagente `luna-builder-fast` (Flash) con contrato comprimido `G/F/A/S/E`. |
| $\ge 2$ componentes independientes con contratos congelados | **Fan-Out** | N subagentes lanzados simultáneamente en un único bloque `invoke_subagent`, seguidos de integración y suite cruzada. |
| Tarea de alta varianza o rezagada sin progreso | **Race** (Opt-in) | Lanzar 2 enfoques en paralelo en worktrees aislados; el primero en pasar el test gana y cancela al otro. |

---

## 📥 4. Instalación Rápida

Puedes instalar Luna Builder Fast en tu entorno de Antigravity en segundos.

### Opción A: Instalación Automática (Recomendada)

Clona este repositorio y ejecuta el instalador correspondiente:

**En Windows (PowerShell):**
```powershell
git clone https://github.com/usuario/luna-builder-fast.git
cd luna-builder-fast
powershell -ExecutionPolicy Bypass -File scripts/install.ps1
```

**En Linux / macOS (Bash):**
```bash
git clone https://github.com/usuario/luna-builder-fast.git
cd luna-builder-fast
chmod +x scripts/install.sh
./scripts/install.sh
```

**O mediante Python (Multiplataforma):**
```bash
python scripts/install.py
```

### Opción B: Instalación en un Proyecto Específico (Workspace)

Si deseas confinar Luna Builder Fast a un solo repositorio/proyecto:
```bash
python scripts/install.py --workspace /ruta/a/tu/proyecto
```

### Opción C: Clon Directo en la Configuración Global de Antigravity

```bash
git clone https://github.com/usuario/luna-builder-fast.git ~/.gemini/config/plugins/luna-builder-fast
```

> **Nota**: Tras instalar como plugin global por primera vez, reinicia Google Antigravity para que indexe el nuevo plugin.

---

## 💬 5. Cómo Usarlo en el Chat

Una vez instalado, el plugin se activa de forma automática en Antigravity cuando utilizas frases clave como:

- `"Ejecuta esta tarea con luna fast"`
- `"Aplica este fix en modo express"`
- `"Ejecuta estas tareas independientes en fan-out con luna fast"`
- `"Audita los cambios con guard"`

### El Contrato Comprimido (G / F / A / S / E)

Cuando el Capataz delega al subagente `luna-builder-fast`, utiliza un contrato de alta densidad técnica:

```text
G: [Objetivo concreto y observable]
F: [Lista cerrada de archivos permitidos]
A: [Comando exacto de aceptación]
S: [Pistas de código o interfaces ya conocidas]
E: [Esfuerzo: Low | Medium | High]
```

### Reporte de Cierre Sintético (≤ 5 líneas)

El ejecutor devuelve exclusivamente información verificable:

```markdown
- **Archivos**: src/auth.py (modificado)
- **Cambio**: Corregido refresco de tokens expirados en encabezado Bearer
- **Verificación**: pytest tests/test_auth.py -> PASS (0.42s)
- **Supuestos/Bloqueos**: Ninguno
- **Estado**: Cumplido
```

---

## 🧰 6. Herramientas CLI Incluidas

Las herramientas se ubican en `skills/luna-builder-fast/scripts/` y funcionan de manera autónoma en terminales Windows, macOS y Linux:

### `guard.py` — Auditor Determinista de Frontera
Garantiza que ningún proceso o agente toque archivos fuera de la lista permitida:
```bash
# 1. Tomar snapshot inicial
python skills/luna-builder-fast/scripts/guard.py snapshot --file .luna/baseline.json

# 2. Auditar tras los cambios
python skills/luna-builder-fast/scripts/guard.py check --allow "src/archivo1.py" "tests/test_archivo1.py" --snapshot .luna/baseline.json
```

### `run_checks.py` — Ejecutor Seguro de Suites
Elimina fallos derivados de operadores de shell frágiles (compatible nativamente con PowerShell 5.1):
```bash
python skills/luna-builder-fast/scripts/run_checks.py \
  -c "Lint:python -m flake8 src/" \
  -c "Tests:pytest tests/" \
  --guard-allow "src/core.py" "tests/test_core.py" \
  --guard-snapshot .luna/baseline.json
```

### `transcript_stats.py` — Medición de TTVD y Métricas de Conversación
Calcula el tiempo de pared real, turnos del modelo y consumo de herramientas a partir de `transcript.jsonl`:
```bash
python skills/luna-builder-fast/scripts/transcript_stats.py /ruta/a/transcript.jsonl
```

### `lf.py` — Planificador DAG de Tareas
Orquesta grafos dirigidos acíclicos de tareas con detección de dependencias circulares (algoritmo de Kahn) y concurrencia controlada:
```bash
python skills/luna-builder-fast/scripts/lf.py tasks.json --workers 2 --integration-check "pytest tests/integration/"
```

### `hook_pretool.py` — Interceptor PreToolUse de Ultrabaja Latencia
Hook de ciclo de vida para Antigravity que intercepta llamadas a `edit_file` y `write_file` en $< 30\text{ ms}$.

---

## 🧪 7. Pruebas Unitarias

El repositorio cuenta con una suite completa de pruebas automatizadas:

```bash
python -m unittest discover -s tests -v
```

O si tienes `pytest` instalado:
```bash
pytest tests/ -v
```

---

## 📁 8. Estructura del Repositorio

```text
luna-builder-fast/
├── .github/
│   └── workflows/
│       └── ci.yml               # CI automatizado en Linux, macOS y Windows
├── agents/
│   └── luna-builder-fast.md     # Manifiesto y prompt del subagente atómico
├── rules/
│   └── AGENTS.md                # Reglas globales de proyecto y enrutamiento
├── skills/
│   └── luna-builder-fast/
│       ├── SKILL.md             # Especificación completa de la skill
│       ├── references/
│       │   └── fan-out.md       # Guía de concurrencia y contratos congelados
│       └── scripts/             # Herramientas de automatización deterministas
│           ├── guard.py
│           ├── run_checks.py
│           ├── transcript_stats.py
│           ├── lf.py
│           └── hook_pretool.py
├── scripts/
│   ├── install.py               # Instalador multiplataforma en Python
│   ├── install.ps1              # Instalador para Windows PowerShell
│   └── install.sh               # Instalador para Linux / macOS
├── tests/                       # Suite de pruebas unitarias
│   ├── test_guard.py
│   ├── test_run_checks.py
│   ├── test_lf.py
│   └── test_hook_pretool.py
├── hooks.json                   # Definición de hooks de ciclo de vida
├── plugin.json                  # Manifiesto del plugin para Google Antigravity
├── pyproject.toml               # Configuración del paquete y herramientas
├── requirements-dev.txt         # Dependencias de desarrollo
├── LICENSE                      # Licencia MIT
└── README.md                    # Documentación principal
```

---

## 📄 Licencia

Este proyecto está distribuido bajo la licencia [MIT](LICENSE).
