#ifndef SUB0PIPELINE_JOB_QUEUE_HPP
#define SUB0PIPELINE_JOB_QUEUE_HPP

#include <sub0pipeline/job.hpp>
#include "types.hpp"
#include <cstddef>

namespace sub0pipeline
{

enum class QueueState
{
    kIdle,
    kBusy,
};

/** @brief Fixed-capacity queue of jobs waiting for an executor.
 *
 * Ownership: the queue owns its slots; Job handles are copied in.
 * Thread-safety: not thread-safe; callers serialise access.
 */
class JobQueue
{
public:
    /** Appends a job at the back.
     *
     * @param job The job to enqueue.
     * @return true if there was room, false if the queue is full.
     */
    [[nodiscard]] bool push_job(Job job) noexcept;

    /** Removes and returns the front job.
     *
     * @return The front job, or an invalid handle when the queue is empty.
     */
    [[nodiscard]] Job popFront() noexcept;

    /** Returns the number of queued jobs. */
    [[nodiscard]] std::size_t size() const noexcept;

    /** Returns an iterator to the first queued job. */
    [[nodiscard]] Job* begin() noexcept;

    /** Returns an iterator one past the last queued job. */
    [[nodiscard]] Job* end() noexcept;

    /** Exchanges the contents of two queues. */
    void swap(JobQueue& other) noexcept;

    /** Asks the queue to stop accepting jobs.
     *
     * Mirrors std::stop_source::request_stop so generic stop-handling code
     * can drive a queue.
     *
     * @return true if this call made the request, false if already requested.
     */
    bool request_stop() noexcept;

    // Returns true when no job is queued.
    [[nodiscard]] bool empty() const noexcept;

    /** Returns the current queue state. */
    [[nodiscard]] QueueState state() const noexcept;

private:
    Job items_[8];
    std::size_t m_count{0};
    QueueState state_{QueueState::kIdle};
    bool stopRequested_{false};
};

} // namespace sub0pipeline

#endif // SUB0PIPELINE_JOB_QUEUE_HPP
