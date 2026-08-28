OldaleTown_House1_MapScripts:: @ 8152EEB
	.byte 0

OldaleTown_House1_EventScript_Woman:: @ 8152EEC
	.ifdef LEARNER_DEMO
	lock
	faceplayer
	call LearnerOpening_OldalePartyOrder
	release
	.else
	msgbox OldaleTown_House1_Text_LeftPokemonGoesOutFirst, MSGBOX_NPC
	.endif
	end
