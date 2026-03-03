#!/usr/bin/env python3
"""
=======================================
PLUGIN - Markdown Converter
======================================
Mantiene el texto como Markdown plano (no convierte a HTML)
Asana muestra markdown en las descripciones.
"""

def convert_to_asana(text: str) -> str:
    """
    Mantiene el texto como Markdown plano.
    Asana muestra markdown en las descripciones.
    """
    if not text:
        return ""
    
    # Limpiar espacios extras al inicio de cada línea
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Remover espacios extras al final
        cleaned_lines.append(line.rstrip())
    
    return '\n'.join(cleaned_lines)
