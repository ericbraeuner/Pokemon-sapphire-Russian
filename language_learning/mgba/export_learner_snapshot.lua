-- Export learner settings and lossless activity events from Pokémon Sapphire.
-- In mGBA 0.10+, open Tools > Scripting, load this file, and leave it running.

local OUTPUT_PATH = "learner-snapshot.json"
local SOURCE_ID = "pokemon-sapphire-learner-save"

local SAVE_BLOCK1 = 0x02025734
local VARS_OFFSET = 0x1340
local VARS_START = 0x4000
local VAR_LANGUAGE = 0x40F0
local VAR_LEVEL = 0x40F1
local VAR_EXPOSURES = 0x40F5
local VAR_DICTIONARIES = 0x40F6
local VAR_LAST_EXPOSURE_CONTEXT = 0x40F7
local VAR_LAST_DICTIONARY_CONTEXT = 0x40F8

local languages = {[1] = "ru", [2] = "de"}
local levels = {[1] = "A1", [2] = "A2", [3] = "B1", [4] = "B2", [5] = "C1", [6] = "C2"}
local sessionId = SOURCE_ID .. "-" .. os.date("!%Y%m%dT%H%M%SZ")
local events = {}
local sequence = 0
local previous = nil
local dirty = false

local function readVar(id)
    return emu:read16(SAVE_BLOCK1 + VARS_OFFSET + 2 * (id - VARS_START))
end

local function jsonString(value)
    return '"' .. value:gsub('\\', '\\\\'):gsub('"', '\\"'):gsub('\n', '\\n') .. '"'
end

local function readState()
    local language = languages[readVar(VAR_LANGUAGE)]
    local cefr = levels[readVar(VAR_LEVEL)]
    if not language or not cefr then return nil end
    return {
        language = language, cefr = cefr,
        exposures = readVar(VAR_EXPOSURES),
        dictionaries = readVar(VAR_DICTIONARIES),
        exposureContext = readVar(VAR_LAST_EXPOSURE_CONTEXT),
        dictionaryContext = readVar(VAR_LAST_DICTIONARY_CONTEXT),
    }
end

local function addEvent(kind, context, delta, capturedAt, language, cefr)
    sequence = sequence + 1
    events[#events + 1] = {sequence = sequence, kind = kind, context = context,
                           delta = delta, capturedAt = capturedAt,
                           language = language, cefr = cefr}
end

local function renderEvents()
    local rendered = {}
    for _, event in ipairs(events) do
        rendered[#rendered + 1] = string.format(
            '    {"sequence": %d, "kind": %s, "context": %d, "delta": %d, "selected_language": %s, "cefr": %s, "captured_at": %s}',
            event.sequence, jsonString(event.kind), event.context, event.delta,
            jsonString(event.language), jsonString(event.cefr), jsonString(event.capturedAt))
    end
    return table.concat(rendered, ",\n")
end

local function writeSnapshot(state)
    local capturedAt = os.date("!%Y-%m-%dT%H:%M:%SZ")
    local body = string.format(
        '{\n  "schema_version": 2,\n  "source_id": %s,\n  "selected_language": %s,\n' ..
        '  "cefr": %s,\n  "exposure_count": %d,\n  "dictionary_count": %d,\n' ..
        '  "last_exposure_context": %d,\n  "last_dictionary_context": %d,\n' ..
        '  "session_id": %s,\n  "events": [\n%s\n  ],\n  "captured_at": %s\n}\n',
        jsonString(SOURCE_ID), jsonString(state.language), jsonString(state.cefr),
        state.exposures, state.dictionaries, state.exposureContext,
        state.dictionaryContext, jsonString(sessionId), renderEvents(),
        jsonString(capturedAt))
    local temporaryPath = OUTPUT_PATH .. ".tmp"
    local file, message = io.open(temporaryPath, "wb")
    if not file then
        console:error("Learner snapshot could not be opened: " .. tostring(message))
        return false
    end
    file:write(body)
    file:close()
    local backupPath = OUTPUT_PATH .. ".bak"
    os.remove(backupPath)
    local old = io.open(OUTPUT_PATH, "rb")
    if old then
        old:close()
        local backedUp, backupMessage = os.rename(OUTPUT_PATH, backupPath)
        if not backedUp then
            os.remove(temporaryPath)
            console:error("Learner snapshot backup failed: " .. tostring(backupMessage))
            return false
        end
    end
    local ok, renameMessage = os.rename(temporaryPath, OUTPUT_PATH)
    if not ok then
        os.rename(backupPath, OUTPUT_PATH)
        console:error("Learner snapshot could not be installed: " .. tostring(renameMessage))
        return false
    end
    os.remove(backupPath)
    return true
end

local function poll()
    local state = readState()
    if not state then return end
    if not previous then
        previous = state
        dirty = true
    else
        local capturedAt = os.date("!%Y-%m-%dT%H:%M:%SZ")
        if state.exposures > previous.exposures then
            addEvent("exposure", state.exposureContext,
                     state.exposures - previous.exposures, capturedAt,
                     state.language, state.cefr)
            dirty = true
        elseif state.exposures < previous.exposures then
            console:warn("Learner exposure counter moved backwards; starting a new baseline")
            dirty = true
        end
        if state.dictionaries > previous.dictionaries then
            addEvent("dictionary", state.dictionaryContext,
                     state.dictionaries - previous.dictionaries, capturedAt,
                     state.language, state.cefr)
            dirty = true
        elseif state.dictionaries < previous.dictionaries then
            console:warn("Learner dictionary counter moved backwards; starting a new baseline")
            dirty = true
        end
        if state.language ~= previous.language or state.cefr ~= previous.cefr then dirty = true end
        previous = state
    end
    if dirty and writeSnapshot(state) then dirty = false end
end

callbacks:add("frame", poll)
callbacks:add("start", poll)
callbacks:add("savedataUpdated", poll)
poll()
