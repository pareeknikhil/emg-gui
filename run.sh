#!/bin/bash

set -e

export PYTHONPATH=$(pwd)


case $1 in 
    record)
    python -B "$PYTHONPATH/scripts/app.py" 
    ;;

    *)
    echo "❌ Invalid option!"
    echo "✅ Usage: $0 [record|train|validate|test|model|embedding|clr]"
    exit 1
    ;;
esac