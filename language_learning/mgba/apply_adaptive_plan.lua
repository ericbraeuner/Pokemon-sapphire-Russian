-- Select compiled learner dialogue variants from an adaptive runtime plan.
-- In mGBA 0.10+, set PLAN_PATH, then load this file in Tools > Scripting.

local PLAN_PATH = "adaptive-runtime.lua"

local SAVE_BLOCK1 = 0x02025734
local VARS_OFFSET = 0x1340
local VARS_START = 0x4000
local VAR_CONTEXT = 0x40F3
local VAR_ADAPTIVE_VARIANT = 0x40F9
local previousContext = nil

local function address(id)
    return SAVE_BLOCK1 + VARS_OFFSET + 2 * (id - VARS_START)
end

local function readVar(id)
    return emu:read16(address(id))
end

local function writeVariant(value)
    -- This is the only save variable this loader writes.
    emu:write16(address(VAR_ADAPTIVE_VARIANT), value)
end

local function loadSelections()
    local chunk, message = loadfile(PLAN_PATH)
    if not chunk then
        console:warn("Adaptive plan unavailable: " .. tostring(message))
        return {}
    end
    local ok, plan = pcall(chunk)
    if not ok or type(plan) ~= "table" or type(plan.selections) ~= "table" then
        console:warn("Adaptive plan is invalid")
        return {}
    end
    return plan.selections
end

local function poll()
    local context = readVar(VAR_CONTEXT)
    if context == previousContext then return end
    previousContext = context
    if context == 0 then
        writeVariant(0)
        return
    end
    local selection = loadSelections()[context]
    if selection == 1 or selection == 2 or selection == 3 then
        writeVariant(selection)
    else
        writeVariant(0)
    end
end

callbacks:add("frame", poll)
console:log("Adaptive learner plan loader started")
