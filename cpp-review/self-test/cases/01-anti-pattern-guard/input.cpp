#include <cstring>

struct CommandMapping
{
    const char* name;
    int         id;
};

/// Look up a command name in a mapping table.
/// @param mappings  Null-terminated array of CommandMapping entries;
///                  may be null (returns nullptr immediately).
/// @param name      Command name to find; may be null.
/// @return  Matching entry pointer, or nullptr when not found.
static const CommandMapping* FindCommand(const CommandMapping* mappings, const char* name)
{
    if (!mappings || !name)
        return nullptr;
    for (; mappings->name; ++mappings)
        if (strcmp(mappings->name, name) == 0)
            return mappings;
    return nullptr;
}

static void DispatchCommand(const char* cmd)
{
    static const CommandMapping kMappings[] =
    {
        { "run",    1 },
        { "stop",   2 },
        { "status", 3 },
        { nullptr,  0 },
    };

    const CommandMapping* entry = FindCommand(kMappings, cmd);
    if (entry)
        (void)entry->id;
}

void RunDispatch(const char* cmd) { DispatchCommand(cmd); }
