PYTHON ?= python

run:
	PYTHONPATH=src $(PYTHON) -m depviz examples/config_test.csv --show-config

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v
