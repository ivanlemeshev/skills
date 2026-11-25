---
name: lem-tech-design-docs
description: "Write, structure, verify, and edit technical design documents for API design, backend or system design, and technical or project plans. Use a fixed sequence: propose the structure, write from real sources, verify correctness and find gaps, then edit the prose without changes to technical content. Use this skill when the user wants to write, review, or complete an API spec, API design doc, backend or architecture design doc, RFC, ADR, technical plan, implementation plan, roadmap, or project plan. Also use it when the user asks to check a design doc for gaps, verify its correctness, or make it sound less like AI text. Use it even when the user does not name the document type."
license: MIT
---

# Technical design documents

Use this skill to write design and planning documents that have a clear structure, correct facts, full coverage, and clear prose.

Do the stages in sequence. Start at the stage that the request needs. Stage 0 tells which stages to do. Do not edit the prose before you verify the content. Edited text that has errors makes the errors more difficult to find.

## Stage 0: Collect the input

Find this information in the request and in the attached material. Ask only for information that is missing. Ask one question at a time.

1. **Document type**: API design, backend design, plan, architecture decision record (ADR), or a mix. For a mix, use one document with sections from each template. The type is the input for Stage 1. It does not set the final structure.
2. **Audience and decision**: Identify the readers. Identify what they must decide or do after they read the document.
3. **Sources of truth**: Code, OpenAPI or proto files, schemas, tickets, notes, and existing documents. Read them before you write. If there are no sources, tell the user. The document will then have more `[OPEN]` markers.
4. **Request scope**: Select the stages for the request:
   - **New document**: Do Stages 1 to 5.
   - **Restructure or complete a draft**: Do Stages 1 to 5. In Stage 1, compare the draft to the template. Do not write a new draft.
   - **Review, gap check, or correctness check**: Do Stage 3, then Stage 5. Do not change the structure or the text. Give the problems and the proposed corrections. Change the document only if the user asks.
   - **Wording edit only**: Do the correctness check in Stage 3, then Stages 4 and 5. Tell the user about the errors that you find. Do not correct technical content without approval.
   - **Unclear scope**: Ask the user which result they need.

## Stage 1: Propose the structure

Do not copy a template without changes. Examine the material and propose a structure for this case. Get approval before you write. Do not wait for approval only if the user told you to continue without questions.

1. **Examine**: Find the main message. Find who decides what. Find the complex or high-risk parts and the routine parts. Find where the sources have good coverage and where they have little information.
2. **Start from the nearest template** in `references/templates.md`. Then change it:
   - Put the decision or the request first. Put the background after it.
   - Remove sections that do not help this case.
   - Add sections that this case needs. For example, add a migration section to replace a legacy system, or a data contract section for an event-driven design.
   - Split or merge sections by the quantity of content.
3. **Show the proposal** as a numbered outline. Use one line for each section. Tell what the section contains and why it is there or why it moved. Add a short list of sections that you removed on purpose. Add a list of possible gaps: sections that will have little content because source material is missing.
4. **If a draft exists**, compare the current structure to the proposed structure. Show which sections move, merge, split, are removed, or are missing. Do not write new text yet.
5. Ask one short question for approval or changes. Then keep the outline and write to it.

Make the structure size agree with the decision size:

- For an ADR, write one page about one decision.
- For a small API change or plan, write one or two pages.
- For a typical feature, write a short document with some sections.
- Use the full template only for large, cross-team, or high-risk designs.

## Stage 2: Write from evidence

Use the outline that the user approved in Stage 1.

- Write only what the sources support. Each specific fact must come from a source or from the user. Specific facts include endpoints, fields, limits, SLAs, owners, dates, and versions.
- If a fact is unknown, write `[OPEN: question, person who can answer]`. Do not invent values.
- For each decision, record the alternatives and the reason to reject each one. Do not record only the result.
- Add examples where they remove ambiguity. Examples include requests and responses, sequences, and schema parts.

## Stage 3: Verify correctness and find gaps

Do the two checks below with `references/checklists.md`. Do the checks. Do not only show the checklist.

### Correctness check

- Compare each specific statement to the sources. If tools are available, run or compile the code and spec examples. For example, validate JSON and YAML, lint OpenAPI files, and check SQL syntax.
- Check that the document agrees with itself. Names, types, status codes, numbers, and diagrams must be the same in all locations.
- Check that the design supports each statement about capacity, latency, consistency, and failure. Identify statements that have no support.
- Check versions, library behavior, and references to standards. If you are not sure and a search tool is available, search to verify.

### Gap check

- Do each item in the checklist for the document type. Mark each item as covered, not applicable (with the reason), or gap.
- Find questions that readers will ask and that the document does not answer. Look at failure modes, migration, rollout, ownership, security, observability, cost, dependencies, and items that are out of scope.

### Stage 3 output

Correct the problems that the sources let you correct. Then add a short **Verification notes** section. Keep it outside the final document, unless the user wants it in the document. Include:

- The facts that you verified and how you verified them.
- The problems that you corrected.
- The `[OPEN]` items that remain, in sequence from the highest risk.
- The assumptions that you made.

Tell the truth about what you did not verify.

## Stage 4: Edit the prose

Do this stage only after Stage 3. Use `references/humanize.md`.

Change the words. Do not change technical content. Code, identifiers, paths, endpoints, field names, numbers, units, versions, quoted errors, and diagram labels must stay exactly the same. After you edit, read the document again. Make sure that no technical fact changed, was added, or was removed.

## Stage 5: Deliver

- Give the finished document in the format that the user asked for. For a short document, put it in the reply. For a longer document, use a file, such as Markdown, or the document tool that your environment supplies. Use Word or PDF only if the user asks for it.
- For a review, give the problems in sequence from the highest risk. Give a proposed correction for each problem. Do not give the full document, unless the user asks for it.
- After the document, add the verification notes and a short list of the `[OPEN]` items that remain.
- If the user gives a house style or a template, use it in place of the defaults in this skill.
