RustboroCity_Flat2_3F_MapScripts:: @ 8157DD9
	.byte 0

RustboroCity_Flat2_3F_EventScript_DevonEmployee:: @ 8157DDA
	.ifdef LEARNER_DEMO
	call LearnerOpening_FlatTwoPresidentStones
	.else
	msgbox RustboroCity_Flat2_3F_Text_PresidentCollectsRareStones, MSGBOX_NPC
	.endif
	end

RustboroCity_Flat2_3F_EventScript_Woman:: @ 8157DE3
	.ifdef LEARNER_DEMO
	call LearnerOpening_FlatTwoSonStones
	.else
	msgbox RustboroCity_Flat2_3F_Text_PresidentsSonAlsoCollectsRareStones, MSGBOX_NPC
	.endif
	end
