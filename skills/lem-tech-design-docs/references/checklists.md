# Verification checklists

Mark each item as covered, not applicable (with the reason), or gap.

## Correctness for all document types

- Each endpoint, field, type, limit, version, and name agrees with the source of truth.
- Each item has the same name in all locations. Numbers in text, tables, and diagrams agree.
- Examples are valid. JSON and YAML parse. SQL has correct syntax. Requests agree with the schema. Responses agree with the status codes.
- Status codes, HTTP methods, and idempotency statements are correct. For example, PUT and DELETE are idempotent, 201 comes with a `Location` header, and the choice between 409 and 422 is deliberate.
- Estimates show the calculation and the assumptions. The orders of magnitude are possible.
- The selected technology and design support the statements about consistency, ordering, delivery guarantees (at-least-once, exactly-once), and transactions.
- Diagrams show each component that the text names. The text names each component that the diagrams show.
- Dates, owners, and dependencies are real or have an `[OPEN]` marker.
- No statement is stronger than its evidence. Use "always," "never," or "guaranteed" only when the statement is true.

## API gaps

- Resource model and IDs; create, update, and delete behavior; partial update method
- Pagination, filters, and sort order; maximum page size
- Idempotency for unsafe operations; retry instructions
- Error format with stable, machine-readable codes
- Authentication and authorization for each operation; tenant isolation; scopes
- Rate limits and quotas; payload size limits; timeouts
- Versioning and deprecation; backward compatibility rules
- Concurrency control (ETags, optimistic locking)
- Asynchronous operations (job resources, webhooks, callbacks); webhook signatures and retries
- Time zones, formats, enum extension, null compared to absent values
- Documentation for consumers: authentication setup, examples, changelog
- Observability: request IDs, audit logs

## Backend and system design gaps

- Quantified requirements and the load assumptions for them
- Data ownership, schema, indexes, growth, retention, backup, and restore
- Consistency model and transaction limits across components
- Failure modes for each dependency: timeouts, retries with backoff and jitter, circuit breakers, backpressure, poison messages
- Single points of failure; multi-region or multi-zone assumptions; disaster recovery targets (RPO and RTO)
- Security: trust boundaries, secrets, encryption at rest and in transit, least privilege, audit
- Migration from the current system; data backfill; dual-write or cutover method
- Rollout, feature flags, and rollback; compatibility during rolling deployments
- Observability: SLIs, SLOs, dashboards, alerts, tracing
- Cost drivers and cost estimate
- Operational ownership, on-call, runbooks
- Tests: unit, integration, load, failure injection
- Alternatives and the reasons to reject them

## ADR gaps

- One decision only; the title states the decision
- Status, date, and decision owners
- Context that tells why the decision is necessary now
- At least one real alternative with the reason to reject it
- Good and bad consequences; new risks and follow-up work
- Links to related ADRs, design documents, and the ADR that this ADR supersedes

## Plan gaps

- Measurable result and success criteria
- Items that are not goals and items for a later time
- An owner and a size for each task; the basis for each estimate
- Dependencies on other teams and external vendors, with dates
- The critical path; the slack and buffer time
- Milestones with exit criteria that you can verify
- Risks with mitigation and escalation triggers
- Rollout, cutover, and rollback plan
- Test and acceptance method
- Decision points and the person who decides
- Assumptions that are listed and that you can test
