RustboroCity_Flat1_2F_MapScripts:: @ 8157C72
	.byte 0

RustboroCity_Flat1_2F_EventScript_Woman:: @ 8157C73
	.ifdef LEARNER_DEMO
	call LearnerOpening_FlatOneMeals
	.else
	msgbox RustboroCity_Flat1_2F_Text_ComingUpWithMealsIsHard, MSGBOX_NPC
	.endif
	end
