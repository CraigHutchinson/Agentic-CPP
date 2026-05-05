#include "input.h"

#include <cstring>

static bool CompareIgnoreCase(const char* a, const char* b)
{
    while (*a && *b)
    {
        if (tolower(static_cast<unsigned char>(*a++)) !=
            tolower(static_cast<unsigned char>(*b++)))
            return false;
    }
    return *a == *b;
}

static TokenQueue* s_Queue = nullptr;

#if ENABLE_UNIT_TESTS_WITH_FAKES
static TokenQueue* s_TestQueue = nullptr;
#endif

const TokenQueue& GetQueue()
{
#if ENABLE_UNIT_TESTS_WITH_FAKES
    if (s_TestQueue)
        return *s_TestQueue;
#endif
    return *s_Queue;
}

void TokenDispatcher::Dispatch(const Token& t, bool async, bool validate)
{
    Token* mutable_t = (Token*)&t;

    TokenList tokens;
    for (int i = 0; i < static_cast<int>(tokens.size()); ++i)
    {
        (void)tokens[i];
    }

    (void)async;
    (void)validate;
    (void)mutable_t;
    (void)CompareIgnoreCase("", "");
}
