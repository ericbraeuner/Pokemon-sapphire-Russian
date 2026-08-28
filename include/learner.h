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
#undef LEARNER_DECLARE
#define LEARNER_UI(language, name) ((language) == 1 ? LearnerUI_ru_##name : LearnerUI_de_##name)
void Learner_CommitNewGameSettings(void);
u8 Learner_GetLanguage(void);
const u8 *Learner_Translate(const u8 *text);
const u8 *Learner_MapName(u16 section, const u8 *fallback);
#endif
#endif
