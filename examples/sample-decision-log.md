# Decision Log: feature/add-rate-limiting

**Generated:** 2024-01-20T14:30:00
**Branch:** `feature/add-rate-limiting`

---

## Problem Statement

Implement rate limiting to prevent API abuse and ensure fair usage across all users.

### Initial Context

The API was experiencing abuse from a few users making excessive requests. Requirements: Rate limit based on API key, 100 requests per minute per key, return 429 status code when exceeded.

## Attempts and Iterations

### Attempt 1: In-memory rate limiting with simple counter

**Outcome:** rejected

**Learnings:** In-memory solution doesn't work across multiple server instances. Rate limits would be per-instance, not global.

**Evidence:**
- [commit 7a3f1b2] "Add simple rate limiting middleware"
- [shell: npm install express-rate-limit]
- [AI assistant] "For distributed systems, you'll need a shared store like Redis"
- [commit 9c2e4d1] "Revert in-memory rate limiting"

### Attempt 2: Redis-based rate limiting

**Outcome:** successful

**Learnings:** Redis provides atomic operations and works across instances. The `INCR` and `EXPIRE` commands handle the counter and TTL perfectly.

**Evidence:**
- [commit b5f6a3c] "Add Redis client configuration"
- [shell: npm install redis]
- [commit d8e2b1a] "Implement Redis-based rate limiting"
- [shell: npm test] "All tests passing"

## Final Solution

Redis-based rate limiting using atomic INCR operations with sliding window approach. Each API key gets a Redis key with TTL of 60 seconds. Requests increment the counter, and if it exceeds 100, return 429.

### How It Works

1. Extract API key from request header
2. Generate Redis key: `ratelimit:{api_key}:{timestamp_window}`
3. Increment counter atomically with `INCR`
4. Set expiry to 60 seconds if new key
5. If counter > 100, return 429 Too Many Requests
6. Otherwise, allow request and include `X-RateLimit-*` headers

**Evidence:**
- [commit d8e2b1a] "Implement Redis-based rate limiting"
- [commit e3a7c5f] "Add rate limit headers"
- [commit f1b9d2e] "Add integration tests for rate limiting"

## Rationale and Tradeoffs

Redis chosen for distributed rate limiting. Sliding window approach chosen for fairness.

### Alternatives Considered
- In-memory rate limiting (rejected: doesn't work with multiple instances)
- Database-based rate limiting (rejected: too slow, adds load to DB)
- Token bucket algorithm (rejected: more complex, sliding window sufficient)

### Tradeoffs
- **Performance vs Accuracy:** Sliding window is approximate but much faster than exact counting
- **Complexity:** Requires Redis infrastructure (already in use for caching)
- **Cost:** Minimal - Redis operations are very cheap

## Risks and Follow-ups

### Risks
- Redis outage would disable rate limiting entirely
- Need to monitor Redis memory usage as we scale

### Follow-up Work
- Implement Redis failover for high availability
- Add CloudWatch alarms for Redis metrics
- Consider adding different rate limits for different endpoint types (e.g., read vs write)

### Technical Debt
- Hardcoded rate limit (100/min) should be configurable per API tier
- Need to add admin endpoint to view/reset rate limits

---

## Appendix: Full Timeline

- **2024-01-20 10:00:00** [commit 7a3f1b2] Add simple rate limiting middleware
- **2024-01-20 10:15:00** [shell] `npm install express-rate-limit`
- **2024-01-20 10:30:00** [AI user] How do I implement rate limiting for multiple servers?
- **2024-01-20 10:31:00** [AI assistant] For distributed systems, you'll need a shared store like Redis. The sliding window algorithm works well with Redis INCR operations...
- **2024-01-20 11:00:00** [commit 9c2e4d1] Revert in-memory rate limiting
- **2024-01-20 11:15:00** [commit b5f6a3c] Add Redis client configuration
- **2024-01-20 11:20:00** [shell] `npm install redis`
- **2024-01-20 12:00:00** [commit d8e2b1a] Implement Redis-based rate limiting
- **2024-01-20 13:00:00** [commit e3a7c5f] Add rate limit headers
- **2024-01-20 13:30:00** [shell] `npm test`
- **2024-01-20 14:00:00** [commit f1b9d2e] Add integration tests for rate limiting
