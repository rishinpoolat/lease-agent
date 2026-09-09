# Layer 05 — Pipeline & Queue Architecture

Answers: *how does an upload become a reviewable result, and what's the
scaling/failure story?* This layer is the direct answer to the brief's "how
you structure code and data to scale" and "where it would break first at
scale."

## Why a queue at all (at this project's scale)

A synchronous request/response — API calls the model inline and returns the
result — is simpler, and would work for a demo. It's the wrong shape for
"production-level" because:

- Vision/text model calls are seconds, not milliseconds. A slow call blocks
  an API worker/connection for the whole request.
- There's no natural place to retry a transient model failure without either
  failing the user's upload or blocking longer.
- Upload throughput and AI-processing throughput are different scaling
  problems (many uploads can arrive in a burst; model processing is
  rate-limited and costs money per call) — coupling them means you can only
  scale them together.

RabbitMQ decouples the two: uploads are cheap and always fast; processing
happens at whatever rate the workers (and the model provider's rate limits)
can sustain.

## Flow

1. Client uploads a lease PDF or a set of photos.
2. API validates the upload, stores the file via a `Storage` interface (local
   disk in dev; swappable for a cloud object store like GCS/S3 in
   production), creates a `Job` row (`status = queued`), and publishes
   `{ job_id }` to the appropriate queue.
3. API returns `202 Accepted` with the `job_id` immediately — no blocking.
4. A worker process consumes from the queue, loads the job + file, calls the
   relevant `ModelProvider` capability ([[04-agent-boundaries]]), and for
   lease jobs also runs the rule engine ([[03-validation-rules]]).
5. Worker persists `LeaseField` / `Flag` / `RuleEvaluation` rows (lease jobs)
   or `PhotoReport` / `WorkOrder` rows (photo jobs), sets `Job.status = done`,
   and acks the message.
6. Frontend polls `GET /jobs/{id}` (simple interval poll is enough at this
   scale — no need for websockets/SSE here) until `done`, then the unit view
   reflects the new data.

## Queue topology

| Queue | Consumer | Purpose |
|-------|----------|---------|
| `lease.extraction` | worker (lease handler) | Part A pipeline |
| `photo.analysis` | worker (photo handler) | Part B pipeline |
| `lease.extraction.dlq` | none (inspection only) | messages that exhausted retries |
| `photo.analysis.dlq` | none (inspection only) | same, for photo jobs |

Two queues, not one generic "jobs" queue — lease and photo jobs have
different consumers, different failure characteristics, and (in production)
would scale independently.

## Failure handling

- On an exception in the handler: nack the message, let it requeue, up to a
  bounded retry count (tracked via a message header or a `Job.retry_count`
  column — pick one when implementing, don't do both).
- After the retry budget is exhausted: dead-letter to the `*.dlq` queue and
  set `Job.status = failed` with the error recorded. **Never silently drop a
  failed extraction** — a lease that failed to process and vanished is worse
  than one that visibly failed.
- Worker writes are keyed by `job_id` and are safe to re-run (idempotent) so
  an at-least-once redelivery doesn't create duplicate `LeaseField` rows —
  upsert/replace-by-`job_id`, not insert-only.

## Scale notes (for the README)

- This build: one RabbitMQ node, one worker replica per queue — correct for
  sample-data volume, not a production claim.
- Production: workers autoscale on queue depth (RabbitMQ management API
  exposes this directly); worker concurrency per replica is tuned to the
  model provider's rate limit, not to CPU count, since the bottleneck is the
  external API call, not local compute.
- The first real bottleneck at scale is almost certainly the model
  provider's rate limit / cost, not RabbitMQ or Postgres — say this
  explicitly in the README rather than implying infrastructure is the
  constraint.
