# DataTalk — Roadmap & Known Constraints

## Current Version
A working multi-agent data analysis system that takes a CSV and a 
plain-English business question and returns a structured HTML insight 
report with full audit trail.

## Features Intentionally Scoped Out (Token/Rate Limit Constraints)

The following features were designed and partially implemented but 
reduced in scope to stay within Gemini free-tier rate limits during 
the competition build window. Each is a natural next step:

### 1. Full Summary Statistics in Cleaning Report
The IntakeCleaningAgent computes df.describe() statistics but sends 
a trimmed version to Gemini to reduce prompt size. A production version 
would pass full summary statistics and render them as a table in the 
HTML report.

### 2. Richer Analysis Context
The AnalysisAgent currently sends 2 sample rows to Gemini. A production 
version would send 5-10 rows plus value counts for categorical columns, 
enabling more accurate pandas code generation.

### 3. Multi-turn Memory Across Sessions
The architecture supports persistent session memory (user_id tracked, 
session state stored) but cross-session retrieval was not fully wired 
due to time constraints. A production version would let returning users 
ask "compare this to last month's data."

### 4. MCP Integration for Live Benchmarking
The original design included a Google Search MCP tool so the 
InsightReporterAgent could add industry benchmarks to findings 
(e.g. "your return rate of 12% compares to an industry average of 8%"). 
Disabled to reduce API calls per session.

### 5. Human-in-the-Loop Cleaning Decisions
The flagged items list is generated but the current workflow auto-proceeds 
without pausing for human input on cleaning decisions. A production version 
would pause and ask the user to decide on ambiguous cases before analysis.

### 6. Clarification Loop Efficiency
Currently the dataset is re-cleaned on every turn including clarification responses. A production version would cache the cleaned dataset and skip re-cleaning if cleaned_file_path already exists in state from a previous turn in the same session.

### 7. Interactive Pre-Analysis Clarification Loop
The clarify_ambiguities node detects unit ambiguities, zero-value 
patterns, and scale issues programmatically and logs them to the 
audit trail as assumptions. A full interactive clarification loop — 
pausing the workflow to ask the user and resuming after their reply — 
was designed and partially implemented but removed due to ADK playground 
multi-turn session limitations. The ambiguity detection logic is 
preserved and runs silently on every analysis run.

### 8. Follow-up Question Merge/Separate Flow
The drill_down_checkpoint supports 'merge' and 'separate' prefixes so 
users can choose whether follow-up answers are appended to the existing 
report or generated as a new file. The underlying merge logic is 
implemented in InsightReporterAgent. A full conversational loop 
(pausing after report delivery and resuming on user reply) was 
partially implemented but ADK playground multi-turn routing limitations 
mean follow-up questions currently require starting a new session.

## Architecture
Five nodes — IntakeCleaningAgent → SecurityCheckpoint → 
ClarifyAmbiguities → AnalysisAgent → InsightReporterAgent — 
with rule-based data cleaning, PII scrubbing (SHA-256 hashing), 
prompt injection defense, silent ambiguity detection, Chart.js 
visualizations, merge/separate report modes, and a full audit trail 
in every HTML report.