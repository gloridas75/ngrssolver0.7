PY?=.venv/bin/python
PIP?=.venv/bin/pip
TEST?=.venv/bin/pytest

init:
	python3 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -e .

dev:
	$(PIP) install -r /dev/null

solve:
	$(PY) src/run_solver.py --in input_enhanced.json --out output_enhanced.json --time 10

solve-auto:
	$(PY) src/run_solver.py --in input_enhanced.json --time 10

server:
	$(PY) server.py

test:
	$(TEST) -q
