# 📊 DataTalk

<p align="center">
  <img src="assets/thumbnail.png" alt="DataTalk Thumbnail" width="700"/>
</p>

> **An AI-powered multi-agent business intelligence assistant built with Google Agent Development Kit (ADK).**

DataTalk enables users to analyze CSV datasets using natural language. By combining a coordinated multi-agent workflow with AI-assisted reasoning, it automatically cleans data, answers business questions, and generates professional HTML reports containing actionable business insights.

---

# 🚀 Project Overview

Businesses collect vast amounts of operational data, but extracting meaningful insights often requires expertise in SQL, Python, spreadsheets, or business intelligence tools. This creates a barrier for non-technical users who simply want answers to business questions.

**DataTalk** bridges this gap by allowing users to interact with their data using natural language. Rather than requiring dashboards or manual analysis, users specify a CSV file and ask a business question. DataTalk then performs the complete analysis workflow automatically and produces a professional HTML report.

Built using the **Google Agent Development Kit (ADK)**, DataTalk demonstrates how multiple specialized AI agents can collaborate to solve a realistic business problem safely and transparently.

---

# 💡 Key Features

- 🤖 Multi-agent workflow built with Google ADK
- 📂 Automatic CSV data loading
- 🧹 Intelligent data cleaning and preprocessing
- 💬 Human-in-the-loop clarification for ambiguous questions
- 🔒 Security checkpoint with prompt injection detection
- 📊 AI-powered business analysis using Pandas
- 📝 Professional HTML report generation
- 🔁 Follow-up drill-down analysis

---

# 🏗️ Architecture

<p align="center">
  <img src="assets/architecture.png" width="850">
</p>

The workflow consists of specialized agents responsible for individual tasks:

1. **Input Parser**
   - Validates the incoming request.
   - Extracts the dataset path and business question.

2. **Question Router**
   - Determines whether clarification is required before analysis.

3. **Data Cleaning**
   - Loads and prepares the dataset.
   - Handles common data quality issues.

4. **Security Checkpoint**
   - Detects unsafe prompts and potential prompt injection attempts.
   - Prevents unsafe execution before analysis.

5. **Clarification Agent**
   - Requests additional information when assumptions would significantly impact results.

6. **Analysis Agent**
   - Generates executable Pandas code using Gemini.
   - Executes analysis within a controlled Python environment.

7. **Insight Reporter**
   - Converts analytical outputs into a professionally formatted HTML report.

8. **Drill-down Loop**
   - Supports follow-up business questions without restarting the workflow.

---

# 🛠️ Technologies

- Google Agent Development Kit (ADK 2.0)
- Google Gemini
- Python
- Pandas
- NumPy
- HTML/CSS
- Antigravity IDE

---

# 🔒 Security Features

DataTalk incorporates several safeguards to improve reliability and security:

- Prompt injection detection
- Dedicated security checkpoint
- Human-in-the-loop clarification
- Controlled execution of AI-generated Python code
- Restricted execution environment
- Analysis limited to the supplied dataframe

---

# 📂 Repository Structure

```text
data-talk-agent/
│
├── app/                         # ADK application configuration
├── assets/                      # Images and architecture diagrams
├── datatalk_agent/              # Core workflow implementation
├── deployment/
│   └── terraform/               # Deployment infrastructure
├── outputs/                     # Generated outputs
├── reports/                     # Example HTML reports
├── tests/                       # Test datasets and evaluation
│
├── README.md
├── ROADMAP.md
├── GEMINI.md
├── pyproject.toml
├── agents-cli-manifest.yaml
└── deployment_metadata.json
```

---

# ⚙️ Installation

## Prerequisites

- Python 3.11+
- Git
- Google Agent Development Kit (ADK)
- Gemini API Key

---

## Clone the Repository

```bash
git clone https://github.com/<your-username>/data-talk-agent.git
cd data-talk-agent
```

---

## Create a Virtual Environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## Install Dependencies

Using **uv** (recommended):

```bash
uv sync
```

or

```bash
pip install -e .
```

---

## Configure Your API Key

Create a `.env` file:

```text
GOOGLE_API_KEY=YOUR_API_KEY
```

---

# ▶️ Running DataTalk

Launch the ADK Web UI:

```bash
adk web
```

Select the **DataTalk** workflow.

---

## Example Request

DataTalk currently accepts **local CSV file paths** rather than direct file uploads.

Example payload:

```json
{
  "file_path": "tests/data/sample_sales.csv",
  "business_question": "Which product category has the highest total sales and average sales per transaction?",
  "user_id": "user_001"
}
```

---

## Workflow

After submitting the request, DataTalk will:

1. Validate the request.
2. Load the CSV dataset.
3. Clean and prepare the data.
4. Perform security checks.
5. Request clarification if needed.
6. Execute AI-powered analysis.
7. Generate a professional HTML report.
8. Support optional follow-up drill-down questions.

Generated reports are saved to the **outputs/** directory.

---

# 📈 Example Questions

```
Which region generated the highest revenue?
```

```
What is the average sales value for each product category?
```

```
Which salesperson had the highest monthly sales?
```

```
Which product category shows the highest growth trend?
```

---

# 🧪 Evaluation

The project includes an evaluation framework covering:

- Ambiguous business questions
- Clean datasets
- Messy datasets
- Business insight generation
- Prompt injection attempts

Evaluation focuses on:

- Workflow correctness
- Analysis quality
- Report quality
- Security robustness

---

# 🚧 Current Limitations

This submission represents a functional prototype.

Current limitations include:

- Local CSV file paths are used instead of direct file uploads.
- CSV is currently the only supported data format.
- Analysis is performed on a single dataset at a time.

These choices simplify reproducible testing and evaluation within the ADK development environment.

---

# 🔮 Future Improvements

Future enhancements include:

- Interactive data visualizations
- Excel and Parquet support
- SQL database connectivity
- Model Context Protocol (MCP) integration
- Cloud deployment
- Direct file upload support
- Dashboard generation
- Persistent conversational memory

---

# 🙏 Acknowledgements

Built using:

- Google Agent Development Kit (ADK)
- Google Gemini
- Antigravity IDE

---

# 📄 License

This project is intended for educational and hackathon purposes.
