#!/bin/bash
#
# Monitor for changes to Python files in the current directory, and when a
# change is detected, run the test suite.
#
# Requires that the user have either `fswatch` or `inotifywait` installed and
# in their PATH.
if command -v fswatch > /dev/null 2>&1; then
    fswatch -0 -l 0.2 --event Created --include '\.py$' --exclude '.*' . | while read -r -d '' filename; do
        echo "Change detected in $filename, running tests ..."
        python3 -m unittest
        echo
    done
elif command -v inotifywait > /dev/null 2>&1; then
    inotifywait -m -e create . | while read -r dir event filename; do
        if [[ "$filename" == *.py ]]; then
            echo "Change detected in $filename, running tests ..."
            python3 -m unittest
            echo
        fi
    done
else
    echo "ERROR: Neither fswatch nor inotifywait found, quitting."
    exit 1
fi
