# Guía de Concurrencia y Fan-Out para Luna Builder Fast

Esta referencia documenta el procedimiento para ejecutar múltiples ejecutores en paralelo sin colisiones conceptuales ni desperdicio de tokens.

---

## 1. Principio Fundamental: Contratos Congelados antes de Concurrir

> **Archivos disjuntos NO garantizan trabajo independiente.**

Dos agentes pueden editar archivos separados pero asumir convenciones incompatibles sobre firmas de funciones, esquemas de bases de datos, códigos de estado HTTP o unidades métricas.

Antes de lanzar un Fan-Out:
1. **El Capataz congela la interfaz**: Define explícitamente el contrato compartido (tipos, payloads, nombres y formato de respuesta).
2. **Asignación unívoca de propiedad**: Cada ejecutor recibe propiedad exclusiva de sus archivos fuente y de pruebas.
3. **Aislamiento de recursos compartidos**: Verificar que no compitan por puertos de red, bases de datos efímeras idénticas o bloqueos de gestores de paquetes.

---

## 2. Regla de Rentabilidad del Fan-Out

Lanzar subagentes concurrentes introduce un costo fijo de coordinación, handoff e integración:

$$\text{Rentabilidad} \iff \sum T_i - \max(T_i) > T_{\text{spawn}} + T_{\text{integración}}$$

### Cuándo USAR Fan-Out:
- $\ge 2$ componentes claramente desacoplados tras congelar contratos (ej: componente frontend de filtros + parser backend independiente).
- Tareas cuya duración estimada individual sea $> 60$ segundos.

### Cuándo NO usar Fan-Out (Usar Express o Agrupación en 1 Turno):
- Cambios pequeños ($\le 2$ archivos o $\le 60$ líneas en total): El costo de invocar subagentes supera el tiempo de edición directa.
- Tareas fuertemente secuenciales donde la salida de una es la entrada de otra.
- Modificaciones mecánicas repetitivas: Usar herramienta determinista (`ast-grep`), no LLMs concurrentes.

---

## 3. Plantilla de Invocación en Antigravity (`invoke_subagent`)

En Google Antigravity, múltiples subagentes declarados en la misma llamada se ejecutan de forma concurrente:

```json
{
  "Subagents": [
    {
      "TypeName": "luna-builder-fast",
      "Role": "Module A Implementer",
      "Model": "flash",
      "Workspace": "inherit",
      "Prompt": "G: Implementar validación de esquemas en módulo A\nF:\n- src/modules/a/validator.py\n- tests/test_validator_a.py\nA: python -m unittest tests/test_validator_a.py\nS: Contrato de esquema en docs/specs/schema_v1.json\nE: Medium"
    },
    {
      "TypeName": "luna-builder-fast",
      "Role": "Module B Implementer",
      "Model": "flash",
      "Workspace": "inherit",
      "Prompt": "G: Implementar endpoint de exportación en módulo B\nF:\n- src/modules/b/exporter.py\n- tests/test_exporter_b.py\nA: python -m unittest tests/test_exporter_b.py\nS: Interfaz acordada: export_csv(records: list) -> str\nE: Medium"
    }
  ]
}
```

*Nota sobre Workspace*: Usar `inherit` cuando los archivos y recursos están totalmente desacoplados. Usar `branch` si existe riesgo de tocar dependencias o ramas de compilación intermedias que requieran merges de git limpios.

---

## 4. Integración Incremental y Verificación Cruzada

Al recibir las notificaciones de finalización de los ejecutores:
1. **Auditoría de Frontera (`guard.py`)**: Correr `guard.py check` sobre el árbol unificado para asegurar que ningún agente sobrepasó su lista permitida.
2. **Suite Cruzada**: Ejecutar los tests de integración que verifican la interacción entre los módulos modificados.
3. **Escalado ante conflicto**: Si ocurre un fallo de integración, el Capataz interviene directamente (Modo Express) o despacha un fix focalizado sobre el contrato roto.
