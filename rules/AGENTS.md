# Reglas de Proyecto: Protocolo Luna Builder Fast para Google Antigravity

## Directiva de Activación Ultra Rápida
Cuando el usuario mencione **"luna fast"**, **"luna-fast"**, **"luna builder fast"** o solicite máxima velocidad de entrega ("ultra fast"):

1. **Meta Única (TTVD)**: Minimizar el tiempo hasta entregar un proyecto correcto y verificado de forma observable, sin inventar trabajo ni dejar reparaciones pendientes.
2. **Tabla de Selección Rápida de Modos**:
   - **Express** (≤2 archivos, ≤60 líneas, contexto en mano): El propio orquestador edita directamente (`edit_file`) sin subagente (0 turnos de handoff).
   - **Codemod** (cambio mecánico repetitivo en N sitios): Ejecución de herramienta determinista (`ast-grep` o script), sin tokens de LLM.
   - **Fast** (1 tarea que requiere implementación acotada): 1 subagente `luna-builder-fast` (Flash) con contrato comprimido `G/F/A/S/E`.
   - **Fan-Out** (≥2 tareas independientes): Contratos congelados previamente; lanzamiento paralelo en un único bloque `invoke_subagent` con verificación de integración final.
3. **Frontera Determinista y Parches O(Δ)**:
   - Prohibido reescribir archivos completos (`O(N)`). Usar reemplazos dirigidos (`edit_file`).
   - La frontera de archivos permitidos es estricta y se audita con `guard.py` mediante baseline de git.
4. **Cero Preguntas Ficticias y Escalado por Causa**:
   - Asumir el default razonable y declararlo en el reporte; solo detenerse por irreversibilidad real (borrado o pérdida de datos).
   - Tras 2 intentos sin progreso, no repetir el mismo enfoque: escalar según la causa (implementación -> capacidad, entorno -> fix ambiental, contrato -> aclarar).
5. **Reporte Terso**: Resumen ≤5 líneas con estado observable: `cumplido`, `parcial` o `no verificado`.
