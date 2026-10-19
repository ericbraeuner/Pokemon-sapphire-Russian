RustboroCity_Flat2_1F_MapScripts:: @ 8157D79
	.byte 0

RustboroCity_Flat2_1F_EventScript_OldWoman:: @ 8157D7A
	.ifdef LEARNER_DEMO
	call LearnerOpening_FlatTwoWorkers
	.else
	msgbox RustboroCity_Flat2_1F_Text_DevonWorkersLiveHere, MSGBOX_NPC
	.endif
	end

RustboroCity_Flat2_1F_EventScript_Skitty:: @ 8157D83
	lock
	faceplayer
	waitse
	playmoncry SPECIES_SKITTY, 0
	.ifdef LEARNER_DEMO
	call LearnerOpening_FlatTwoSkitty
	.else
	msgbox RustboroCity_Flat2_1F_Text_Skitty, MSGBOX_DEFAULT
	.endif
	waitmoncry
	release
	end
