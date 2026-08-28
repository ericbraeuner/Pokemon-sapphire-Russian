OldaleTown_Mart_MapScripts:: @ 8152F78
	.byte 0

OldaleTown_Mart_EventScript_Clerk:: @ 8152F79
	lock
	faceplayer
	message Text_HowMayIServeYou
	waitmessage
	goto_if_set FLAG_ADVENTURE_STARTED, OldaleTown_Mart_ExpandedItems
	pokemart OldaleTown_Mart_Pokemart_Basic
	msgbox Text_PleaseComeAgain, MSGBOX_DEFAULT
	release
	end

	.align 2
OldaleTown_Mart_Pokemart_Basic:: @ 8152F9C
	.2byte ITEM_POTION
	.2byte ITEM_ANTIDOTE
	.2byte ITEM_PARALYZE_HEAL
	.2byte ITEM_AWAKENING
	.2byte ITEM_NONE
	release
	end

OldaleTown_Mart_ExpandedItems:: @ 8152FA8
	pokemart OldaleTown_Mart_Pokemart_Expanded
	msgbox Text_PleaseComeAgain, MSGBOX_DEFAULT
	release
	end

	.align 2
OldaleTown_Mart_Pokemart_Expanded:: @ 8152FB8
	.2byte ITEM_POKE_BALL
	.2byte ITEM_POTION
	.2byte ITEM_ANTIDOTE
	.2byte ITEM_PARALYZE_HEAL
	.2byte ITEM_AWAKENING
	.2byte ITEM_NONE
	release
	end

OldaleTown_Mart_EventScript_Woman:: @ 8152FC6
	lock
	faceplayer
	goto_if_set FLAG_ADVENTURE_STARTED, OldaleTown_Mart_EventScript_PokeBallsInStock
	.ifdef LEARNER_DEMO
	call LearnerOpening_OldaleSoldOut
	.else
	msgbox OldaleTown_Mart_Text_PokeBallsAreSoldOut, MSGBOX_DEFAULT
	.endif
	release
	end

OldaleTown_Mart_EventScript_PokeBallsInStock:: @ 8152FDB
	.ifdef LEARNER_DEMO
	call LearnerOpening_OldaleBuyBalls
	.else
	msgbox OldaleTown_Mart_Text_ImGoingToBuyPokeBalls, MSGBOX_DEFAULT
	.endif
	release
	end

OldaleTown_Mart_EventScript_Boy:: @ 8152FE5
	.ifdef LEARNER_DEMO
	lock
	faceplayer
	call LearnerOpening_OldaleHealth
	release
	.else
	msgbox OldaleTown_Mart_Text_RestoreHPWithPotion, MSGBOX_NPC
	.endif
	end
