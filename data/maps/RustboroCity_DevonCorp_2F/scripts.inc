RustboroCity_DevonCorp_2F_MapScripts:: @ 81574CA
	map_script MAP_SCRIPT_ON_TRANSITION, RustboroCity_DevonCorp_2F_OnTransition
	.byte 0

RustboroCity_DevonCorp_2F_OnTransition:: @ 81574D0
	compare VAR_FOSSIL_RESURRECTION_STATE, 1
	call_if_eq RustboroCity_DevonCorp_2F_EventScript_SetFossilReady
	end

RustboroCity_DevonCorp_2F_EventScript_SetFossilReady:: @ 81574DC
	setvar VAR_FOSSIL_RESURRECTION_STATE, 2
	return

RustboroCity_DevonCorp_2F_EventScript_TalkToPokemonScientist:: @ 81574E2
	lock
	faceplayer
	compare VAR_FOSSIL_RESURRECTION_STATE, 1
	call_if_eq RustboroCity_DevonCorp_2F_EventScript_SetFossilReady
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonTalkDevice
	.else
	msgbox RustboroCity_DevonCorp_2F_Text_DeviceForTalkingToPokemon, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_DevonCorp_2F_EventScript_BallScientist:: @ 81574F9
	lock
	faceplayer
	compare VAR_FOSSIL_RESURRECTION_STATE, 1
	call_if_eq RustboroCity_DevonCorp_2F_EventScript_SetFossilReady
	goto_if_set FLAG_MET_DEVON_EMPLOYEE, RustboroCity_DevonCorp_2F_EventScript_DevelopedBalls
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonBallResearch
	.else
	msgbox RustboroCity_DevonCorp_2F_Text_DevelopingNewBalls, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_DevonCorp_2F_EventScript_DevelopedBalls:: @ 8157519
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonNewBalls
	.else
	msgbox RustboroCity_DevonCorp_2F_Text_WeFinallyMadeNewBalls, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_DevonCorp_2F_EventScript_PokenavScientist:: @ 8157523
	lock
	faceplayer
	compare VAR_FOSSIL_RESURRECTION_STATE, 1
	call_if_eq RustboroCity_DevonCorp_2F_EventScript_SetFossilReady
	goto_if_set FLAG_RECEIVED_POKENAV, RustboroCity_DevonCorp_2F_EventScript_HasPokenav
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonMadePokenav
	.else
	msgbox RustboroCity_DevonCorp_2F_Text_IMadePokenav, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_DevonCorp_2F_EventScript_HasPokenav:: @ 8157543
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonSeePokenav
	.else
	msgbox RustboroCity_DevonCorp_2F_Text_WowThatsAPokenav, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_DevonCorp_2F_EventScript_PokemonDreamsScientist:: @ 815754D
	lock
	faceplayer
	compare VAR_FOSSIL_RESURRECTION_STATE, 1
	call_if_eq RustboroCity_DevonCorp_2F_EventScript_SetFossilReady
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonDreamDevice
	.else
	msgbox RustboroCity_DevonCorp_2F_Text_DeviceToVisualizePokemonDreams, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_DevonCorp_2F_EventScript_FossilScientist:: @ 8157564
	lock
	faceplayer
	compare VAR_FOSSIL_RESURRECTION_STATE, 2
	goto_if_eq RustboroCity_DevonCorp_2F_EventScript_FossilMonReady
	compare VAR_FOSSIL_RESURRECTION_STATE, 1
	goto_if_eq RustboroCity_DevonCorp_2F_EventScript_StillRegenerating
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonFossilDevice
	.else
	msgbox RustboroCity_DevonCorp_2F_Text_DevelopDeviceToResurrectFossils, MSGBOX_DEFAULT
	.endif
	checkitem ITEM_ROOT_FOSSIL, 1
	compare VAR_RESULT, 1
	goto_if_eq RustboroCity_DevonCorp_2F_EventScript_NoticeRootFossil
	checkitem ITEM_CLAW_FOSSIL, 1
	compare VAR_RESULT, 1
	goto_if_eq RustboroCity_DevonCorp_2F_EventScript_NoticeClawFossil
	release
	end

RustboroCity_DevonCorp_2F_EventScript_NoticeRootFossil:: @ 81575A6
	closemessage
	playse SE_PIN
	applymovement 5, Common_Movement_ExclamationMark
	waitmovement 0
	applymovement 5, Common_Movement_Delay48
	waitmovement 0
	msgbox RustboroCity_DevonCorp_2F_Text_WantToBringFossilBackToLife, MSGBOX_YESNO
	compare VAR_RESULT, NO
	goto_if_eq RustboroCity_DevonCorp_2F_EventScript_DeclineGiveFossil
	bufferitemname 0, ITEM_ROOT_FOSSIL
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonHandedFossil
	.else
	msgbox RustboroCity_DevonCorp_2F_Text_HandedFossilToResearcher, MSGBOX_DEFAULT
	.endif
	removeitem ITEM_ROOT_FOSSIL
	setvar VAR_FOSSIL_RESURRECTION_STATE, 1
	setvar VAR_WHICH_FOSSIL_REVIVED, 1
	release
	end

RustboroCity_DevonCorp_2F_EventScript_NoticeClawFossil:: @ 81575EE
	closemessage
	playse SE_PIN
	applymovement 5, Common_Movement_ExclamationMark
	waitmovement 0
	applymovement 5, Common_Movement_Delay48
	waitmovement 0
	msgbox RustboroCity_DevonCorp_2F_Text_WantToBringFossilBackToLife, MSGBOX_YESNO
	compare VAR_RESULT, NO
	goto_if_eq RustboroCity_DevonCorp_2F_EventScript_DeclineGiveFossil
	bufferitemname 0, ITEM_CLAW_FOSSIL
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonHandedFossil
	.else
	msgbox RustboroCity_DevonCorp_2F_Text_HandedFossilToResearcher, MSGBOX_DEFAULT
	.endif
	removeitem ITEM_CLAW_FOSSIL
	setvar VAR_FOSSIL_RESURRECTION_STATE, 1
	setvar VAR_WHICH_FOSSIL_REVIVED, 2
	release
	end

RustboroCity_DevonCorp_2F_EventScript_DeclineGiveFossil:: @ 8157636
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonFossilDeclined
	.else
	msgbox RustboroCity_DevonCorp_2F_Text_OhIsThatSo, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_DevonCorp_2F_EventScript_StillRegenerating:: @ 8157640
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonFossilWaiting
	.else
	msgbox RustboroCity_DevonCorp_2F_Text_FossilRegeneratorTakesTime, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_DevonCorp_2F_EventScript_FossilMonReady:: @ 815764A
	compare VAR_WHICH_FOSSIL_REVIVED, 1
	goto_if_eq RustboroCity_DevonCorp_2F_EventScript_LileepReady
	compare VAR_WHICH_FOSSIL_REVIVED, 2
	goto_if_eq RustboroCity_DevonCorp_2F_EventScript_AnorithReady
	end

RustboroCity_DevonCorp_2F_EventScript_LileepReady:: @ 8157661
	bufferspeciesname 1, SPECIES_LILEEP
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonFossilRevived
	.else
	msgbox RustboroCity_DevonCorp_2F_Text_FossilizedMonBroughtBackToLife, MSGBOX_DEFAULT
	.endif
	getpartysize
	compare VAR_RESULT, 6
	goto_if_eq RustboroCity_DevonCorp_2F_EventScript_TooManyPokemon
	copyvar VAR_0x8004, VAR_RESULT
	setvar VAR_FOSSIL_RESURRECTION_STATE, 0
	setflag FLAG_RECEIVED_FOSSIL_MON
	playfanfare MUS_OBTAIN_ITEM
	message RustboroCity_DevonCorp_2F_Text_ReceivedMonFromResearcher
	waitfanfare
	waitmessage
	givemon SPECIES_LILEEP, 20, ITEM_NONE
	msgbox gText_NicknameReceivedPokemon, MSGBOX_YESNO
	compare VAR_RESULT, YES
	call_if_eq Common_EventScript_NameReceivedPartyMon
	release
	end

RustboroCity_DevonCorp_2F_EventScript_AnorithReady:: @ 81576B4
	bufferspeciesname 1, SPECIES_ANORITH
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonFossilRevived
	.else
	msgbox RustboroCity_DevonCorp_2F_Text_FossilizedMonBroughtBackToLife, MSGBOX_DEFAULT
	.endif
	getpartysize
	compare VAR_RESULT, 6
	goto_if_eq RustboroCity_DevonCorp_2F_EventScript_TooManyPokemon
	copyvar VAR_0x8004, VAR_RESULT
	setvar VAR_FOSSIL_RESURRECTION_STATE, 0
	setflag FLAG_RECEIVED_FOSSIL_MON
	playfanfare MUS_OBTAIN_ITEM
	message RustboroCity_DevonCorp_2F_Text_ReceivedMonFromResearcher
	waitfanfare
	waitmessage
	givemon SPECIES_ANORITH, 20, ITEM_NONE
	msgbox gText_NicknameReceivedPokemon, MSGBOX_YESNO
	compare VAR_RESULT, YES
	call_if_eq Common_EventScript_NameReceivedPartyMon
	release
	end

RustboroCity_DevonCorp_2F_EventScript_TooManyPokemon:: @ 8157707
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonPartyFull
	.else
	msgbox RustboroCity_DevonCorp_2F_Text_TooManyPokemon, MSGBOX_DEFAULT
	.endif
	release
	end
