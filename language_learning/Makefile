.PHONY: validate test demo

PYTHON ?= python3

validate:
	$(PYTHON) language_learning/tools/validate.py

test: validate
	$(PYTHON) -m unittest discover -s language_learning/tests -v

demo: test
	$(MAKE) GAME_VERSION=SAPPHIRE LEARNER_DEMO=1 PYTHON="$(PYTHON)"
