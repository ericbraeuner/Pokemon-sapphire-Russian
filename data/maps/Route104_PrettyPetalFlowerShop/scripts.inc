Route104_PrettyPetalFlowerShop_MapScripts:: @ 815BDE4
	map_script MAP_SCRIPT_ON_TRANSITION, Route104_PrettyPetalFlowerShop_MapScript1_15BDEA
	.byte 0

Route104_PrettyPetalFlowerShop_MapScript1_15BDEA:: @ 815BDEA
	setflag FLAG_LANDMARK_FLOWER_SHOP
	goto_if_unset FLAG_MET_PRETTY_PETAL_SHOP_OWNER, Route104_PrettyPetalFlowerShop_EventScript_15BE03
	goto_if_unset FLAG_BADGE03_GET, Route104_PrettyPetalFlowerShop_EventScript_15BE03
	setflag FLAG_TEMP_1
	end

Route104_PrettyPetalFlowerShop_EventScript_15BE03:: @ 815BE03
	setobjectxyperm 1, 4, 6
	end

Route104_PrettyPetalFlowerShop_EventScript_15BE0B:: @ 815BE0B
	lock
	faceplayer
	goto_if_set FLAG_TEMP_1, Route104_PrettyPetalFlowerShop_EventScript_15BE7C
	.ifdef LEARNER_DEMO
	call LearnerOpening_FlowerShopWelcome
	.else
	msgbox Route104_PrettyPetalFlowerShop_Text_1C5EC6, MSGBOX_DEFAULT
	.endif
	goto_if_set FLAG_MET_PRETTY_PETAL_SHOP_OWNER, Route104_PrettyPetalFlowerShop_EventScript_15BE4A
	setflag FLAG_MET_PRETTY_PETAL_SHOP_OWNER
	msgbox Route104_PrettyPetalFlowerShop_Text_1C5F48, MSGBOX_YESNO
	compare VAR_RESULT, YES
	call_if_eq Route104_PrettyPetalFlowerShop_EventScript_15BE6A
	compare VAR_RESULT, NO
	call_if_eq Route104_PrettyPetalFlowerShop_EventScript_15BE73
	release
	end

Route104_PrettyPetalFlowerShop_EventScript_15BE4A:: @ 815BE4A
	msgbox Route104_PrettyPetalFlowerShop_Text_1C5F1B, MSGBOX_YESNO
	compare VAR_RESULT, YES
	call_if_eq Route104_PrettyPetalFlowerShop_EventScript_15BE6A
	compare VAR_RESULT, NO
	call_if_eq Route104_PrettyPetalFlowerShop_EventScript_15BE73
	release
	end

Route104_PrettyPetalFlowerShop_EventScript_15BE6A:: @ 815BE6A
	.ifdef LEARNER_DEMO
	call LearnerOpening_FlowerShopBerryLesson
	.else
	msgbox Route104_PrettyPetalFlowerShop_Text_1C5F9D, MSGBOX_DEFAULT
	.endif
	return

Route104_PrettyPetalFlowerShop_EventScript_15BE73:: @ 815BE73
	.ifdef LEARNER_DEMO
	call LearnerOpening_FlowerShopHappiness
	.else
	msgbox Route104_PrettyPetalFlowerShop_Text_1C6121, MSGBOX_DEFAULT
	.endif
	return

Route104_PrettyPetalFlowerShop_EventScript_15BE7C:: @ 815BE7C
	message Text_PlayerWhatCanIDoForYou
	waitmessage
	pokemartdecoration2 Route104_PrettyPetalFlowerShop_Items
	msgbox Text_PleaseComeAgain, MSGBOX_DEFAULT
	release
	end

	.align 2
Route104_PrettyPetalFlowerShop_Items:: @ 815BE94
	.2byte ITEM_FULL_RESTORE
	.2byte ITEM_MAX_POTION
	.2byte ITEM_HYPER_POTION
	.2byte ITEM_SUPER_POTION
	.2byte ITEM_FULL_HEAL
	.2byte ITEM_REVIVE
	.2byte ITEM_NONE
	release
	end

Route104_PrettyPetalFlowerShop_EventScript_15BEA4:: @ 815BEA4
	lock
	faceplayer
	goto_if_unset FLAG_RECEIVED_WAILMER_PAIL, Route104_PrettyPetalFlowerShop_EventScript_15BEB9
	.ifdef LEARNER_DEMO
	call LearnerOpening_FlowerShopWatering
	.else
	msgbox Route104_PrettyPetalFlowerShop_Text_1C61E8, MSGBOX_DEFAULT
	.endif
	release
	end

Route104_PrettyPetalFlowerShop_EventScript_15BEB9:: @ 815BEB9
	.ifdef LEARNER_DEMO
	call LearnerOpening_FlowerShopPailGift
	.else
	msgbox Route104_PrettyPetalFlowerShop_Text_1C6158, MSGBOX_DEFAULT
	.endif
	giveitem ITEM_WAILMER_PAIL
	.ifdef LEARNER_DEMO
	call LearnerOpening_FlowerShopWatering
	.else
	msgbox Route104_PrettyPetalFlowerShop_Text_1C61E8, MSGBOX_DEFAULT
	.endif
	setflag FLAG_RECEIVED_WAILMER_PAIL
	release
	end

Route104_PrettyPetalFlowerShop_EventScript_15BEDA:: @ 815BEDA
	lock
	faceplayer
	dotimebasedevents
	goto_if_set FLAG_DAILY_RECEIVED_BERRY_FLOWER_SHOP, Route104_PrettyPetalFlowerShop_EventScript_15BF1A
	.ifdef LEARNER_DEMO
	call LearnerOpening_FlowerShopDailyBerry
	.else
	msgbox Route104_PrettyPetalFlowerShop_Text_1C62DA, MSGBOX_DEFAULT
	.endif
	random 8
	addvar VAR_RESULT, ITEM_CHERI_BERRY
	giveitem VAR_RESULT
	compare VAR_RESULT, 0
	goto_if_eq Common_EventScript_ShowBagIsFull
	setflag FLAG_DAILY_RECEIVED_BERRY_FLOWER_SHOP
	.ifdef LEARNER_DEMO
	call LearnerOpening_FlowerShopBerryUses
	.else
	msgbox Route104_PrettyPetalFlowerShop_Text_1C6335, MSGBOX_DEFAULT
	.endif
	release
	end

Route104_PrettyPetalFlowerShop_EventScript_15BF1A:: @ 815BF1A
	.ifdef LEARNER_DEMO
	call LearnerOpening_FlowerShopBerryUses
	.else
	msgbox Route104_PrettyPetalFlowerShop_Text_1C6335, MSGBOX_DEFAULT
	.endif
	release
	end
