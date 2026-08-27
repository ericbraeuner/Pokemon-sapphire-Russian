@ Saved by the normal SAVE command. Never touch Mom's VAR_0x8004/5/8.
LearnerOpening_EnsureSettings::
	compare VAR_LEARNER_LANGUAGE, 1
	goto_if_eq LearnerOpening_CheckLevel
	compare VAR_LEARNER_LANGUAGE, 2
	goto_if_eq LearnerOpening_CheckLevel
	goto LearnerOpening_Settings
LearnerOpening_CheckLevel:
	compare VAR_LEARNER_LEVEL, 1
	goto_if_lt LearnerOpening_Level
	compare VAR_LEARNER_LEVEL, 6
	goto_if_gt LearnerOpening_Level
	return

LearnerOpening_Settings::
	msgbox LearnerOpening_SettingsText, MSGBOX_DEFAULT
	closemessage
	multichoice 0, 0, MULTI_LEARNER_LANGUAGE, 1
	compare VAR_RESULT, 1
	goto_if_gt LearnerOpening_Settings
	copyvar VAR_LEARNER_LANGUAGE, VAR_RESULT
	addvar VAR_LEARNER_LANGUAGE, 1
LearnerOpening_Level:
	closemessage
	multichoice 0, 0, MULTI_LEARNER_LEVEL, 1
	compare VAR_RESULT, 5
	goto_if_gt LearnerOpening_Level
	copyvar VAR_LEARNER_LEVEL, VAR_RESULT
	addvar VAR_LEARNER_LEVEL, 1
	return

LearnerOpening_SettingsText:
	.string "Language / Sprache\n"
	.string "A1, A2: simpler dialogue.\p"
	.string "B1-C2: natural dialogue.\n"
	.string "Help stays available.$"
