RustboroCity_House2_MapScripts:: @ 8157D66
	.byte 0

RustboroCity_House2_EventScript_PokefanF:: @ 8157D67
	.ifdef LEARNER_DEMO
	call LearnerOpening_HouseTwoTrainerSchool
	.else
	msgbox RustboroCity_House2_Text_TrainerSchoolExcellent, MSGBOX_NPC
	.endif
	end

RustboroCity_House2_EventScript_LittleGirl:: @ 8157D70
	.ifdef LEARNER_DEMO
	call LearnerOpening_HouseTwoRoxanne
	.else
	msgbox RustboroCity_House2_Text_RoxanneKnowsALot, MSGBOX_NPC
	.endif
	end
