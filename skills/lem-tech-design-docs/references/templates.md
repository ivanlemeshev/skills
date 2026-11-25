# Templates

Use these templates as the start of a structure proposal. They are not final outlines. Change them to agree with the material: change the sequence, remove, add, and size sections for the decision.

## Change a template

- **Start with what the reader needs**: Put the decision, request, or summary first. Put the background after it.
- **Sort by risk and uncertainty**: Give the most space and the first position to the most difficult or least certain parts.
- **Add sections for this case**: For example, legacy migration, multi-tenancy, compliance, event contracts, cost, vendor dependency, and data backfill.
- **Remove empty sections**: If a section has no specific content, remove it. Do not fill it. If an important section has no content, name it as a gap.
- **Split or merge by quantity**: Split a section that is longer than one or two screens. Merge small adjacent sections.
- **Move reference material to appendices**: Put long endpoint tables, schemas, and checklists in appendices.
- **Write one document for each decision audience**: If API consumers and the platform team need different information, propose a short consumer document and an internal design document.

## API design document

1. **Summary**: The purpose of the API, its callers, and the decision or request.
2. **Goals and non-goals**
3. **Consumers and use cases**: The three to five most important flows. Write each flow as a short scenario.
4. **Resource model**: Entities, identifiers, relations, and lifecycle states.
5. **Endpoints or operations**: Method, path, purpose, authentication, request, response, and errors. Give a table and one full example for each complex operation.
6. **Conventions**: Names, pagination, filters, sort order, idempotency, versioning, date, time, and money formats, and null compared to missing values.
7. **Errors**: Error envelope, codes, and the codes that clients can retry.
8. **Authentication and authorization**: Scheme, scopes or roles, and tenant isolation.
9. **Non-functional requirements**: Rate limits, latency targets, payload limits, caching, and consistency guarantees.
10. **Compatibility and change**: Breaking and non-breaking changes, deprecation policy, and migration for current clients.
11. **Security and privacy**: Data classification, personal data handling, and abuse cases.
12. **Observability and support**: Logs, trace IDs, metrics, and how consumers find problems.
13. **Alternatives**
14. **Open questions**

## Backend or system design document (RFC)

1. **Summary and context**: The problem, why it is necessary now, and who it affects.
2. **Goals, non-goals, and constraints**
3. **Requirements**: Functional requirements and quantified non-functional requirements (load, latency, availability, durability, and cost).
4. **Proposed design**: Architecture overview and diagram, components and their responsibilities, and data flow for the main scenarios.
5. **Data model and storage**: Schemas, indexes, retention, consistency model, and migration.
6. **Interfaces**: Internal APIs, events and queues, and contracts with other teams.
7. **Failure modes and resilience**: What can fail, how you find the failure, degraded behavior, retries, backpressure, and recovery.
8. **Security**: Authentication and authorization, secrets, data protection, and trust boundaries.
9. **Scalability and capacity**: Estimates with their assumptions.
10. **Observability**: Metrics, logs, traces, alerts, and SLOs.
11. **Rollout**: Phases, feature flags, migration, and rollback.
12. **Test strategy**
13. **Alternatives and decision record**
14. **Risks and open questions**
15. **Ownership and operations**: Who operates the system, on-call, and runbooks.

## Architecture decision record (ADR)

Record one decision in one page.

1. **Title**: A short statement of the decision.
2. **Status**: Proposed, accepted, deprecated, or superseded. For a superseded ADR, give a link to the new ADR.
3. **Context**: The problem, the constraints, and the conditions that make the decision necessary.
4. **Decision**: What the team will do. Use direct statements.
5. **Alternatives**: Each option and the reason to reject it.
6. **Consequences**: The good and bad results, new risks, and follow-up work.

## Technical plan or project plan

1. **Result**: What is true when the work is complete, and how you measure it.
2. **Scope**: Items in scope, out of scope, and for a later time.
3. **Approach**: A summary of the technical design with a link to the design document.
4. **Work breakdown**: Workstreams, tasks, and sized estimates. Give the basis and the confidence for each estimate.
5. **Sequence and dependencies**: The critical path, external dependencies, and what blocks each item.
6. **Milestones**: Each milestone has a date and an exit criterion that you can verify.
7. **Roles and ownership**
8. **Risks**: Probability, impact, mitigation, and the trigger to escalate.
9. **Rollout and cutover plan**: Include rollback.
10. **Tests and acceptance**
11. **Communication and review points**
12. **Open questions and assumptions**
