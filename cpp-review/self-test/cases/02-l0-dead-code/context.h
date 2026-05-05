#pragma once

/// Caches the application context string for the process lifetime.
///
/// Intended for use with `Singleton<T>` once a production caller is wired.
/// In this commit no production file includes or calls this class;
/// it ships as dead code on trunk.
class ContextCache
{
public:
    ContextCache();

    /// Return the cached context string, or nullptr before the first resolve.
    const char* Get() const;

private:
    const char* m_Value = nullptr;
};

// Note: the only file that #includes this header in the current commit is
// ContextCacheTests.cpp. No production accessor calls ContextCache::Get().
