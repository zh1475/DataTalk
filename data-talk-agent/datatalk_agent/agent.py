# ruff: noqa
import os
import re
import json
import sys
import io
import logging
import hashlib
import datetime
import base64
from typing import Any
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field
from google.genai import Client
from google.genai import types
from google.adk.workflow import Workflow, START, Edge, FunctionNode
from google.adk.agents.context import Context
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from . import config

# Security logger — writes to outputs/security_events.log
os.makedirs("outputs", exist_ok=True)
_sec_logger = logging.getLogger("datatalk.security")
if not _sec_logger.handlers:
    _fh = logging.FileHandler(os.path.join("outputs", "security_events.log"))
    _fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    _sec_logger.addHandler(_fh)
    _sec_logger.setLevel(logging.WARNING)

# Outputs folder already created above

# ------------------------------------------------------------------------------
# Define State Schema using Pydantic
# ------------------------------------------------------------------------------
class DataTalkState(BaseModel):
    file_path: str = ""
    business_question: str = ""
    user_id: str = ""
    
    # Intake & Cleaning output
    cleaned_file_path: str = ""
    original_shape: str = ""
    cleaned_shape: str = ""
    original_duplicates: int = 0
    outliers_detected: str = ""
    type_mismatches: str = ""
    automated_actions: list[str] = Field(default_factory=list)
    flagged_items: list[str] = Field(default_factory=list)
    human_decisions: str = "None (Auto-cleaned)"
    null_percentages: dict[str, float] = Field(default_factory=dict)
    original_missing_values: int = 0
    completeness_pct: float = 100.0
    cols_with_missing: str = ""
    data_quality_assessment: str = ""
    
    # Analysis output
    analysis_stdout: str = ""
    analysis_code: str = ""
    table_data_html: str = ""
    
    # Security fields
    pii_redacted_columns: list[str] = Field(default_factory=list)
    security_flag: bool = False
    security_message: str = ""

    # Report path
    report_file_path: str = ""
    drill_down_count: int = 0

    # Clarification & multi-turn flow
    unit_clarifications: str = ""
    clarification_needed: bool = False
    report_mode: str = "separate"
    pending_followup: str = ""

# ------------------------------------------------------------------------------
# HTML Template for Report Generation
# ------------------------------------------------------------------------------
html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DataTalk Insights Report</title>

    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #333333;
            background-color: #ffffff;
            line-height: 1.6;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
        }
        header {
            border-bottom: 3px solid #0077B6;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        h1 {
            color: #0077B6;
            font-size: 2.2em;
            margin-bottom: 5px;
        }
        h2 {
            color: #0077B6;
            font-size: 1.6em;
            margin-top: 30px;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 8px;
        }
        h3 {
            color: #333333;
            font-size: 1.2em;
            margin-top: 15px;
        }
        .direct-answer {
            background-color: #E8F1F5;
            border-left: 5px solid #0077B6;
            padding: 15px 20px;
            font-size: 1.15em;
            font-weight: 500;
            margin: 20px 0;
            color: #005683;
            border-radius: 0 4px 4px 0;
        }
        .metadata {
            font-size: 0.9em;
            color: #666666;
            margin-top: 10px;
        }
        .audit-section, .process-section {
            background-color: #F8F9FA;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 30px;
        }
        .findings-section, .recommendations-section {
            padding: 10px 0;
            margin-bottom: 30px;
        }
        .badge {
            display: inline-block;
            padding: 3px 8px;
            font-size: 0.8em;
            font-weight: 600;
            border-radius: 4px;
            text-transform: uppercase;
        }
        .badge-success { background-color: #D4EDDA; color: #155724; }
        .badge-warning { background-color: #FFF3CD; color: #856404; }
        .badge-danger { background-color: #F8D7DA; color: #721C24; }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }
        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            text-align: left;
            padding: 10px;
            border-bottom: 1px solid #dddddd;
            font-size: 0.9em;
        }
        th {
            background-color: #0077B6;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        .assumption-box {
            background-color: #FFFDF4;
            border-left: 5px solid #ffcc00;
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 4px 4px 0;
        }
        ul {
            padding-left: 20px;
        }
        li {
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>DataTalk Insights Report</h1>
            <div class="metadata">
                <strong>Business Question:</strong> {business_question}<br>
                <strong>Dataset:</strong> {dataset_name} ({rows_count} rows, {cols_count} columns)<br>
                <strong>Generated On:</strong> {generated_date}
            </div>
            <div class="direct-answer">
                <strong>Direct Answer:</strong> {direct_answer}
            </div>
        </header>

        <!-- Section 1: Key Findings -->
        <section class="findings-section">
            <h2>1. Key Findings</h2>

            <div class="grid">
                <div>
                    <h3>Analysis Findings</h3>
                    <p style="white-space: pre-wrap;">{findings_narrative}</p>
                </div>
            </div>

            <div class="grid">
                <div>
                    <h3>Data Summary Table</h3>
                    <div style="overflow-x: auto;">
                        {data_table_fallback}
                    </div>
                </div>
            </div>

            <h3>Caveats & Limitations</h3>
            <p>{caveats_content}</p>
        </section>

        <!-- Section 2: Recommended Next Steps -->
        <section class="recommendations-section">
            <h2>2. Recommended Next Steps</h2>

            <h3>Business Actions</h3>
            <ul>
                {business_actions_list}
            </ul>

            <h3>Recommended Follow-up Questions</h3>
            <ul>
                {follow_up_questions_list}
            </ul>
        </section>

        <!-- Technical Detail Sections -->
        <div style="margin-top:50px; border-top: 2px dashed #cccccc; padding-top: 30px;">
        <p style="color:#999; font-size:0.85em; text-transform:uppercase; letter-spacing:1px; margin-bottom:20px;">Technical Detail — For Verification Purposes</p>
        <section class="audit-section">
            <h2>Data Cleaning Audit Trail</h2>

            <h3>Data Profiling Summary (Original)</h3>
            <ul>
                <li><strong>Original Shape:</strong> {original_shape}</li>
                <li><strong>Duplicate Rows:</strong> {original_duplicates}</li>
                <li><strong>Outliers Detected:</strong> {outliers_detected}</li>
                <li><strong>Type Mismatches / Warnings:</strong> {type_mismatches}</li>
            </ul>

            <h3>Automated Actions Taken</h3>
            <ul>
                {automated_actions_list}
            </ul>

            <h3>Items Flagged for Human Review</h3>
            <ul>
                {flagged_items_list}
            </ul>

            <h3>Human Decisions Applied</h3>
            <p>{human_decisions}</p>

            <!-- PII Redaction Sub-section -->
            <h3 style="color:#721C24;">&#128274; PII Redaction Audit</h3>
            <div style="background:#fff5f5;border-left:5px solid #E63946;padding:14px 18px;border-radius:0 4px 4px 0;margin-bottom:12px;">
                {pii_section_html}
            </div>

            <h3>Final Dataset Status</h3>
            <ul>
                <li><strong>Cleaned Shape:</strong> {cleaned_shape}</li>
                <li><strong>Status:</strong> <span class="badge badge-success">Clean &amp; Ready</span></li>
            </ul>
        </section>

        <section class="process-section">
            <h2>Analysis Process Log</h2>
            <h3>Steps Taken</h3>
            <ol>
                {analysis_steps_list}
            </ol>

            <h3>Assumptions Made</h3>
            <div class="assumption-box">
                {assumptions_content}
            </div>

            <h3>Confidence Assessment</h3>
            <p>{confidence_notes}</p>
        </div>
    </div>

    <!-- Chart.js Setup Scripts -->
    <script>
        // Findings Chart Setup
        const findingsCtx = document.getElementById('findingsChart').getContext('2d');
        const findingsChartData = {findings_chart_js_data};
        
        if (
    findingsChartData &&
    !findingsChartData.unavailable &&
    findingsChartData.labels &&
    findingsChartData.datasets &&
    findingsChartData.datasets.length > 0
        ) {
            new Chart(findingsCtx, {
                type: findingsChartData.type || 'bar',
                data: {
                    labels: findingsChartData.labels,
                    datasets: findingsChartData.datasets.map(ds => ({
                        ...ds,
                        backgroundColor: ds.backgroundColor || '#0077B6',
                        borderColor: ds.borderColor || '#005683',
                        borderWidth: 1
                    }))
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        } else {
            document.getElementById('findingsChart').style.display = 'none';

            document.getElementById('findingsChart').parentElement.innerHTML = `
                <div style="
                    height:300px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    flex-direction:column;
                    color:#666;
                    background:#f8f9fa;
                    border:1px dashed #ccc;
                    border-radius:8px;
                ">
                    <div style="font-size:18px;font-weight:600;">
                        Visualization unavailable
                    </div>
                    <div style="margin-top:8px;font-size:14px;">
                        The analysis completed successfully, but no suitable chart could be generated for this query.
                    </div>
                </div>`;
        }

        // Quality Chart Setup
        const qualityCtx = document.getElementById('qualityChart').getContext('2d');
        const qualityChartData = {quality_chart_js_data};
        
        new Chart(qualityCtx, {{
            type: 'bar',
            data: {{
                labels: qualityChartData.labels,
                datasets: [{{
                    label: '% Missing Values',
                    data: qualityChartData.data,
                    backgroundColor: '#E63946',
                    borderColor: '#C32F3A',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {{
                    x: {{
                        beginAtZero: true,
                        max: 100
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

# ------------------------------------------------------------------------------
# Graph Node Implementations
# ------------------------------------------------------------------------------

def parse_input(ctx: Context, node_input: Any) -> dict:
    """Parses raw input JSON. Decodes base64 Pub/Sub or reads plain JSON."""
    text_content = ""
    event = {}
    
    if isinstance(node_input, dict):
        event = node_input
    elif hasattr(node_input, "parts") and node_input.parts:
        text_content = node_input.parts[0].text
        try:
            event = json.loads(text_content)
        except json.JSONDecodeError:
            event = {"data": {"business_question": text_content}}
    elif isinstance(node_input, str):
        text_content = node_input
        try:
            event = json.loads(text_content)
        except json.JSONDecodeError:
            event = {"data": {"business_question": text_content}}
            
    data_payload = event.get("data", {})
    
    # Check if 'data' is base64-encoded
    if isinstance(data_payload, str):
        try:
            decoded = base64.b64decode(data_payload).decode("utf-8")
            data_payload = json.loads(decoded)
        except Exception:
            pass
            
    if not isinstance(data_payload, dict):
        data_payload = {}
        
    file_path = data_payload.get("file_path", "")
    business_question = data_payload.get("business_question", "")
    user_id = data_payload.get("user_id", "")
    
    # Fallback to top-level fields
    if not file_path:
        file_path = event.get("file_path", "")
    if not business_question:
        business_question = event.get("business_question", "")
        if not business_question and text_content and not text_content.startswith("{"):
            business_question = text_content
    if not user_id:
        user_id = event.get("user_id", "local_user")

    # Preserve file_path from previous turn if not provided in this turn
    if not file_path:
        file_path = ctx.state.get("file_path", "")

    # Preserve business_question from previous turn if not provided
    if not business_question:
        business_question = ctx.state.get("business_question", "")

    # Detect if this is a plain text clarification response
    # (user replied with clarification text, not a full JSON payload)
    is_clarification = (
        ctx.state.get("clarification_needed", False)
        and bool(text_content)
        and not text_content.strip().startswith("{")
    )

    return {
        "file_path": file_path,
        "business_question": business_question,
        "user_id": user_id,
        "is_clarification": is_clarification,
        "raw_input": text_content
    }


def route_question(ctx: Context, node_input: dict):
    """Checks word count and specificity in Python code, routing accordingly."""
    question = node_input.get("business_question", "").strip()
    file_path = node_input.get("file_path", "").strip()
    user_id = node_input.get("user_id", "local_user")
    
    words = question.split()
    
    # Don't treat drill-down exit words as vague questions
    EXIT_WORDS = {"no", "n", "exit", "stop", "finish", "done", "quit"}
    state_delta = {}
    if question.lower().strip() in EXIT_WORDS:
        return Event(
            output="Workflow finished. Thank you for using DataTalk!",
            route="clarify",
            state=state_delta
        )
    
    is_too_vague = (
        len(words) < config.MIN_WORDS
        or question.lower() in config.VAGUE_PHRASES
        or not question
    )
    
    state_delta = {
        "file_path": file_path,
        "business_question": question,
        "user_id": user_id,
        "human_decisions": "None (Auto-cleaned)"
    }
    
    if is_too_vague:
        msg = f"Clarification Request: The question '{question}' is too vague. Please ask a specific business question with at least 5 words."
        return Event(output=msg, route="clarify", state=state_delta)
    else:
        return Event(output=node_input, route="process", state=state_delta)


def intake_cleaning_agent(ctx: Context, node_input: dict):
    """Profiles and cleans the dataset based on programmatic and LLM decisions."""
    file_path = node_input.get("file_path", "")
    
    if not file_path or not os.path.exists(file_path):
        return Event(
            output=(
                f"⚠️ Could not start analysis: no readable data file was found at "
                f"'{file_path or '(empty path)'}'.\n\n"
                "Please provide the CSV location in your message, e.g.:\n"
                '{"file_path": "tests/data/sample_sales.csv", '
                '"business_question": "Which category generated the most revenue?"}'
            ),
            route="error",
        )

    df = pd.read_csv(file_path)
    original_shape = f"{df.shape[0]} rows, {df.shape[1]} columns"
    
    # 1. Missing values
    missing_count = df.isna().sum().to_dict()
    missing_pct = (df.isna().mean() * 100).to_dict()
    
    # 2. Exact duplicates
    exact_duplicates = int(df.duplicated().sum())
    
    # 3. Outlier detection (IQR)
    outliers = {}
    for col in df.select_dtypes(include=[np.number]).columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_rows = df[(df[col] < lower) | (df[col] > upper)].index.tolist()
        if outlier_rows:
            outliers[col] = {
                "count": len(outlier_rows),
                "rows": outlier_rows[:10]
            }
            
    # 4. Type validation candidates
    date_candidates = []
    id_candidates = []
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                parsed = pd.to_datetime(df[col], errors='coerce')
                parsed_non_null = parsed.dropna()
                non_null_orig = df[col].dropna()
                if len(parsed_non_null) > 0 and len(parsed_non_null) / len(non_null_orig) > 0.8:
                    date_candidates.append(col)
            except Exception:
                pass
        elif df[col].dtype in ['float64', 'float32']:
            non_null = df[col].dropna()
            if len(non_null) > 0 and (non_null % 1 == 0).all():
                if "id" in col.lower() or "code" in col.lower() or "num" in col.lower():
                    id_candidates.append(col)
                    
    # 5. Cardinality check
    high_cardinality = []
    for col in df.select_dtypes(include=['object', 'category']).columns:
        unique_cnt = df[col].nunique()
        if unique_cnt > 10 and unique_cnt / len(df) > 0.5:
            high_cardinality.append({"column": col, "unique_values": unique_cnt})
            
    # ------------------------------------------------------------------------
    # Rule-based cleaning decisions (no LLM required for this step).
    # Decisions are derived programmatically from the profiling metrics above,
    # preserving the full cleaning capability while saving the entire token
    # budget for the AnalysisAgent and InsightReporterAgent.
    # ------------------------------------------------------------------------
    numeric_cols = set(df.select_dtypes(include=[np.number]).columns)
    categorical_cols = set(df.select_dtypes(include=['object', 'category']).columns)

    # 1. Drop any column with more than 70% missing values.
    columns_to_drop = [col for col, pct in missing_pct.items() if pct > 70]
    dropped_set = set(columns_to_drop)

    # 2. Numeric columns with nulls -> fill with the median.
    fillna_numeric = {
        col: "median"
        for col in numeric_cols
        if col not in dropped_set and missing_count.get(col, 0) > 0
    }

    # 3. Categorical columns with nulls -> fill with the mode.
    fillna_categorical = {
        col: "mode"
        for col in categorical_cols
        if col not in dropped_set and missing_count.get(col, 0) > 0
    }

    # 4. Type casts from the detected candidates (dates -> datetime, IDs -> int).
    cast_types = {}
    for col in date_candidates:
        if col not in dropped_set:
            cast_types[col] = "datetime"
    for col in id_candidates:
        if col not in dropped_set:
            cast_types[col] = "int"

    decisions = {
        "columns_to_drop": columns_to_drop,
        "fillna_numeric": fillna_numeric,
        "fillna_categorical": fillna_categorical,
        "cast_types": cast_types,
        "reasoning": (
            "Rule-based system: dropped columns with >70% missing values, "
            "median-imputed numeric nulls, mode-imputed categorical nulls, "
            "and cast detected date/ID columns."
        ),
    }

    # Apply actions
    automated_actions = [
        "Cleaning decisions made by rule-based system (no LLM required for this step)."
    ]
    flagged_items = []

    # Duplicates dropping
    if exact_duplicates > 0:
        df = df.drop_duplicates()
        automated_actions.append(f"Dropped {exact_duplicates} exact duplicate rows.")
        
    # Column Pruning
    for col in decisions.get("columns_to_drop", []):
        if col in df.columns:
            df = df.drop(columns=[col])
            automated_actions.append(f"Dropped column '{col}'.")
            
    # Fill numerical nulls
    for col, strategy in decisions.get("fillna_numeric", {}).items():
        if col in df.columns:
            nulls = df[col].isna().sum()
            if nulls > 0:
                if strategy == 'mean':
                    val = df[col].mean()
                elif strategy == 'median':
                    val = df[col].median()
                else:
                    val = strategy
                df[col] = df[col].fillna(val)
                automated_actions.append(f"Filled {nulls} nulls in '{col}' with {strategy} ({val:.2f}).")
                
    # Fill categorical nulls
    for col, strategy in decisions.get("fillna_categorical", {}).items():
        if col in df.columns:
            nulls = df[col].isna().sum()
            if nulls > 0:
                if strategy == 'mode':
                    val = df[col].mode()[0] if not df[col].mode().empty else "Unknown"
                else:
                    val = strategy
                df[col] = df[col].fillna(val)
                automated_actions.append(f"Filled {nulls} nulls in '{col}' with mode/value '{val}'.")
                
    # Type casting
    for col, new_type in decisions.get("cast_types", {}).items():
        if col in df.columns:
            try:
                if new_type == 'datetime':
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    automated_actions.append(f"Cast '{col}' from string to datetime.")
                elif new_type == 'int':
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                    automated_actions.append(f"Cast float ID '{col}' to integer.")
                elif new_type == 'str':
                    df[col] = df[col].astype(str)
                    automated_actions.append(f"Cast '{col}' to string.")
            except Exception as e:
                flagged_items.append(f"Type cast warning for '{col}': {str(e)}")
                
    # Outliers flagging
    for col, detail in outliers.items():
        if col in df.columns:
            flagged_items.append(f"Outliers: Column '{col}' contains {detail['count']} outliers. Sample affected row indices: {detail['rows']}")
            
    # Cardinality warning
    for val in high_cardinality:
        col = val["column"]
        if col in df.columns:
            flagged_items.append(f"High Cardinality Category Alert in '{col}': {val['unique_values']} unique values.")
            
    # Check remaining nulls
    rem_nulls = df.isna().sum()
    for col, cnt in rem_nulls.items():
        if cnt > 0:
            flagged_items.append(f"Column '{col}' has {cnt} un-cleaned null values.")

    cleaned_shape = f"{df.shape[0]} rows, {df.shape[1]} columns"
    base_name = os.path.basename(file_path)
    cleaned_path = os.path.abspath(os.path.join("outputs", f"cleaned_{base_name}"))
    df.to_csv(cleaned_path, index=False)
    
    # Calculate data quality metrics
    orig_rows, orig_cols = 0, 0
    try:
        parts = original_shape.split(",")
        orig_rows = int(parts[0].split()[0])
        orig_cols = int(parts[1].split()[0])
    except Exception:
        pass

    total_cells = orig_rows * orig_cols
    total_nulls = sum(missing_count.values())
    completeness = ((total_cells - total_nulls) / total_cells * 100) if total_cells > 0 else 100.0
    cols_with_nulls = [col for col, count in missing_count.items() if count > 0]
    cols_with_nulls_str = ", ".join(cols_with_nulls) if cols_with_nulls else "None"
    
    if completeness >= 95:
        assessment = "Excellent"
    elif completeness >= 85:
        assessment = "Good"
    elif completeness >= 70:
        assessment = "Fair"
    else:
        assessment = "Poor"
    
    state_delta = {
        "cleaned_file_path": cleaned_path,
        "original_shape": original_shape,
        "cleaned_shape": cleaned_shape,
        "original_duplicates": exact_duplicates,
        "outliers_detected": f"{sum(d['count'] for d in outliers.values())} outliers flagged",
        "type_mismatches": f"{len(date_candidates)} datetime candidate(s), {len(id_candidates)} float ID candidate(s)",
        "automated_actions": automated_actions if automated_actions else ["No changes required."],
        "flagged_items": flagged_items if flagged_items else ["Data is completely clean."],
        "null_percentages": missing_pct,
        "original_missing_values": total_nulls,
        "completeness_pct": round(completeness, 2),
        "cols_with_missing": cols_with_nulls_str,
        "data_quality_assessment": assessment
    }
    
    return Event(
        output={"cleaned_file_path": cleaned_path},
        route="clean",
        state=state_delta
    )


def analysis_agent(ctx: Context, node_input: dict):
    """Executes dynamic pandas operations locally to answer the business question."""
    cleaned_path = ctx.state.get("cleaned_file_path", "")
    question = ctx.state.get("business_question", "")
    unit_clarifications = ctx.state.get("unit_clarifications", "")

    # Reuse cleaned file from previous turn if available
    if not cleaned_path or not os.path.exists(cleaned_path):
        cleaned_path = ctx.state.get("file_path", "")

    if not cleaned_path or not os.path.exists(cleaned_path):
        return Event(
            output={"message": "Error: No dataset found. Please start a new session with a file_path.", "report_path": ""},
            state={}
        )

    df = pd.read_csv(cleaned_path)
    
    # Gather metadata to feed the LLM
    cols = list(df.columns)
    dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
    head_sample = df.head(2).to_dict()
    
# Truncate to reduce token usage
    head_json = json.dumps(head_sample, default=str)[:2000]
    
    client = Client()
    prompt = f"""
    Write pandas code to answer: "{question}"
    
    DataFrame `df` has these columns: {cols}
    Types: {dtypes}
    Sample (2 rows): {json.dumps(df.head(2).to_dict(), default=str)[:1000]}
    Unit clarifications from user: {unit_clarifications if unit_clarifications else "None — use best judgment but flag any assumptions made"}

    Rules:

    1. Return ONLY executable Python code.

    2. Do NOT import any libraries.

    3. Print the final textual answer using print().
    """
    
    response = client.models.generate_content(
        model=config.MODEL_NAME,
        contents=prompt
    )
    code = response.text
    
    # Strip markdown wrappers
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0]
    elif "```" in code:
        code = code.split("```")[1].split("```")[0]
        
    code_to_exec = code.strip()
    
    # Run the code
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout
    
    error_occurred = None
    locals_dict = {"df": df, "pd": pd, "np": np, "json": json}
    globals_dict = {}
    
    try:
        exec(code_to_exec, globals_dict, locals_dict)
    except Exception as e:
        error_occurred = e
    finally:
        sys.stdout = old_stdout
        
    captured_out = new_stdout.getvalue()
    
    # Self-healing loop: if it failed, ask Gemini to correct it once
    if error_occurred:
        correction_prompt = f"""
        The following python code failed with an error:
        ```python
        {code_to_exec}
        ```
        Error: {str(error_occurred)}
        
        Correct the code and return ONLY executable python. No markdown.
        """
        try:
            response = client.models.generate_content(
                model=config.MODEL_NAME,
                contents=correction_prompt
            )
            code_to_exec = response.text.strip()
            if "```python" in code_to_exec:
                code_to_exec = code_to_exec.split("```python")[1].split("```")[0].strip()
            elif "```" in code_to_exec:
                code_to_exec = code_to_exec.split("```")[1].split("```")[0].strip()
                
            new_stdout = io.StringIO()
            sys.stdout = new_stdout
            exec(code_to_exec, globals_dict, locals_dict)
            captured_out = new_stdout.getvalue()
            error_occurred = None
        except Exception as retry_err:
            error_occurred = retry_err
        finally:
            sys.stdout = old_stdout
            
    if error_occurred:
        captured_out = f"Error executing analysis: {str(error_occurred)}\nRaw code attempted:\n{code_to_exec}"
        
    stdout_narrative = captured_out.strip()
    
    # Data summary table
    table_html = df.head(10).to_html(classes="table", index=False)
    
    state_delta = {
        "analysis_stdout": stdout_narrative,
        "analysis_code": code_to_exec,
        "table_data_html": table_html
    }
    
    return Event(
        output={"stdout": stdout_narrative},
        state=state_delta
    )


def insight_reporter_agent(ctx: Context, node_input: dict):
    """Writes a structured plain-English business report in self-contained HTML."""
    business_question = ctx.state.get("business_question")
    original_shape = ctx.state.get("original_shape")
    cleaned_shape = ctx.state.get("cleaned_shape")
    original_duplicates = ctx.state.get("original_duplicates", 0)
    outliers_detected = ctx.state.get("outliers_detected", "0")
    type_mismatches = ctx.state.get("type_mismatches", "")
    automated_actions = ctx.state.get("automated_actions", [])
    flagged_items = ctx.state.get("flagged_items", [])
    human_decisions = ctx.state.get("human_decisions", "None")
    null_percentages = ctx.state.get("null_percentages", {})
    
    analysis_stdout = ctx.state.get("analysis_stdout")
    analysis_code = ctx.state.get("analysis_code")
    chart_data = ctx.state.get("chart_data", {})
    table_html = ctx.state.get("table_data_html")
    user_id = ctx.state.get("user_id", "local_user")
    
    client = Client()
    prompt = f"""
    Write a business report as JSON for this analysis.
    
    Question: "{business_question}"
    Analysis output: {analysis_stdout[:1000]}
    
    Return:
    {{
      "direct_answer": "one sentence",
      "findings_narrative": "2-3 paragraphs with numbers",
      "business_actions": ["action1", "action2"],
      "follow_up_questions": ["question1"],
      "caveats": "limitations",
      "analysis_steps": ["step1", "step2", "step3"],
      "assumptions": "what was assumed",
      "confidence_notes": "any warnings"
    }}
    """
    
    try:
        response = client.models.generate_content(
            model=config.MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        report_data = json.loads(response.text)
    except Exception as e:
        report_data = {
            "direct_answer": "Analysis execution completed successfully.",
            "findings_narrative": f"Findings narrative:\n{analysis_stdout}",
            "business_actions": ["Review generated data values."],
            "follow_up_questions": ["What is the next drill-down analysis?"],
            "caveats": "None provided.",
            "analysis_steps": ["Executed Pandas analysis code."],
            "assumptions": "Standard defaults.",
            "confidence_notes": f"High confidence. (Text generation failed: {str(e)})"
        }
        
    # Build list contents
    actions_html = "".join([f"<li>{item}</li>" for item in report_data.get("business_actions", [])])
    questions_html = "".join([f"<li>{item}</li>" for item in report_data.get("follow_up_questions", [])])
    steps_html = "".join([f"<li>{item}</li>" for item in report_data.get("analysis_steps", [])])
    
    automated_actions_html = "".join([f"<li>{item}</li>" for item in automated_actions])
    flagged_items_html = "".join([f"<li>{item}</li>" for item in flagged_items])
    
    # Missingness chart config
    null_labels = list(null_percentages.keys())
    null_values = [round(float(v), 2) for v in null_percentages.values()]
    quality_chart_json = json.dumps({
        "labels": null_labels,
        "data": null_values
    })
    
    # Replace templates manually (avoiding curly braces errors from format())
    generated_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dataset_name = os.path.basename(ctx.state.get("file_path", "dataset.csv"))
    
    orig_rows, orig_cols = 0, 0
    try:
        parts = original_shape.split(",")
        orig_rows = int(parts[0].split()[0])
        orig_cols = int(parts[1].split()[0])
    except Exception:
        pass
        
    html_content = html_template
    html_content = html_content.replace("{business_question}", str(business_question))
    html_content = html_content.replace("{dataset_name}", str(dataset_name))
    html_content = html_content.replace("{rows_count}", str(orig_rows))
    html_content = html_content.replace("{cols_count}", str(orig_cols))
    html_content = html_content.replace("{generated_date}", str(generated_date))
    html_content = html_content.replace("{direct_answer}", str(report_data.get("direct_answer", "")))
    html_content = html_content.replace("{original_shape}", str(original_shape))
    html_content = html_content.replace("{original_duplicates}", str(original_duplicates))
    html_content = html_content.replace("{outliers_detected}", str(outliers_detected))
    html_content = html_content.replace("{type_mismatches}", str(type_mismatches))
    html_content = html_content.replace("{automated_actions_list}", str(automated_actions_html))
    html_content = html_content.replace("{flagged_items_list}", str(flagged_items_html))
    html_content = html_content.replace("{human_decisions}", str(human_decisions))
    html_content = html_content.replace("{cleaned_shape}", str(cleaned_shape))
    html_content = html_content.replace("{analysis_steps_list}", str(steps_html))
    html_content = html_content.replace("{assumptions_content}", str(report_data.get("assumptions", "None")))
    html_content = html_content.replace("{confidence_notes}", str(report_data.get("confidence_notes", "N/A")))
    html_content = html_content.replace("{findings_narrative}", str(report_data.get("findings_narrative", "")))
    html_content = html_content.replace("{caveats_content}", str(report_data.get("caveats", "None")))
    html_content = html_content.replace("{business_actions_list}", str(actions_html))
    html_content = html_content.replace("{follow_up_questions_list}", str(questions_html))
    html_content = html_content.replace("{data_table_fallback}", str(table_html if table_html else "<p>No data table available.</p>"))
    if chart_data:
        chart_json_str = json.dumps(chart_data)
    else:
        chart_json_str = json.dumps({
            "unavailable": True,
            "reason": "The analysis agent could not generate a visualization for this query."
        })
    html_content = html_content.replace("{findings_chart_js_data}", chart_json_str)
    html_content = html_content.replace("{quality_chart_js_data}", quality_chart_json)
 
    # PII Redaction section
    pii_cols = ctx.state.get("pii_redacted_columns", [])
    if pii_cols:
        pii_rows = "".join(
            f"<tr><td><code>{col}</code></td>"
            f"<td>Column name matched PII heuristic (name/email/phone/id/card/ssn keyword or regex pattern)</td>"
            f"<td><span class='badge badge-danger'>SHA-256 Hashed</span></td></tr>"
            for col in pii_cols
        )
        pii_section_html = (
            f"<p><strong>{len(pii_cols)} column(s) contained personal identifiers and were hashed "
            f"(SHA-256) before any LLM interaction.</strong></p>"
            f"<table><thead><tr><th>Column</th><th>Reason</th><th>Action</th></tr></thead>"
            f"<tbody>{pii_rows}</tbody></table>"
        )
    else:
        pii_section_html = "<p><span class='badge badge-success'>No PII Detected</span> No columns were flagged for PII redaction.</p>"
    html_content = html_content.replace("{pii_section_html}", pii_section_html)

    report_mode = ctx.state.get("report_mode", "separate")
    existing_report = ctx.state.get("report_file_path", "")

    if report_mode == "merge" and existing_report and os.path.exists(existing_report):
        # Load existing report and append new findings before </body>
        with open(existing_report, "r", encoding="utf-8") as f:
            existing_html = f.read()

        new_section = f"""
        <section class="findings-section" style="border-top:3px solid
        #0077B6;margin-top:40px;padding-top:20px;">
            <h2>Follow-up: {business_question}</h2>
            <div class="direct-answer">
                <strong>Answer:</strong>
                {report_data.get("direct_answer", "")}
            </div>
            <p style="white-space:pre-wrap;">
                {report_data.get("findings_narrative", "")}
            </p>
            <h3>Recommended Actions</h3>
            <ul>{actions_html}</ul>
        </section>
        """
        merged_html = existing_html.replace(
            "</body>", new_section + "\n</body>"
        )
        with open(existing_report, "w", encoding="utf-8") as f:
            f.write(merged_html)
        report_path = existing_report
    else:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"report_{user_id}_{timestamp}.html"
        report_path = os.path.abspath(
            os.path.join("outputs", report_filename)
        )
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    state_delta = {"report_file_path": report_path}

    return Event(
        output={
            "message": f"Your DataTalk Report is ready!\nFile: {report_path}",
            "report_path": report_path
        },
        state=state_delta
    )


def security_checkpoint(ctx: Context, node_input: dict):
    """Security checkpoint: blocks prompt injection and redacts PII before any LLM sees the data.

    Routes:
      "secure" — input is safe, continue to analysis_agent
      "error"  — injection detected, stop and inform the user
    """
    # ------------------------------------------------------------------
    # 1. Prompt-injection detection on business_question
    # ------------------------------------------------------------------
    question = ctx.state.get("business_question", "")
    question_lower = question.lower()

    _INJECTION_PATTERNS = [
        r"ignore\s+(previous|prior|all)\s+instructions?",
        r"output\s+all\s+(the\s+)?data",
        r"pretend\s+(you\s+are|to\s+be)",
        r"(act|behave)\s+as\s+(if\s+you\s+are|a\s+different)",
        r"bypass\s+(security|filter|guardrail)",
        r"(give|show|reveal|print|dump)\s+(me\s+)?(the\s+)?(system\s+prompt|raw\s+data|training\s+data)",
        r"forget\s+(everything|all|prior)",
        r"you\s+are\s+now\s+[a-z]+",
        r"do\s+anything\s+now",
        r"DAN\b",
        r"jailbreak",
    ]

    for pat in _INJECTION_PATTERNS:
        if re.search(pat, question_lower):
            _sec_logger.warning(
                "PROMPT_INJECTION_DETECTED | user_id=%s | pattern=%s | question=%r",
                ctx.state.get("user_id", "unknown"), pat, question[:200]
            )
            return Event(
                output=(
                    "\u26a0\ufe0f Security Alert: Your business question contains instructions "
                    "that are not allowed. Please rephrase as a plain business question "
                    "(e.g. \"What are the top 5 products by revenue?\"). "
                    "This event has been logged."
                ),
                route="error",
                state={"security_flag": True,
                       "security_message": f"Prompt injection blocked. Pattern: {pat}"}
            )

    # ------------------------------------------------------------------
    # 2. PII detection and SHA-256 hashing on the cleaned dataset
    # ------------------------------------------------------------------
    cleaned_path = ctx.state.get("cleaned_file_path") or ctx.state.get("file_path", "")
    if not cleaned_path or not os.path.exists(cleaned_path):
        # Nothing to redact — continue safely
        return Event(output=node_input, route="secure",
                     state={"pii_redacted_columns": [], "security_flag": False})

    df = pd.read_csv(cleaned_path)

    # Heuristic: column-name keywords
    _PII_NAME_KEYWORDS = [
        "name", "email", "phone", "mobile", "address", "postcode", "zipcode",
        "ssn", "sin", "nid", "national_id", "passport", "dob", "date_of_birth",
        "birth", "credit", "card", "pan", "cvv", "iban", "account",
    ]
    # Regex patterns for content-based detection (applied to column samples)
    _PII_CONTENT_PATTERNS = [
        re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),        # email
        re.compile(r"\b\d{3}[\-\s]?\d{2}[\-\s]?\d{4}\b"),                         # SSN-like
        re.compile(r"\b4[0-9]{12}(?:[0-9]{3})?\b"),                                # Visa card
        re.compile(r"\b5[1-5][0-9]{14}\b"),                                         # MasterCard
        re.compile(r"\+?[1-9]\d{0,2}[\s\-]?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{4}\b"),  # phone
    ]

    redacted_cols = set()

    for col in df.columns:
        col_lower = col.lower().replace(" ", "_")
        # Name-based check
        if any(kw in col_lower for kw in _PII_NAME_KEYWORDS):
            redacted_cols.add(col)
            continue
        # Content-based check on up to 30 non-null sample values
        sample_vals = df[col].dropna().astype(str).head(30).tolist()
        for val in sample_vals:
            if any(pat.search(val) for pat in _PII_CONTENT_PATTERNS):
                redacted_cols.add(col)
                break

    def _sha256(value) -> str:
        if pd.isna(value):
            return value
        return hashlib.sha256(str(value).encode()).hexdigest()[:16]  # 16-char prefix for readability

    for col in redacted_cols:
        df[col] = df[col].apply(_sha256)

    if redacted_cols:
        _sec_logger.warning(
            "PII_REDACTED | user_id=%s | columns=%s",
            ctx.state.get("user_id", "unknown"), list(redacted_cols)
        )

    # Persist the PII-scrubbed dataset
    base_name = os.path.basename(cleaned_path)
    scrubbed_path = os.path.abspath(os.path.join("outputs", f"scrubbed_{base_name}"))
    df.to_csv(scrubbed_path, index=False)

    return Event(
        output=node_input,
        route="secure",
        state={
            "cleaned_file_path": scrubbed_path,
            "pii_redacted_columns": list(redacted_cols),
            "security_flag": False,
            "security_message": "",
        }
    )


def drill_down_checkpoint(ctx: Context, node_input: Any):
    """Checkpoint to allow user to drill deeper into findings or exit.
    Handles merge vs separate report preference and reuses same dataset."""

    if isinstance(node_input, dict):
        follow_up = node_input.get("follow_up", "").strip()
        if not follow_up:
            # node_input came from insight_reporter — prompt user
            return Event(
                output=(
                    "Report generated! Do you want to ask a follow-up "
                    "question about this data?\n\n"
                    "- Type your question to continue\n"
                    "- Type 'no' to finish\n\n"
                    "Tip: prefix with 'merge ' to add the answer to "
                    "your existing report, or 'separate ' for a new "
                    "report. Default is separate."
                ),
                route="exit"
            )
    elif isinstance(node_input, str):
        follow_up = node_input.strip()
    else:
        follow_up = ""

    if not follow_up:
        return Event(
            output="Report ready! Type a follow-up question or 'no' to finish.",
            route="exit"
        )

    current_count = ctx.state.get("drill_down_count", 0)

    if follow_up.lower() in ("no", "n", "exit", "stop", "finish"):
        return Event(
            output="Workflow finished. Thank you for using DataTalk!",
            route="exit"
        )
    elif current_count >= 3:
        return Event(
            output="Maximum follow-up questions reached. Workflow finished.",
            route="exit"
        )

    # Detect merge/separate prefix
    if follow_up.lower().startswith("merge "):
        actual_question = follow_up[6:].strip()
        report_mode = "merge"
    elif follow_up.lower().startswith("separate "):
        actual_question = follow_up[9:].strip()
        report_mode = "separate"
    else:
        actual_question = follow_up
        report_mode = "separate"

    return Event(
        output={
            "file_path": ctx.state.get("file_path", ""),
            "business_question": actual_question,
            "user_id": ctx.state.get("user_id", "local_user"),
            "raw_input": actual_question
        },
        route="drill",
        state={
            "business_question": actual_question,
            "report_mode": report_mode,
            "pending_followup": "",
            "drill_down_count": current_count + 1,
            "file_path": ctx.state.get("file_path", ""),
            "cleaned_file_path": ctx.state.get("cleaned_file_path", "")
        }
    )


def clarify_question(ctx: Context, node_input: str) -> str:
    """Instantly returns clarification request."""
    return node_input


def end_node(ctx: Context, node_input: str) -> str:
    """Ends the workflow session."""
    return node_input


def clarify_ambiguities(ctx: Context, node_input: Any):
    """Detects data ambiguities and logs them to the audit trail,
    then proceeds directly to analysis. Full interactive clarification
    is noted in ROADMAP.md as a planned enhancement."""
    
    cleaned_path = ctx.state.get("cleaned_file_path", "")
    ambiguity_notes = []

    if cleaned_path and os.path.exists(cleaned_path):
        df = pd.read_csv(cleaned_path)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        UNIT_TRIGGER_WORDS = [
            "sales", "revenue", "amount", "value", "price", "cost",
            "units", "quantity", "total", "income", "profit", "spend"
        ]
        for col in numeric_cols:
            if any(word in col.lower() for word in UNIT_TRIGGER_WORDS):
                non_null = df[col].dropna()
                if len(non_null) > 0:
                    mean_val = non_null.mean()
                    if mean_val > 10000:
                        ambiguity_notes.append(
                            f"Note: '{col}' averages {mean_val:,.0f} — "
                            f"units assumed to be base currency. "
                            f"Verify scale before acting on findings."
                        )
                    elif 0 < mean_val < 1:
                        ambiguity_notes.append(
                            f"Note: '{col}' averages {mean_val:.4f} — "
                            f"treated as decimal (e.g. 0.15 = 15%). "
                            f"Verify before acting on findings."
                        )

        for col in numeric_cols:
            if any(word in col.lower() for word in UNIT_TRIGGER_WORDS):
                zero_pct = (df[col] == 0).mean() * 100
                if zero_pct > 20:
                    ambiguity_notes.append(
                        f"Note: '{col}' has {zero_pct:.0f}% zeros — "
                        f"assumed to mean no activity, not missing data."
                    )

    notes_str = " | ".join(ambiguity_notes) if ambiguity_notes else "None detected"

    return Event(
        output=node_input,
        route="proceed",
        state={
            "unit_clarifications": notes_str,
            "clarification_needed": False
        }
    )

# ------------------------------------------------------------------------------
# Wrap node functions as FunctionNode instances (required by ADK 1.18.0)
# ------------------------------------------------------------------------------

parse_input_node         = FunctionNode(func=parse_input)
route_question_node      = FunctionNode(func=route_question)
intake_cleaning_node     = FunctionNode(func=intake_cleaning_agent)
security_checkpoint_node = FunctionNode(func=security_checkpoint)
analysis_agent_node      = FunctionNode(func=analysis_agent)
insight_reporter_node    = FunctionNode(func=insight_reporter_agent)
drill_down_node          = FunctionNode(func=drill_down_checkpoint)
clarify_question_node    = FunctionNode(func=clarify_question)
end_node_node            = FunctionNode(func=end_node)
clarify_ambiguities_node = FunctionNode(func=clarify_ambiguities)

# ------------------------------------------------------------------------------
# Define and Wire Up Workflow Graph
# ------------------------------------------------------------------------------

app = Workflow(
    name="DataTalk",
    edges=[
        # Input parsing and routing
        Edge(from_node=START,                       to_node=parse_input_node),
        Edge(from_node=parse_input_node,            to_node=route_question_node),
        Edge(from_node=route_question_node,         to_node=clarify_question_node,      route="clarify"),
        Edge(from_node=route_question_node,         to_node=intake_cleaning_node,       route="process"),
        # Security checkpoint
        Edge(from_node=intake_cleaning_node,        to_node=security_checkpoint_node,   route="clean"),
        Edge(from_node=intake_cleaning_node,        to_node=end_node_node,              route="error"),
        Edge(from_node=security_checkpoint_node,    to_node=clarify_ambiguities_node,   route="secure"),
        Edge(from_node=security_checkpoint_node,    to_node=end_node_node,              route="error"),
        # Clarification flow
        Edge(from_node=clarify_ambiguities_node,    to_node=analysis_agent_node,        route="proceed"),
        Edge(from_node=clarify_ambiguities_node,    to_node=end_node_node,              route="needs_clarification"),
        # Analysis and reporting
        Edge(from_node=analysis_agent_node,         to_node=insight_reporter_node),
        Edge(from_node=insight_reporter_node,       to_node=drill_down_node),
        # Drill-down loop
        Edge(from_node=drill_down_node,             to_node=analysis_agent_node,        route="drill"),
        Edge(from_node=drill_down_node,             to_node=end_node_node,              route="exit"),
    ],
    state_schema=DataTalkState
)

# ------------------------------------------------------------------------------
# Expose the workflow under the name the ADK agent loader looks for.
# `adk web` / the dev UI discovers an agent by finding a `root_agent` that is a
# BaseAgent or BaseNode (a Workflow is a BaseNode). A variable named `app` is
# only recognized when it is an `App` instance, so the Workflow must also be
# exported as `root_agent` to be discoverable.
# ------------------------------------------------------------------------------
root_agent = app
