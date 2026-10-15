-- Export learner settings and counters from Pokémon Sapphire to JSON.
-- In mGBA 0.10+, open Tools > Scripting, load this file, and leave it running.

local OUTPUT_PATH = "learner-snapshot.json"
local SOURCE_ID = "pokemon-sapphire-learner-save"
local EXPORT_INTERVAL_FRAMES = 300

local SAVE_BLOCK1 = 0x02025734
local VARS_OFFSET = 0x1340
local VARS_START = 0x4000
local VAR_LANGUAGE = 0x40F0
local VAR_LEVEL = 0x40F1
local VAR_EXPOSURES = 0x40F5
local VAR_DICTIONARIES = 0x40F6

local languages = {[1] = "ru", [2] = "de"}
local levels = {[1] = "A1", [2] = "A2", [3] = "B1", [4] = "B2", [5] = "C1", [6] = "C2"}
local lastSignature = nil
local frameCounter = 0

local function readVar(id)
    return emu:read16(SAVE_BLOCK1 + VARS_OFFSET + 2 * (id - VARS_START))
end

local function jsonString(value)
    return '"' .. value:gsub('\\', '\\\\'):gsub('"', '\\"'):gsub('\n', '\\n') .. '"'
end

local function snapshot()
    local language = languages[readVar(VAR_LANGUAGE)]
    local cefr = levels[readVar(VAR_LEVEL)]
    if not language or not cefr then
        return nil
    end
    local exposures = readVar(VAR_EXPOSURES)
    local dictionaries = readVar(VAR_DICTIONARIES)
    local capturedAt = os.date("!%Y-%m-%dT%H:%M:%SZ")
    local signature = table.concat({language, cefr, exposures, dictionaries}, ":")
    local body = string.format(
        '{\n  "schema_version": 1,\n  "source_id": %s,\n  "selected_language": %s,\n' ..
        '  "cefr": %s,\n  "exposure_count": %d,\n  "dictionary_count": %d,\n' ..
        '  "captured_at": %s\n}\n',
        jsonString(SOURCE_ID), jsonString(language), jsonString(cefr),
        exposures, dictionaries, jsonString(capturedAt))
    return body, signature
end

local function exportIfChanged()
    local body, signature = snapshot()
    if not body or signature == lastSignature then
        return
    end
    local temporaryPath = OUTPUT_PATH .. ".tmp"
    local file, message = io.open(temporaryPath, "wb")
    if not file then
        console:error("Learner snapshot could not be opened: " .. tostring(message))
        return
    end
    file:write(body)
    file:close()
    os.remove(OUTPUT_PATH)
    local ok, renameMessage = os.rename(temporaryPath, OUTPUT_PATH)
    if not ok then
        console:error("Learner snapshot could not be installed: " .. tostring(renameMessage))
        return
    end
    lastSignature = signature
    console:log("Learner snapshot updated: " .. signature)
end

callbacks:add("frame", function()
    frameCounter = frameCounter + 1
    if frameCounter >= EXPORT_INTERVAL_FRAMES then
        frameCounter = 0
        exportIfChanged()
    end
end)

callbacks:add("start", exportIfChanged)
callbacks:add("savedataUpdated", exportIfChanged)
exportIfChanged()
