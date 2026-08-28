#ifndef GUARD_LEARNER_H
#define GUARD_LEARNER_H
#if LEARNER_DEMO
#define LEARNER_DECLARE(name) \
    extern const u8 LearnerUI_ru_##name[]; \
    extern const u8 LearnerUI_de_##name[];
LEARNER_DECLARE(ClockPrompt)
LEARNER_DECLARE(Yes)
LEARNER_DECLARE(No)
LEARNER_DECLARE(Level)
LEARNER_DECLARE(Mode)
LEARNER_DECLARE(Guided)
LEARNER_DECLARE(Immersion)
LEARNER_DECLARE(Boy)
LEARNER_DECLARE(Girl)
LEARNER_DECLARE(NewName)
LEARNER_DECLARE(YourName)
LEARNER_DECLARE(Potion)
LEARNER_DECLARE(PotionDescription)
LEARNER_DECLARE(Welcome)
LEARNER_DECLARE(ThisIsPokemon)
LEARNER_DECLARE(WorldInhabitedByPokemon)
LEARNER_DECLARE(AndYouAre)
LEARNER_DECLARE(AreYouBoyOrGirl)
LEARNER_DECLARE(WhatsYourName)
LEARNER_DECLARE(SoItsPlayer)
LEARNER_DECLARE(AhOkayYouArePlayer)
LEARNER_DECLARE(AreYouReady)
LEARNER_DECLARE(TreeckoName)
LEARNER_DECLARE(TorchicName)
LEARNER_DECLARE(MudkipName)
LEARNER_DECLARE(TreeckoKind)
LEARNER_DECLARE(TorchicKind)
LEARNER_DECLARE(MudkipKind)
LEARNER_DECLARE(Antidote)
LEARNER_DECLARE(ParaHeal)
LEARNER_DECLARE(Awakening)
LEARNER_DECLARE(PokeBall)
LEARNER_DECLARE(AntidoteDesc)
LEARNER_DECLARE(ParaHealDesc)
LEARNER_DECLARE(AwakeningDesc)
LEARNER_DECLARE(PokeBallDesc)
LEARNER_DECLARE(GreatBall)
LEARNER_DECLARE(GreatBallDesc)
LEARNER_DECLARE(UltraBall)
LEARNER_DECLARE(UltraBallDesc)
LEARNER_DECLARE(SuperPotion)
LEARNER_DECLARE(SuperPotionDesc)
LEARNER_DECLARE(HyperPotion)
LEARNER_DECLARE(HyperPotionDesc)
LEARNER_DECLARE(MaxPotion)
LEARNER_DECLARE(MaxPotionDesc)
LEARNER_DECLARE(FullRestore)
LEARNER_DECLARE(FullRestoreDesc)
LEARNER_DECLARE(BurnHeal)
LEARNER_DECLARE(BurnHealDesc)
LEARNER_DECLARE(IceHeal)
LEARNER_DECLARE(IceHealDesc)
LEARNER_DECLARE(FullHeal)
LEARNER_DECLARE(FullHealDesc)
LEARNER_DECLARE(Revive)
LEARNER_DECLARE(ReviveDesc)
LEARNER_DECLARE(MaxRevive)
LEARNER_DECLARE(MaxReviveDesc)
LEARNER_DECLARE(Repel)
LEARNER_DECLARE(RepelDesc)
LEARNER_DECLARE(SuperRepel)
LEARNER_DECLARE(SuperRepelDesc)
LEARNER_DECLARE(MaxRepel)
LEARNER_DECLARE(MaxRepelDesc)
LEARNER_DECLARE(EscapeRope)
LEARNER_DECLARE(EscapeRopeDesc)
LEARNER_DECLARE(RareCandy)
LEARNER_DECLARE(RareCandyDesc)
LEARNER_DECLARE(Ether)
LEARNER_DECLARE(EtherDesc)
LEARNER_DECLARE(Elixir)
LEARNER_DECLARE(ElixirDesc)
#undef LEARNER_DECLARE
#define LEARNER_UI(language, name) ((language) == 1 ? LearnerUI_ru_##name : LearnerUI_de_##name)
void Learner_CommitNewGameSettings(void);
u8 Learner_GetLanguage(void);
const u8 *Learner_ItemText(u16 itemId, bool8 description);
void Learner_CopyItemName(u16 itemId, u8 *dest);
extern const u8 gLearnerBagTilesRu[], gLearnerBagTilesDe[];
extern const u8 gLearnerDexSearchTilesRu[], gLearnerDexSearchTilesDe[];
extern const u8 gLearnerDexMainTilesRu[], gLearnerDexMainTilesDe[];
extern const u8 gLearnerDexSpriteTilesRu[], gLearnerDexSpriteTilesDe[];
const u8 *Learner_Translate(const u8 *text);
const u8 *Learner_MapName(u16 section, const u8 *fallback);
#endif
#endif
