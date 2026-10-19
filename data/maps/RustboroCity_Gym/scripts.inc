RustboroCity_Gym_MapScripts:: @ 81578D8
	.byte 0

RustboroCity_Gym_EventScript_Roxanne:: @ 81578D9
	trainerbattle_single TRAINER_ROXANNE, RustboroCity_Gym_Text_RoxanneIntro, RustboroCity_Gym_Text_RoxanneDefeat, RustboroCity_Gym_EventScript_RoxanneDefeated, NO_MUSIC
	goto_if_unset FLAG_RECEIVED_TM_ROCK_TOMB, RustboroCity_Gym_EventScript_GiveRockTomb
	.ifdef LEARNER_DEMO
	call LearnerOpening_RoxannePostBattle
	.else
	msgbox RustboroCity_Gym_Text_RoxannePostBattle, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_Gym_EventScript_RoxanneDefeated:: @ 81578FE
	message RustboroCity_Gym_Text_ReceivedStoneBadge
	waitmessage
	call Common_EventScript_PlayGymBadgeFanfare
	.ifdef LEARNER_DEMO
	call LearnerOpening_StoneBadgeInfo
	.else
	msgbox RustboroCity_Gym_Text_StoneBadgeInfoTakeThis, MSGBOX_DEFAULT
	.endif
	setflag FLAG_DEFEATED_RUSTBORO_GYM
	setflag FLAG_BADGE01_GET
	setvar VAR_RUSTBORO_STATE, 1
	addvar VAR_PETALBURG_GYM_STATE, 1
	setvar VAR_0x8008, 1
	call Common_EventScript_SetGymTrainers
	compare VAR_PETALBURG_GYM_STATE, 6
	call_if_eq Common_EventScript_ReadyPetalburgGymForBattle
	goto RustboroCity_Gym_EventScript_GiveRockTomb
	end

RustboroCity_Gym_EventScript_GiveRockTomb:: @ 815793C
	giveitem ITEM_TM39_ROCK_TOMB
	compare VAR_RESULT, 0
	goto_if_eq Common_EventScript_ShowBagIsFull
	setflag FLAG_RECEIVED_TM_ROCK_TOMB
	.ifdef LEARNER_DEMO
	call LearnerOpening_RockTombInfo
	.else
	msgbox RustboroCity_Gym_Text_ExplainRockTomb, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_Gym_EventScript_Josh:: @ 8157960
	trainerbattle_single TRAINER_JOSH, RustboroCity_Gym_Text_JoshIntro, RustboroCity_Gym_Text_JoshDefeat
	.ifdef LEARNER_DEMO
	call LearnerOpening_JoshPostBattle
	.else
	msgbox RustboroCity_Gym_Text_JoshPostBattle, MSGBOX_AUTOCLOSE
	.endif
	end

RustboroCity_Gym_EventScript_Tommy:: @ 8157977
	trainerbattle_single TRAINER_TOMMY, RustboroCity_Gym_Text_TommyIntro, RustboroCity_Gym_Text_TommyDefeat
	.ifdef LEARNER_DEMO
	call LearnerOpening_TommyPostBattle
	.else
	msgbox RustboroCity_Gym_Text_TommyPostBattle, MSGBOX_AUTOCLOSE
	.endif
	end

RustboroCity_Gym_EventScript_GymGuide:: @ 815798E
	lock
	faceplayer
	goto_if_set FLAG_DEFEATED_RUSTBORO_GYM, RustboroCity_Gym_EventScript_GymGuidePostVictory
	.ifdef LEARNER_DEMO
	call LearnerOpening_GymGuideAdvice
	.else
	msgbox RustboroCity_Gym_Text_GymGuideAdvice, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_Gym_EventScript_GymGuidePostVictory:: @ 81579A3
	.ifdef LEARNER_DEMO
	call LearnerOpening_GymGuideVictory
	.else
	msgbox RustboroCity_Gym_Text_GymGuidePostVictory, MSGBOX_DEFAULT
	.endif
	release
	end

RustboroCity_Gym_EventScript_LeftGymStatue:: @ 81579AD
	lockall
	goto_if_set FLAG_BADGE01_GET, RustboroCity_Gym_EventScript_GymStatueCertified
	goto RustboroCity_Gym_EventScript_GymStatue
	end

RustboroCity_Gym_EventScript_RightGymStatue:: @ 81579BD
	lockall
	goto_if_set FLAG_BADGE01_GET, RustboroCity_Gym_EventScript_GymStatueCertified
	goto RustboroCity_Gym_EventScript_GymStatue
	end

RustboroCity_Gym_EventScript_GymStatueCertified:: @ 81579CD
	.ifdef LEARNER_DEMO
	call LearnerOpening_GymStatueCertified
	.else
	msgbox RustboroCity_Gym_Text_GymStatueCertified, MSGBOX_DEFAULT
	.endif
	releaseall
	end

RustboroCity_Gym_EventScript_GymStatue:: @ 81579D7
	.ifdef LEARNER_DEMO
	call LearnerOpening_GymStatue
	.else
	msgbox RustboroCity_Gym_Text_GymStatue, MSGBOX_DEFAULT
	.endif
	releaseall
	end
