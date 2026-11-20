. "$(dirname "$0")/../../_lib/fixtures.sh"
python_project
# An unused import (auto-fixable) and code that ruff format rewrites.
replace calc.py '"""A tiny calculator."""' '"""A tiny calculator."""
import os'
replace calc.py 'def add(a: int, b: int) -> int:
    return a + b' 'def add(a:int,b:int)->int:
    return a+b'
