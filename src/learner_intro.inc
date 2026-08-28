// Included only by the opt-in build, after the Birch task declarations.
// Keep pending choices outside SaveBlock1: NewGameInitData clears that block.
static EWRAM_DATA u8 sLearnerLanguage = 0;
static EWRAM_DATA u8 sLearnerLevel = 0;
static EWRAM_DATA u8 sLearnerMode = 0;
static EWRAM_DATA bool8 sLearnerSettingsPending = FALSE;

static const u8 sLearnerLanguageTitle[] = _("Language");
static const u8 sLearnerRussianName[] = _("Russian");
static const u8 sLearnerGermanName[] = _("German");
static const u8 sLearnerLevelA1[] = _("A1");
static const u8 sLearnerLevelA2[] = _("A2");
static const u8 sLearnerLevelB1[] = _("B1");
static const u8 sLearnerLevelB2[] = _("B2");
static const u8 sLearnerLevelC1[] = _("C1");
static const u8 sLearnerLevelC2[] = _("C2");
static const u8 sLearnerGuidance[] = _("A: read or confirm.\nB: back in menus.\pAfter translated scenes,\nopen the dictionary for help.\pYour language and level stay\nselected until you change them.");
static const struct MenuAction sLearnerLanguageChoices[] = {
    {sLearnerRussianName, NULL}, {sLearnerGermanName, NULL}
};
static const struct MenuAction sLearnerLevelChoices[] = {
    {sLearnerLevelA1, NULL}, {sLearnerLevelA2, NULL},
    {sLearnerLevelB1, NULL}, {sLearnerLevelB2, NULL},
    {sLearnerLevelC1, NULL}, {sLearnerLevelC2, NULL}
};
static const struct MenuAction sLearnerRuModes[] = {
    {LearnerUI_ru_Guided, NULL}, {LearnerUI_ru_Immersion, NULL}
};
static const struct MenuAction sLearnerDeModes[] = {
    {LearnerUI_de_Guided, NULL}, {LearnerUI_de_Immersion, NULL}
};
static const struct MenuAction sLearnerRuGender[] = {
    {LearnerUI_ru_Boy, NULL}, {LearnerUI_ru_Girl, NULL}
};
static const struct MenuAction sLearnerDeGender[] = {
    {LearnerUI_de_Boy, NULL}, {LearnerUI_de_Girl, NULL}
};
static const struct MenuAction sLearnerRuYesNo[] = {
    {LearnerUI_ru_Yes, NULL}, {LearnerUI_ru_No, NULL}
};
static const struct MenuAction sLearnerDeYesNo[] = {
    {LearnerUI_de_Yes, NULL}, {LearnerUI_de_No, NULL}
};

void Learner_CommitNewGameSettings(void)
{
    if (!sLearnerSettingsPending)
        return;
    VarSet(VAR_LEARNER_LANGUAGE, sLearnerLanguage);
    VarSet(VAR_LEARNER_LEVEL, sLearnerLevel);
    VarSet(VAR_LEARNER_MODE, sLearnerMode);
    sLearnerSettingsPending = FALSE;
}

u8 Learner_GetLanguage(void)
{
    return sLearnerSettingsPending ? sLearnerLanguage : VarGet(VAR_LEARNER_LANGUAGE);
}

static void Learner_DrawSetup(const u8 *title, const struct MenuAction *items, u8 count, u8 cursor)
{
    Menu_EraseScreen();
    Menu_DrawStdWindowFrame(2, 1, 27, 18);
    Menu_PrintText(title, 4, 2);
    Menu_PrintItems(4, 5, count, items);
    InitMenu(0, 4, 5, count, cursor, 22);
}

static void Task_LearnerSetup(u8 taskId)
{
    s8 choice;
    if (gPaletteFade.active)
        return;
    switch (gTasks[taskId].data[12])
    {
    case 0:
        Learner_DrawSetup(sLearnerLanguageTitle, sLearnerLanguageChoices, 2, sLearnerLanguage - 1);
        gTasks[taskId].data[12] = 1;
        break;
    case 2:
        Learner_DrawSetup(LEARNER_UI(sLearnerLanguage, Level), sLearnerLevelChoices, 6, sLearnerLevel - 1);
        gTasks[taskId].data[12] = 3;
        break;
    case 4:
        Learner_DrawSetup(LEARNER_UI(sLearnerLanguage, Mode), sLearnerLanguage == 1 ? sLearnerRuModes : sLearnerDeModes, 2, sLearnerMode - 1);
        gTasks[taskId].data[12] = 5;
        break;
    case 6:
        if (BirchSpeechUpdateWindowText())
        {
            Menu_EraseScreen();
            gTasks[taskId].func = Task_NewGameSpeech2;
        }
        break;
    default:
        choice = Menu_ProcessInputNoWrap();
        if (choice == -2)
            return;
        if (choice == -1)
        {
            if (gTasks[taskId].data[12] > 1)
            {
                Menu_DestroyCursor();
                gTasks[taskId].data[12] -= 3;
            }
            return;
        }
        Menu_DestroyCursor();
        if (gTasks[taskId].data[12] == 1)
            sLearnerLanguage = choice + 1;
        else if (gTasks[taskId].data[12] == 3)
            sLearnerLevel = choice + 1;
        else
        {
            sLearnerMode = choice + 1;
            Menu_EraseScreen();
            if (sLearnerMode == 1)
            {
                Menu_DrawStdWindowFrame(2, 13, 27, 18);
                MenuPrintMessage(sLearnerGuidance, 3, 14);
                gTasks[taskId].data[12] = 6;
            }
            else
                gTasks[taskId].func = Task_NewGameSpeech2;
            return;
        }
        gTasks[taskId].data[12]++;
        break;
    }
}
