inotifywait -m -e create . | while read -r dir event filename; do
    if [[ "$filename" == *.py ]]; then
        echo "Change detected in $filename, running tests ..."
        python3 -m unittest
        echo
    fi
done
