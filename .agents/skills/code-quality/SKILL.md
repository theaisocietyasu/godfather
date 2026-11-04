---
name: code-quality
description: >-
  Run a disciplined quality pass over existing code, or lay out new code: naming and file/folder
  structure that a new engineer can navigate, modular-monolith boundaries, reuse of what the
  project already depends on, data-driven registries over enumerated one-offs, and removing dead
  code, silent fallbacks and fake data. Use when asked to clean up, refactor, reorganize, rename,
  de-duplicate, make it modular, make it production-ready, decide where code or a file should
  live, or review code for quality. Not a bug hunt: use systematic-debugging for that.
---

# Code quality

A quality pass is mostly subtraction and consistency, not cleverness. The goal is a codebase that is easy to read, safe to change, honest about what it does, and built to survive growth. A new engineer should be able to open it, guess where a file lives, and read a stack trace path to know which part of the system failed.

Ground structural calls in established principles (high cohesion, low coupling, separation of concerns, one reason to change per module), not taste. For module interface design, use the `codebase-design` skill.

## Prime directive

Preserve behavior, unless the behavior is itself the bug. The one deliberate exception is code that hides failure (silent fallbacks, mock data, swallowed errors): there, failing honestly is the fix. If you find a real bug, say so and keep the fix out of the refactor.

## Workflow

Work in small, verifiable units, never one sweeping rewrite.

1. **Map before you touch.** Read the folder and the project's AGENTS.md, CLAUDE.md or ARCHITECTURE.md. Read the dependency manifests so you know what the project already has. Find every reference to a symbol or file across the tree (including dynamic and string-based ones) before calling anything dead.
2. **Change one concern at a time.** Rename, then stop. Extract, then stop. Each step leaves the code working.
3. **Prove it still works.** Run the project's checks (format, lint, types, tests) after each meaningful change. If the path has no tests, exercise it and say so.
4. **Migrate callers, then delete.** Update every reference first. Delete the old thing only when nothing points at it. Move files with `git mv` so history follows them.

Confirm with the person before any change that touches many callers, restructures folders, renames files in bulk, or adds a dependency.

## 1. Naming

- **Name the role, not today's instance.** `fetch_user` scales; `fetch_user_from_postgres_v2` bakes in a vendor and a version that will rot. Interfaces are named for the capability (`VectorReader`), implementations for the technology (`hashmap.rs`, `cuda.rs`), so a new backend is a new file, not a new branch.
- **Name the category, scale by registration.** When the system grows by adding more of the same kind of thing (tools, sources, providers, scorers, steps), model the kind once as an interface and make the instances data: a registry the code iterates or looks up. Adding the next one should cost one file plus one registry entry, not edits to a switch in three places.
- **One name, one meaning.** Before naming a module, check the word is not already used for something else in the tree. Repeating a word across layers is fine when it means the same thing each time (`config/embedding`, `errors/embedding`).
- **One concept, one word.** Don't let `user`, `account` and `profile` mean the same thing in three files.
- **Not too vague either.** `data`, `handler`, `manager`, `helpers` and a `utils` that does everything are as bad as over-specific names. General enough to scale, specific enough to be unambiguous.
- **No magic values.** A number or string with meaning is a named constant, defined once.

## 2. Files and folders

- **Nest by domain.** A folder is named for what its code is about (billing, auth, search, storage), never for a language, a framework layer alone, or one customer's topic.
- **Let the path carry context.** A file inside `sources/` doesn't need `source` in its name.
- **No flat folders, no one-file folders.** Past about seven sibling files with a natural grouping, split into domain subfolders. Never invent a bucket to hit a count.
- **One vocabulary across parallel trees.** The same domain name appears in `types/<domain>`, `services/<domain>`, `tests/<domain>`, so finding one piece of a domain finds the rest.
- **One canonical path per item.** Index files (`mod.rs`, `__init__.py`, `index.ts`) re-export; they don't define things. No module re-exports another module's contents under a second path.
- **One casing convention** per language across the tree, following the language's standard.
- **Keep generated trees in the generator's layout** (for example a component library's `ui/` folder), so regeneration keeps working.

## 3. Modular monolith boundaries

- **One deployable, many modules.** Each module owns one domain, its data and its public interface. Other modules use only that interface, never its internals or its tables.
- **Dependencies point one way.** Write the layering down (a short diagram in ARCHITECTURE.md) and enforce it with a check script or lint rule where the language allows. A reverse import is a layering violation, not a shortcut.
- **Keep transport and vendors at the edges.** Core logic doesn't know about HTTP status codes or a vendor SDK's types. Those live in the adapter module that talks to them.
- **Split a module when it mixes responsibilities,** not because it's long. After splitting, each piece is nameable in one sentence; if not, the seam was wrong.
- **A change that moves a boundary or closes off an option gets a short decision record** (docs/decisions or an ADR).

## 4. Reuse

- **Search before you write.** Extend an existing function rather than cloning it.
- **Duplication beats the wrong abstraction.** Extract on the third real repeat, and only when the cases share a shape. Two implementations justify an interface; one is speculation.
- **Use what the manifest already has.** A hand-rolled HTTP client, parser, retry loop or date helper next to an installed library that does the job is cruft. Migrate callers, then delete it and any dependency nothing uses anymore.
- **Prefer, in order:** delete it, the standard library, a dependency the project already has, a small owned helper, a new dependency.
- **A new dependency is an addition, not a cleanup.** Confirm first. Justify it by what it deletes or fixes, weigh size, maintenance, license and how hard it is to back out, and adopt it one module at a time.

## 5. Cleaning and honesty

- **Silent fallbacks.** Discarded errors, defaults returned on failure, a catch-all that returns "no results". These turn a loud bug into an invisible wrong answer. Remove the mask so the failure surfaces. Keep documented, intentional defaults.
- **One way to do a thing.** No second spelling of a name, no fallback that quietly serves something other than what was asked. If it can't do what was asked, it returns an error saying so.
- **Mock data in real paths.** Hardcoded sample responses, stubs pretending an integration works, a health check that checks nothing. Remove them or make them fail loudly. Honest test fixtures stay.
- **Dead code.** Unreferenced functions, commented-out blocks, unreachable branches, config knobs nothing reads, options always passed the same value. Prove it's unused, then delete it; git remembers.
- **Unused pass-throughs.** Wrappers and re-exports nothing outside the module consumes.

## What not to do

- Don't rename for taste. A rename must make a future change cheaper; say which change.
- Don't reformat unrelated code. It buries the real change.
- Don't touch a public API without saying so.
- Don't add abstraction for a case that doesn't exist yet.

## Done means

A new engineer could find their way around the folder. Names describe roles, files and folders are domain-focused, boundaries point one way, nothing behaves differently except failures that were hidden before, every deletion is proven unused, no dependency was added without agreement, and the project's checks pass. Report what changed and why each change makes a future edit cheaper.
