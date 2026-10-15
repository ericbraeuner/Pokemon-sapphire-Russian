.PHONY: validate test demo review-queue

PYTHON ?= python3

validate:
	$(PYTHON) language_learning/tools/validate.py

test: validate
	$(PYTHON) -m unittest discover -s language_learning/tests -v

demo: test
	$(MAKE) GAME_VERSION=SAPPHIRE LEARNER_DEMO=1 PYTHON="$(PYTHON)"

review-queue:
	$(PYTHON) language_learning/tools/review_queue.py language_learning/profiles/sample-learner.json --include-upcoming
