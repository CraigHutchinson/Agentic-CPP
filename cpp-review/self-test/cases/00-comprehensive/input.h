#pragma once

#include <utility>
#include <vector>

// Forward declarations.
struct Token;
class TokenQueue;

// Defect Q1: No class docblock on TokenDispatcher.
class TokenDispatcher
{
public:
    // Defect L2-A: boolean selector parameters (async, validate) make
    // call sites unreadable; prefer an options struct or named overloads.
    void Dispatch(const Token& t, bool async, bool validate);

    // Defect L3-A: pure observer -- missing [[nodiscard]].
    bool IsEmpty() const;

    // Defect L2-B: std::pair<bool, Token> return -- prefer a named struct
    // or std::optional<Token>.
    std::pair<bool, Token> TryDequeue();

    void Flush();

    // Defect Q5: raw pointer member with no ownership annotation
    // (// owning or // non-owning).
    TokenQueue* m_Queue;
};

// Defect L3-B: unscoped enum; use enum class.
enum DispatchMode
{
    kSync,
    kAsync,
    kDeferred,
};

// Defect L3-C: typedef alias; use 'using' instead.
typedef std::vector<Token> TokenList;
