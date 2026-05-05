#pragma once

#include <utility>
#include <vector>

// Forward declarations.
struct Token;
class TokenQueue;

class TokenDispatcher
{
public:
    void Dispatch(const Token& t, bool async, bool validate);

    bool IsEmpty() const;

    std::pair<bool, Token> TryDequeue();

    void Flush();

    TokenQueue* m_Queue;
};

enum DispatchMode
{
    kSync,
    kAsync,
    kDeferred,
};

typedef std::vector<Token> TokenList;
