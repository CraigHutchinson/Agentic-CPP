#include <cstring>

// Imagine a lookup API with this declaration in its header:
//
//   /// Look up a command name in a mapping table.
//   /// @param mappings  Null-terminated array of CommandMapping entries;
//   ///                  may be null (returns nullptr immediately).
//   /// @param name      Command name to find; may be null.
//   /// @return  Matching entry pointer, or nullptr when not found.
//   const CommandMapping* FindCommand(const CommandMapping* mappings,
//                                    const char* name);
//
// The API documentation explicitly says both params *may* be null.
// An AI reviewer that reads only the API doc (not the call site) may flag:
//   "The API says mappings may be null; this caller does not guard against it."
// This case verifies that the input-source check suppresses that finding.

struct CommandMapping
{
    const char* name;
    int         id;
};

// Stub used only in this file.
static const CommandMapping* FindCommand(const CommandMapping* mappings, const char* name)
{
    if (!mappings || !name)
        return nullptr;
    for (; mappings->name; ++mappings)
        if (strcmp(mappings->name, name) == 0)
            return mappings;
    return nullptr;
}

// Call site: both arguments are constructed inline by the caller.
//   kMappings -- static const array, cannot be null.
//   cmd       -- const char* parameter; validated by the caller before this point.
// Neither argument can trigger the "may be null" path in the API contract.
static void DispatchCommand(const char* cmd)
{
    static const CommandMapping kMappings[] =
    {
        { "run",    1 },
        { "stop",   2 },
        { "status", 3 },
        { nullptr,  0 },    // sentinel
    };

    const CommandMapping* entry = FindCommand(kMappings, cmd);
    if (entry)
        (void)entry->id;
}

// Entry point used only to suppress "unused function" warnings in this snippet.
void RunDispatch(const char* cmd) { DispatchCommand(cmd); }
