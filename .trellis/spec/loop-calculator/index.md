# Loop Calculator Spec Index

> Load these specs before changing Loop Calculator backend, frontend, product-data, or calculation behavior.

## Project Specs

- [Architecture](./architecture.md): package boundaries, runtime surfaces, and ownership rules.
- [Code Style](./code-style.md): Python, FastAPI, Vue, TypeScript, and verification conventions.
- [Database Naming](./database-naming.md): product-data naming, SQLite/API field rules, and migration checks.

## Required Baseline

Always read root `AGENTS.md` first. It is the canonical agent entry point for setup, test commands, and non-negotiable architecture rules.

## Pre-Development Checklist

- [ ] Identify whether the task touches pure calculation logic, backend API/storage, frontend UI/state, or data import.
- [ ] Read the matching spec file above and the relevant source module before editing.
- [ ] If calculation behavior changes, plan a focused test update before implementation.
- [ ] If data import/merge behavior changes, read `数据库合并去重机制.md`.
- [ ] Keep unrelated dirty worktree changes untouched.

## Quality Check

- [ ] Run the smallest meaningful check for the changed files.
- [ ] Record blocked checks with the exact command and failure reason.
- [ ] Update `.trellis/workspace/` with session progress, pitfalls, and next steps before ending a significant task.
