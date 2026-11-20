. "$(dirname "$0")/../../_lib/fixtures.sh"
python_project
cat >> calc.py <<'PY'


def mean(values: list[int]) -> float:
    return total / len(values)
PY
