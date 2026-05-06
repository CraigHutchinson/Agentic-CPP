#include "context.h"

#include <cassert>

void TestContextCacheIsNullBeforePopulate()
{
    ContextCache cache;
    assert(cache.Get() == nullptr);
}

void TestContextCacheGetAfterPopulate()
{
    ContextCache cache;
    cache.Populate("app-v2");
    assert(cache.Get() != nullptr);
}
