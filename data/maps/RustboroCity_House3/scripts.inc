RustboroCity_House3_MapScripts:: @ 8157DEC
	.byte 0

RustboroCity_House3_EventScript_OldMan:: @ 8157DED
	.ifdef LEARNER_DEMO
	call LearnerOpening_HouseThreeNicknames
	.else
	msgbox RustboroCity_House3_Text_IGivePerfectlySuitedNicknames, MSGBOX_NPC
	.endif
	end

RustboroCity_House3_EventScript_OldWoman:: @ 8157DF6
	.ifdef LEARNER_DEMO
	call LearnerOpening_HouseThreePekachuOpinion
	.else
	msgbox RustboroCity_House3_Text_NamingPikachuPekachu, MSGBOX_NPC
	.endif
	end

RustboroCity_House3_EventScript_Pekachu:: @ 8157DFF
	lock
	faceplayer
	waitse
	playmoncry SPECIES_PIKACHU, 0
	.ifdef LEARNER_DEMO
	call LearnerOpening_HouseThreePekachuCry
	.else
	msgbox RustboroCity_House3_Text_Pekachu, MSGBOX_DEFAULT
	.endif
	waitmoncry
	release
	end
