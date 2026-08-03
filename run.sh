#!/bin/bash

set -e

PYTHONPATH="$(pwd)/src"
export PYTHONPATH

case $1 in
record)
	python -B "$PYTHONPATH/emg_gui/app.py"
	;;

*)
	echo "❌ Invalid option!"
	echo "✅ Usage: $0 [record|train|validate|test|model|embedding|clr]"
	exit 1
	;;
esac
