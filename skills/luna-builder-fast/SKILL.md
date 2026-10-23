---
name: luna-builder-fast
description: "Protocolo de ultra-velocidad para Google Antigravity enfocado en minimizar el TTVD (Time to Verified Delivery) mediante bypass de burocracia, parches mínimos O(Δ), ejecución determinista y concurrencia selectiva."
---

# Luna Builder Fast para Google Antigravity

Usa esta skill para completar tareas y proyectos con la **máxima velocidad técnica observable**, eliminando turnos conversacionales innecesarios, reescrituras redundantes y esperas de coordinación ociosas, manteniendo una verificación rigurosa y honesta.

---

## 1. La Meta Irrenunciable: TTVD (Time to Verified Delivery)

> **TTVD**: Tiempo de reloj de pared (*wall-clock*) transcurrido desde la asignación hasta que una **suite de aceptación independiente pasa limpiamente sobre el código integrado**.

- Un cierre rápido pero con errores o pruebas falsas **no es velocidad**, genera retrabajo.
- Un estado `parcial` se registra y no computa como éxito rápido.
- Toda medición de tiempo considera la espera real del usuario, no la suma de tiempos de subagentes.

---

## 2. Matriz de Decisión de Modos (Sin Deliberación Ociosa)

Evalúa la tarea en este orden estricto para seleccionar el modo de ejecución:

| Condición | Modo Asignado | Mecánica Operativa |
| :--- | :--- | :--- |
| $\le 2$ archivos y $\le 60$ líneas, contexto ya en memoria | **Express** | El propio Capataz edita directamente con `edit_file` y corre `run_checks.py`. Cero turnos de subagente. |
| Cambio mecánico/sintáctico en N archivos (rename, imports) | **Codemod** | Herramienta determinista (`ast-grep --rewrite` o script Python). Cero tokens de LLM consumidos. |
| 1 tarea que requiere lógica o implementación no trivial | **Fast** | 1 subagente `luna-builder-fast` (Flash) con contrato comprimido y esfuerzo cognitivo escalonado. |
| $\ge 2$ componentes independientes con contratos congelables | **Fan-Out** | N subagentes lanzados simultáneamente en un único bloque `invoke_subagent`, seguidos de integración y suite cruzada. |
| Tarea de alta varianza o rezagada sin progreso | **Race** (Opt-in) | Lanzar 2 enfoques en paralelo en worktrees aislados; el primero que pase el test gana y cancela al otro. |

---

## 3. El Contrato Comprimido

El Capataz despacha cada tarea atómica utilizando este formato de 5 líneas de alta densidad de información:

```text
G: [Objetivo observable y verificable en una frase]
F: [Lista cerrada de archivos permitidos para edición o creación]
A: [Comando exacto de aceptación independiente]
S: [Pistas, contexto o fragmentos de código conocidos (evita exploración repetida)]
E: [Nivel de esfuerzo asignado: Low | Medium | High]
```

### Reglas de Asignación de Esfuerzo (E)
- **Low**: Modificaciones mecánicas, configuración simple, firmas de funciones directas.
- **Medium** (Default estándar): Nuevos métodos, adaptación de parsers, tests unitarios, lógica de negocio local.
- **High**: Algoritmos complejos con restricciones sutiles, transformaciones matemáticas, sincronización concurrente.

---

## 4. Auditoría de Frontera Determinista (`guard.py`)

No confíes en que el modelo se mantenga en su frontera por autodisciplina; audítalo con herramientas deterministas:

1. **Tomar baseline antes de escribir**:
   ```bash
   python "$HOME/.gemini/config/plugins/luna-builder-fast/skills/luna-builder-fast/scripts/guard.py" snapshot --file .luna/baseline.json
   ```
2. **Auditar al finalizar la tarea**:
   ```bash
   python "$HOME/.gemini/config/plugins/luna-builder-fast/skills/luna-builder-fast/scripts/guard.py" check --allow "ruta/archivo1.py" "ruta/archivo2.py" --snapshot .luna/baseline.json
   ```
   *El script verifica archivos staged, unstaged, untracked, borrados y renombrados respecto al snapshot inicial. Devuelve exit code 0 solo si todos los cambios están dentro de la lista permitida.*

---

## 5. Ejecución Segura de Comprobaciones (`run_checks.py`)

Evita concatenaciones de comandos como `&&` (incompatibles con PowerShell 5.1). Usa el runner determinista:

```bash
python "$HOME/.gemini/config/plugins/luna-builder-fast/skills/luna-builder-fast/scripts/run_checks.py" -c "Lint:python -m flake8 src/" -c "Tests:pytest tests/test_core.py" --guard-allow "src/core.py" "tests/test_core.py" --guard-snapshot .luna/baseline.json
```
- Archiva logs detallados completos en `.luna/runs/<run_id>/`.
- Muestra en terminal solo un extracto observable de las líneas relevantes en caso de fallo.
- Devuelve exit code 0 únicamente si **todos** los checks y el guard pasaron exitosamente.

---

## 6. Escalado por Causa ante Fallos (Regla de 2 Intentos)

Si un check de aceptación falla, analiza el error:
> **Tras 2 intentos sin progreso observable, DETÉN repeticiones idénticas y escala según la causa raíz:**

1. **Fallo de Implementación** (Aserción falla, error de tipos, lógica incorrecta):
   - Escalar el esfuerzo cognitivo del modelo ejecutor (de Low -> Medium, o Medium -> High).
   - Inyectar el extracto del traceback guardado en el log de `run_checks.py`.
2. **Fallo de Entorno** (`ModuleNotFound`, error de permisos, versión de runtime incorrecta):
   - No subas el esfuerzo del LLM (no resolverá una falta de dependencias). Ejecuta la instalación o corrección ambiental (`uv pip install`, etc.).
3. **Contrato Insuficiente o Contradictorio** (Requisitos en conflicto con el test):
   - Detén la implementación y redefine el contrato `G/F/A` con especificaciones unívocas.
4. **Partición de Tarea Deficiente** (Se requieren cambios fuera de la lista permitida para funcionar):
   - Amplía explícitamente la lista `F` o fusiona la tarea con su módulo dependiente.

---

## 7. Reporte de Cierre Sintético (≤ 5 Líneas)

El ejecutor reporta su entrega estrictamente con este formato:

```markdown
- **Archivos**: [ruta/al/archivo (modificado|creado)]
- **Cambio**: [Resumen conciso del parche aplicado]
- **Verificación**: [Comando de aceptación -> PASS / FAIL / NO_EJECUTADO]
- **Supuestos/Bloqueos**: [Ninguno | Supuesto técnico adoptado | Detalle del bloqueo]
- **Estado**: [Cumplido | Parcial | No verificado]
```
