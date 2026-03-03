#!/bin/bash
# Lanzador para ejecutar scripts de Python
# Uso: ./run.sh script.py [argumentos]

SCRIPT=$1
shift

if [ -z "$SCRIPT" ]; then
    echo "Uso: ./run.sh script.py [argumentos]"
    exit 1
fi

# Activar venv si existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Ejecutar script
python3 "$SCRIPT" "$@"
