set positional-arguments

test:
    poetry run python -m pytest -s

run *args:
    poetry run python gcidsum.py "$@"
