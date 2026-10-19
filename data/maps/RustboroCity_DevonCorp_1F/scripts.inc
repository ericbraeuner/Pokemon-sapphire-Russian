RustboroCity_DevonCorp_1F_MapScripts:: @ 8157406
	map_script MAP_SCRIPT_ON_TRANSITION, RustboroCity_DevonCorp_1F_OnTransition
	.byte 0

RustboroCity_DevonCorp_1F_OnTransition:: @ 815740C
	call_if_unset FLAG_RETURNED_DEVON_GOODS, RustboroCity_DevonCorp_1F_EventScript_BlockStairs
	end

RustboroCity_DevonCorp_1F_EventScript_BlockStairs:: @ 8157416
	setobjectxyperm 2, 14, 2
	setobjectmovementtype 2, 8
	return

RustboroCity_DevonCorp_1F_EventScript_Employee:: @ 8157422
	lock
	faceplayer
	goto_if_set FLAG_RETURNED_DEVON_GOODS, RustboroCity_DevonCorp_1F_EventScript_GoodsRecovered
	goto_if_set FLAG_DEVON_GOODS_STOLEN, RustboroCity_DevonCorp_1F_EventScript_RobberWasntBright
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonShoes
	.else
	msgbox RustboroCity_DevonCorp_1F_Text_ThoseShoesAreOurProduct, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_DevonCorp_1F_EventScript_RobberWasntBright:: @ 8157440
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonRobber
	.else
	msgbox RustboroCity_DevonCorp_1F_Text_RobberWasntVeryBright, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_DevonCorp_1F_EventScript_GoodsRecovered:: @ 815744A
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonGoodsRecovered
	.else
	msgbox RustboroCity_DevonCorp_1F_Text_SoundsLikeStolenGoodsRecovered, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_DevonCorp_1F_EventScript_StairGuard:: @ 8157454
	lock
	faceplayer
	goto_if_set FLAG_RETURNED_DEVON_GOODS, RustboroCity_DevonCorp_1F_EventScript_AlwaysWelcome
	goto_if_set FLAG_RECOVERED_DEVON_GOODS, RustboroCity_DevonCorp_1F_EventScript_GotRobbed
	goto_if_set FLAG_DEVON_GOODS_STOLEN, RustboroCity_DevonCorp_1F_EventScript_GotRobbed
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonAuthorizedOnly
	.else
	msgbox RustboroCity_DevonCorp_1F_Text_OnlyAuthorizedPeopleEnter, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_DevonCorp_1F_EventScript_AlwaysWelcome:: @ 815747B
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonAlwaysWelcome
	.else
	msgbox RustboroCity_DevonCorp_1F_Text_YoureAlwaysWelcomeHere, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_DevonCorp_1F_EventScript_GotRobbed:: @ 8157485
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonRobberyShock
	.else
	msgbox RustboroCity_DevonCorp_1F_Text_HowCouldWeGetRobbed, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_DevonCorp_1F_EventScript_Greeter:: @ 815748F
	lock
	faceplayer
	goto_if_set FLAG_RETURNED_DEVON_GOODS, RustboroCity_DevonCorp_1F_EventScript_WelcomeToDevonCorp
	goto_if_set FLAG_RECOVERED_DEVON_GOODS, RustboroCity_DevonCorp_1F_EventScript_StaffGotRobbed
	goto_if_set FLAG_DEVON_GOODS_STOLEN, RustboroCity_DevonCorp_1F_EventScript_StaffGotRobbed
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonWelcome
	.else
	msgbox RustboroCity_DevonCorp_1F_Text_WelcomeToDevonCorp, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_DevonCorp_1F_EventScript_WelcomeToDevonCorp:: @ 81574B6
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonWelcome
	.else
	msgbox RustboroCity_DevonCorp_1F_Text_WelcomeToDevonCorp, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_DevonCorp_1F_EventScript_StaffGotRobbed:: @ 81574C0
	.ifdef LEARNER_DEMO
	call LearnerOpening_DevonStaffRobbed
	.else
	msgbox RustboroCity_DevonCorp_1F_Text_StaffGotRobbed, MSGBOX_DEFAULT
	.endif
	release
	end
