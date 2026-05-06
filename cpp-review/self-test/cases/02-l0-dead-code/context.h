#pragma once

/** Caches the resolved application context string for the process lifetime.
 *
 * Ownership:     non-owning; the returned pointer is valid for the life of
 *                the backing store passed to Populate().
 * Thread-safety: not thread-safe.
 */
class ContextCache
{
public:
    ContextCache() = default;

    /// Store the context string. Must be called before Get().
    void Populate(const char* value) noexcept;

    /// Return the cached context string, or nullptr before Populate() is called.
    [[nodiscard]] const char* Get() const noexcept;

private:
    const char* m_Value = nullptr; // non-owning
};
