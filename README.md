# 📊 DataTalk

> An AI-powered multi-agent data analyst built with Google Agent Development Kit (ADK).

DataTalk enables users to upload CSV datasets, ask natural language business questions, and receive AI-generated analytical insights in a professional HTML report.

---
## Quick Start

```bash
git clone https://github.com/<your-username>/DataTalk.git
cd DataTalk
python -m venv .venv
pip install -r requirements.txt
adk web
```

# Problem

Business users often possess valuable data but lack the technical expertise to analyze it efficiently. Traditional business intelligence platforms require SQL knowledge, dashboard creation, or specialist analysts.

DataTalk bridges this gap by allowing users to ask business questions in plain English while AI agents perform the analysis automatically.

---

# Solution

DataTalk is a secure multi-agent workflow that:

- Loads CSV datasets
- Cleans and validates data
- Detects ambiguous questions
- Requests clarification when needed
- Performs AI-assisted data analysis
- Generates professional HTML reports
- Supports follow-up drill-down questions

---

# Features

✅ Multi-agent workflow using Google ADK

✅ Intelligent question routing

✅ Automatic data cleaning

✅ Human-in-the-loop clarification

✅ Secure code execution

✅ AI-generated business insights

✅ Professional HTML reports

✅ Drill-down analysis

---

# Architecture

![Architecture](assets/architecture.png)

Workflow:

```
User
    ↓
Input Parser
    ↓
Question Router
 ├── Clarify
 └── Process
        ↓
Data Cleaning
        ↓
Security Check
        ↓
Clarification
        ↓
Analysis Agent
        ↓
Report Generator
        ↓
Drill-down Loop
```

---

# Technologies

- Google Agent Development Kit (ADK 2.0)
- Gemini
- Python
- Pandas
- NumPy
- HTML/CSS
- Antigravity IDE

---

# Security

The project includes multiple security mechanisms:

- Prompt injection detection
- Secure execution checkpoint
- Restricted execution environment
- Human confirmation for ambiguous requests
- Controlled Python execution against dataframe objects only

---

# Evaluation

The project was evaluated using synthetic business scenarios covering:

- Clean datasets
- Messy datasets
- Ambiguous business questions
- Business insight generation
- Prompt injection attempts

Evaluation focuses on:

- Workflow correctness
- Analysis quality
- Report quality
- Security robustness

---

# Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/DataTalk.git
cd DataTalk
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Launch the ADK web interface:

```bash
adk web
```

---

# Example

Input:

```
CSV: sample_sales.csv

Question:
Which product category generated the highest total revenue?
```

Output:

- AI-generated business insights
- Executive summary
- Data quality summary
- Statistical overview
- Professional HTML report

---

# Repository Structure

```
assets/
docs/
reports/
tests/
artifacts/
agent.py
config.py
state.py
```

---

# Future Improvements

- Interactive visualizations
- SQL database support
- Model Context Protocol (MCP) integration
- Cloud deployment
- Support for Excel and Parquet datasets
- Dashboard generation

---

# Acknowledgements

Built using Google Agent Development Kit (ADK) and Gemini.
