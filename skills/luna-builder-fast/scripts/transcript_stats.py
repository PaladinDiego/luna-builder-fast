#!/usr/bin/env python3
"""
transcript_stats.py — Telemetría y cálculo de TTVD (Time to Verified Delivery)
a partir de logs de conversación de Antigravity (transcript.jsonl / transcript_full.jsonl).
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path


def parse_iso(ts_str):
    if not ts_str:
        return None
    # Manejar formatos ISO terminados en Z o con offset
    clean = ts_str.replace("Z", "+00:00")
    try:
        return datetime.datetime.fromisoformat(clean)
    except Exception:
        return None


def analyze_transcript(file_path):
    p = Path(file_path)
    if not p.exists():
        print(f"[transcript_stats] Error: Archivo no encontrado: {p}", file=sys.stderr)
        sys.exit(1)

    steps = []
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                steps.append(json.loads(line))
            except Exception:
                continue

    if not steps:
        print("[transcript_stats] Archivo vacío o sin pasos válidos.")
        sys.exit(1)

    timestamps = []
    tool_counts = {}
    model_turns = 0
    user_inputs = 0
    tokens_stats = {
        "input_tokens": 0,
        "output_tokens": 0,
        "thinking_tokens": 0
    }

    for s in steps:
        ts = parse_iso(s.get("created_at"))
        if ts:
            timestamps.append(ts)

        stype = s.get("type", "")
        source = s.get("source", "")

        if stype in ("PLANNER_RESPONSE", "MODEL") or source == "MODEL":
            model_turns += 1

        if stype == "USER_INPUT" or source == "USER_EXPLICIT":
            user_inputs += 1

        for tc in s.get("tool_calls", []):
            name = tc.get("name", "unknown")
            tool_counts[name] = tool_counts.get(name, 0) + 1

        usage = s.get("usage", {})
        if usage:
            tokens_stats["input_tokens"] += usage.get("input_tokens", 0)
            tokens_stats["output_tokens"] += usage.get("output_tokens", 0)
            tokens_stats["thinking_tokens"] += usage.get("thinking_tokens", 0)

    timestamps.sort()
    wall_clock_seconds = 0
    if len(timestamps) >= 2:
        wall_clock_seconds = (timestamps[-1] - timestamps[0]).total_seconds()

    print("=" * 65)
    print("MÉTRICAS DE RENDIMIENTO Y TTVD (transcript_stats.py)")
    print("=" * 65)
    print(f"Archivo analizado: {p.resolve()}")
    print(f"Total de eventos/pasos:       {len(steps)}")
    print(f"Turnos del modelo (LLM):      {model_turns}")
    print(f"Interacciones de usuario:     {user_inputs}")
    print(f"Tiempo de pared (Wall-Clock): {wall_clock_seconds:.2f} segundos ({wall_clock_seconds/60:.2f} min)")
    print("-" * 65)
    print("Llamadas a herramientas (Tool Calls):")
    for name, cnt in sorted(tool_counts.items(), key=lambda x: -x[1]):
        print(f"  - {name:<25}: {cnt}")
    if sum(tokens_stats.values()) > 0:
        print("-" * 65)
        print("Consumo de Tokens:")
        for k, v in tokens_stats.items():
            print(f"  - {k:<25}: {v}")
    print("=" * 65)

    return {
        "steps": len(steps),
        "model_turns": model_turns,
        "wall_clock_seconds": wall_clock_seconds,
        "tool_counts": tool_counts,
        "tokens": tokens_stats
    }


def main():
    parser = argparse.ArgumentParser(description="Analizador de transcript y TTVD")
    parser.add_argument("transcript", help="Ruta al archivo transcript.jsonl o transcript_full.jsonl")
    args = parser.parse_args()
    analyze_transcript(args.transcript)


if __name__ == "__main__":
    main()
