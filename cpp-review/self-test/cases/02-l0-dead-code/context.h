#pragma once

/// Caches the application context string for the process lifetime.
class ContextCache
{
public:
    ContextCache();

    /// Return the cached context string, or nullptr before the first resolve.
    const char* Get() const;

private:
    const char* m_Value = nullptr;
};
