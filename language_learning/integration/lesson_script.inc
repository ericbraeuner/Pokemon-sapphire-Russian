@ Called with the intro already locked. Do not change VAR_0x8004/5,
@ which carry Mom's object ID and the player's house selection.
LearnerLesson_ChooseLanguage::
	msgbox LearnerLesson_Intro, MSGBOX_DEFAULT
	closemessage
	multichoice 0, 0, MULTI_LEARNER_LANGUAGE, 0
	compare VAR_RESULT, 0
	goto_if_eq LearnerLesson_Russian
	compare VAR_RESULT, 1
	goto_if_eq LearnerLesson_German
	return

LearnerLesson_Russian:
	msgbox LearnerLesson_RuText, MSGBOX_DEFAULT
LearnerLesson_RussianMenu:
	closemessage
	multichoice 0, 0, MULTI_LEARNER_ACTION, 0
	compare VAR_RESULT, 0
	goto_if_eq LearnerLesson_Russian
	compare VAR_RESULT, 1
	goto_if_eq LearnerLesson_RussianHint
	compare VAR_RESULT, 2
	goto_if_eq LearnerLesson_RussianWords
	compare VAR_RESULT, 3
	goto_if_eq LearnerLesson_ChooseLanguage
	return
LearnerLesson_RussianHint:
	msgbox LearnerLesson_RuHint, MSGBOX_DEFAULT
	goto LearnerLesson_RussianMenu
LearnerLesson_RussianWords:
	msgbox LearnerLesson_RuWords, MSGBOX_DEFAULT
	goto LearnerLesson_RussianMenu

LearnerLesson_German:
	msgbox LearnerLesson_DeText, MSGBOX_DEFAULT
LearnerLesson_GermanMenu:
	closemessage
	multichoice 0, 0, MULTI_LEARNER_ACTION, 0
	compare VAR_RESULT, 0
	goto_if_eq LearnerLesson_German
	compare VAR_RESULT, 1
	goto_if_eq LearnerLesson_GermanHint
	compare VAR_RESULT, 2
	goto_if_eq LearnerLesson_GermanWords
	compare VAR_RESULT, 3
	goto_if_eq LearnerLesson_ChooseLanguage
	return
LearnerLesson_GermanHint:
	msgbox LearnerLesson_DeHint, MSGBOX_DEFAULT
	goto LearnerLesson_GermanMenu
LearnerLesson_GermanWords:
	msgbox LearnerLesson_DeWords, MSGBOX_DEFAULT
	goto LearnerLesson_GermanMenu

LearnerLesson_Intro:
	.string "MOM: Let's practice a greeting!\n"
	.string "Choose a language, or skip.$"
