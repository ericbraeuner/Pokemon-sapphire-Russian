RustboroCity_Flat1_1F_MapScripts:: @ 8157C5F
	.byte 0

RustboroCity_Flat1_1F_EventScript_Man:: @ 8157C60
	.ifdef LEARNER_DEMO
	call LearnerOpening_FlatOneAbilities
	.else
	msgbox RustboroCity_Flat1_1F_Text_EveryPokemonHasAbility, MSGBOX_NPC
	.endif
	end

RustboroCity_Flat1_1F_EventScript_Woman:: @ 8157C69
	.ifdef LEARNER_DEMO
	call LearnerOpening_FlatOnePokemonStrange
	.else
	msgbox RustboroCity_Flat1_1F_Text_PokemonStrange, MSGBOX_NPC
	.endif
	end
