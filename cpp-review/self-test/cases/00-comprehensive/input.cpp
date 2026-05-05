#include "input.h"

#include <cstring>

// Defect REINVENTION: CompareIgnoreCase duplicates an existing project
// utility (e.g. StrIEquals in Word.h or a generic AsciiCaseInsensitiveEquals).
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

// Defect TESTABILITY: file-static with a test-build bypass.
// The ENABLE_UNIT_TESTS_WITH_FAKES branch is the tell -- the author already
// conceded this design is testability-hostile.
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
    // Defect L3-D: C-style cast -- use static_cast<> or reinterpret_cast<>.
    Token* mutable_t = (Token*)&t;

    // Defect L3-E: index-based loop where range-for suffices.
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
