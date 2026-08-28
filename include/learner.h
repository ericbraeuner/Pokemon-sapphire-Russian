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
LEARNER_DECLARE(Welcome)
LEARNER_DECLARE(ThisIsPokemon)
LEARNER_DECLARE(WorldInhabitedByPokemon)
LEARNER_DECLARE(AndYouAre)
LEARNER_DECLARE(AreYouBoyOrGirl)
LEARNER_DECLARE(WhatsYourName)
LEARNER_DECLARE(SoItsPlayer)
LEARNER_DECLARE(AhOkayYouArePlayer)
LEARNER_DECLARE(AreYouReady)
#undef LEARNER_DECLARE
#define LEARNER_UI(language, name) ((language) == 1 ? LearnerUI_ru_##name : LearnerUI_de_##name)
void Learner_CommitNewGameSettings(void);
#endif
#endif
