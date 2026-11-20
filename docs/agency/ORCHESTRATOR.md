# Orchestrator

SQLite `jobs` table + `enqueueAndRun`.

Agents: research, lead, website_builder, email_draft, qa.

Prefer Python scripts for repetitive import/backup; agents call libraries/scripts instead of LLM APIs.
