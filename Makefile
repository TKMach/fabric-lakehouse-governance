.PHONY: data demo test diagrams
export PYTHONPATH := src

data:
	python scripts/generate_synthetic_data.py --out data/sample --seed 42

demo:
	python -m lakehouse_gov.runner --data data/sample --report

test:
	python -m pytest -q

diagrams:   ## requires graphviz (dot) and the Inter font
	cd docs/diagrams && python build_diagrams.py && rm -f *.dot
