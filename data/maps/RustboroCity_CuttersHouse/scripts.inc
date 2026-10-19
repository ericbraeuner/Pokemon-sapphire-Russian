RustboroCity_CuttersHouse_MapScripts:: @ 8157D26
	.byte 0

RustboroCity_CuttersHouse_EventScript_Cutter:: @ 8157D27
	lock
	faceplayer
	goto_if_set FLAG_RECEIVED_HM01, RustboroCity_CuttersHouse_EventScript_ExplainCut
	.ifdef LEARNER_DEMO
	call LearnerOpening_CutterGift
	.else
	msgbox RustboroCity_CuttersHouse_Text_YouCanPutThisHMToGoodUse, MSGBOX_DEFAULT
	.endif
	giveitem ITEM_HM01_CUT
	setflag FLAG_RECEIVED_HM01
	.ifdef LEARNER_DEMO
	call LearnerOpening_CutterExplainCut
	.else
	msgbox RustboroCity_CuttersHouse_Text_ExplainCut, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_CuttersHouse_EventScript_ExplainCut:: @ 8157D53
	.ifdef LEARNER_DEMO
	call LearnerOpening_CutterExplainCut
	.else
	msgbox RustboroCity_CuttersHouse_Text_ExplainCut, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_CuttersHouse_EventScript_Lass:: @ 8157D5D
	.ifdef LEARNER_DEMO
	call LearnerOpening_CutterFamilyHistory
	.else
	msgbox RustboroCity_CuttersHouse_Text_DadHelpedClearLandOfTrees, MSGBOX_NPC
	.endif
	end
