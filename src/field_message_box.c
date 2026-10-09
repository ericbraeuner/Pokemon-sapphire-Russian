#include "global.h"
#include "event_data.h"
#include "field_message_box.h"
#include "main.h"
#include "menu.h"
#include "string_util.h"
#include "task.h"
#include "text.h"
#include "text_window.h"
#include "constants/vars.h"

static EWRAM_DATA struct Window gFieldMessageBoxWindow = {0};

static u8 sMessageBoxMode;

static void Task_FieldMessageBox(u8 taskId);
static void CreateFieldMessageBoxTask(void);
static void DestroyFieldMessageBoxTask(void);
static void PrintFieldMessage(const u8 *message);
static void PrintFieldMessageFromStringVar4(void);

void InitFieldMessageBox(void)
{
    sMessageBoxMode = FIELD_MESSAGE_BOX_HIDDEN;
    TextWindow_SetDlgFrameBaseTileNum(gMenuTextWindowContentTileOffset);
    Text_InitWindowWithTemplate(&gFieldMessageBoxWindow, &gMenuTextWindowTemplate);
}

static void Task_FieldMessageBox(u8 taskId)
{
    struct Task *task = &gTasks[taskId];
    switch (task->data[0])
    {
    case 0:
        TextWindow_LoadDialogueFrameTiles(&gFieldMessageBoxWindow);
        task->data[0]++;
        break;
    case 1:
        TextWindow_DrawDialogueFrame(&gFieldMessageBoxWindow);
        task->data[0]++;
        break;
    case 2:
#if LEARNER_DEMO
        // R opens the vocabulary for authored learner dialogue. The generated
        // script replays this exact message after the vocabulary closes.
        if (sMessageBoxMode == FIELD_MESSAGE_BOX_NORMAL
         && VarGet(VAR_LEARNER_DICTIONARY_CONTEXT) != 0
         && VarGet(VAR_LEARNER_DICTIONARY_REQUEST) == 0
         && JOY_NEW(R_BUTTON))
        {
            VarSet(VAR_LEARNER_DICTIONARY_REQUEST, 1);
            gMain.newKeys |= A_BUTTON;
        }
#endif
        switch (sMessageBoxMode)
        {
        case FIELD_MESSAGE_BOX_NORMAL:
            if (!Text_UpdateWindow(&gFieldMessageBoxWindow))
                return;
            break;
        case FIELD_MESSAGE_BOX_AUTO_SCROLL:
            if (!Text_UpdateWindowAutoscroll(&gFieldMessageBoxWindow))
                return;
            break;
        }
        sMessageBoxMode = FIELD_MESSAGE_BOX_HIDDEN;
        DestroyTask(taskId);
    }
}

static void CreateFieldMessageBoxTask(void)
{
    CreateTask(Task_FieldMessageBox, 80);
}

static void DestroyFieldMessageBoxTask(void)
{
    u8 taskId = FindTaskIdByFunc(Task_FieldMessageBox);
    if (taskId != 0xFF)
        DestroyTask(taskId);
}

bool8 ShowFieldMessage(const u8 *message)
{
    if (sMessageBoxMode != FIELD_MESSAGE_BOX_HIDDEN)
    {
        return FALSE;
    }
    else
    {
        PrintFieldMessage(message);
        sMessageBoxMode = FIELD_MESSAGE_BOX_NORMAL;
        return TRUE;
    }
}

bool8 ShowFieldAutoScrollMessage(const u8 *message)
{
    if (sMessageBoxMode != FIELD_MESSAGE_BOX_HIDDEN)
    {
        return FALSE;
    }
    else
    {
        sMessageBoxMode = FIELD_MESSAGE_BOX_AUTO_SCROLL;
        PrintFieldMessage(message);
        return TRUE;
    }
}

bool8 unref_sub_8064BB8(const u8 *message)
{
    sMessageBoxMode = FIELD_MESSAGE_BOX_AUTO_SCROLL;
    PrintFieldMessage(message);
    return TRUE;
}

bool8 unref_sub_8064BD0(const u8 *message)
{
    if (sMessageBoxMode != FIELD_MESSAGE_BOX_HIDDEN)
    {
        return FALSE;
    }
    else
    {
        sMessageBoxMode = FIELD_MESSAGE_BOX_NORMAL;
        PrintFieldMessageFromStringVar4();
        return TRUE;
    }
}

static void PrintFieldMessage(const u8 *message)
{
    StringExpandPlaceholders(gStringVar4, message);
    Contest_StartTextPrinter(&gFieldMessageBoxWindow, gStringVar4, gMenuTextTileOffset, 2, 15);
    CreateFieldMessageBoxTask();
}

static void PrintFieldMessageFromStringVar4(void)
{
    Contest_StartTextPrinter(&gFieldMessageBoxWindow, gStringVar4, gMenuTextTileOffset, 2, 15);
    CreateFieldMessageBoxTask();
}

void HideFieldMessageBox(void)
{
    DestroyFieldMessageBoxTask();
    TextWindow_EraseDialogueFrame(&gFieldMessageBoxWindow);
    sMessageBoxMode = FIELD_MESSAGE_BOX_HIDDEN;
}

u8 GetFieldMessageBoxMode(void)
{
    return sMessageBoxMode;
}

bool8 IsFieldMessageBoxHidden(void)
{
    if (sMessageBoxMode == FIELD_MESSAGE_BOX_HIDDEN)
        return TRUE;
    else
        return FALSE;
}

void unref_sub_8064CA0(void)
{
    DestroyFieldMessageBoxTask();
    TextWindow_DrawDialogueFrame(&gFieldMessageBoxWindow);
    sMessageBoxMode = FIELD_MESSAGE_BOX_HIDDEN;
}
