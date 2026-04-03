# Contributing to Atelier Pipeline

Thank you for your interest in contributing to Atelier Pipeline, a multi-agent
orchestration system for AI-powered IDEs. This project is licensed under
[Apache 2.0](LICENSE).

## Code of Conduct

All participants are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md).
Be respectful, constructive, and inclusive.

## Reporting Bugs

Found a bug? Please
[open a bug report](https://github.com/robertsfeir/atelier-pipeline/issues/new?template=bug_report.yml).

Include:
- A clear description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Your environment (OS, shell, Node.js version, IDE)

## Suggesting Features

Have an idea?
[Open a feature request](https://github.com/robertsfeir/atelier-pipeline/issues/new?template=feature_request.yml).

Describe the use case and the problem it solves. Concrete examples help.

## Security Vulnerabilities

Do **not** open a public issue for security vulnerabilities. See
[SECURITY.md](SECURITY.md) for responsible disclosure instructions.

## Development Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/robertsfeir/atelier-pipeline.git
   cd atelier-pipeline
   ```

2. Run the `/pipeline-setup` skill inside Claude Code to install pipeline files
   into your project's `.claude/` directory.

3. Run the test suite:

   ```bash
   bats tests/hooks/ && cd brain && node --test ../tests/brain/*.test.mjs
   ```

   Hook tests use [Bats](https://github.com/bats-core/bats-core). Brain tests
   use the Node.js built-in test runner.

## Architecture Overview

Atelier Pipeline is a multi-agent system where **Eva** (the Pipeline
Orchestrator) routes work across 11+ specialized agents:

| Agent | Role |
|-------|------|
| **Robert** | Product -- feature discovery, specs, product strategy |
| **Sable** | UX -- user experience and interaction design |
| **Cal** | Architecture -- ADR production and technical planning |
| **Colby** | Build -- implementation and coding |
| **Roz** | QA -- test authoring, validation, and investigation |
| **Ellis** | Commits -- git operations and changelog |
| **Agatha** | Documentation -- doc planning and writing |
| **Poirot** | Review -- blind diff-based code review |
| **Sentinel** | Security -- Semgrep-backed SAST auditing |
| **Deps** | Dependencies -- outdated scan, CVE checks, upgrade risk |
| **Darwin** | Evolution -- telemetry analysis and pipeline improvement |

Source templates live in `source/` and are installed to `.claude/` (Claude Code)
or `.cursor-plugin/` (Cursor) by the setup skill. The `brain/` directory
contains the Atelier Brain MCP server (Node.js + PostgreSQL).

## Pull Request Guidelines

- **Branch from `main`.** Create a feature or fix branch off of `main`.
- **Tests must pass.** Run the full test suite before submitting.
- **Follow existing patterns.** Match the conventions in `CLAUDE.md` and the
  surrounding code. Roz-first TDD, Eva never writes code, ADRs are immutable.
- **One concern per PR.** Keep pull requests focused on a single change. Split
  unrelated work into separate PRs.
- **Link related issues.** Reference the issue number in your PR description
  (e.g., "Fixes #42").
- **Describe what and why.** The PR description should explain the change and
  its motivation, not just list the files touched.

## Maintainer

This project is maintained by [Robert Sfeir](https://github.com/robertsfeir).
