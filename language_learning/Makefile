.PHONY: validate test demo review-queue select-variant adaptive-plan dashboard

PYTHON ?= python3

validate:
	$(PYTHON) language_learning/tools/validate.py

test: validate
	$(PYTHON) -m unittest discover -s language_learning/tests -v

demo: test
	$(MAKE) GAME_VERSION=SAPPHIRE LEARNER_DEMO=1 PYTHON="$(PYTHON)"

review-queue:
	$(PYTHON) language_learning/tools/review_queue.py language_learning/profiles/sample-learner.json --include-upcoming

select-variant:
	$(PYTHON) language_learning/tools/adaptive_selector.py language_learning/language_packs/ru/pack.json language_learning/profiles/sample-learner.json littleroot.player_house.mom.welcome.001

adaptive-plan:
	$(PYTHON) language_learning/tools/adaptive_plan.py language_learning/profiles/sample-learner.json build/adaptive-plan.json --generated-at 2026-01-15T18:30:00Z

dashboard:
	$(PYTHON) language_learning/tools/learner_dashboard.py language_learning/profiles/sample-learner.json build/learner-dashboard.html
