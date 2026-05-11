import streamlit as st
from agent import run_agent
import tempfile
import os
import io
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CSV Analyst Agent",
    page_icon="📊",
    layout="wide"
)

# ── Load CSS from templates.html ──────────────────────────────────────────────
def _load_template_css():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "templates.html")
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        s = raw.find("<style>")
        e = raw.find("</style>") + len("</style>")
        return raw[s:e] if s != -1 else ""
    except FileNotFoundError:
        return ""

TEMPLATE_CSS = _load_template_css()

# Inject template CSS + extra Streamlit tweaks
st.markdown(TEMPLATE_CSS + """
<style>
section[data-testid="stSidebar"] { background: #f8f7ff; }
[data-testid="stChatMessage"]     { border-radius: 10px; }
.stMetric label { font-size: 0.78rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Page Header (from templates.html class: main-header) ─────────────────────
st.markdown("""
<div class="main-header">
  <h2>📊 CSV Data Analyst Agent</h2>
  <p>Upload your data file and ask questions in plain English —
     get tables, histograms, bar charts, pie charts &amp; more instantly.</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📖 How to Use")
    st.markdown("**Supported files:** CSV · TXT · XLSX")
    st.warning("⚠️ PDF files are **not** supported")
    st.divider()
    st.markdown("**💬 Ask these questions:**")
    examples = [
        ("`summary`",               "Full data report + charts"),
        ("`total salary`",          "Sum of salary column"),
        ("`average age`",           "Mean of age column"),
        ("`maximum sales`",         "Highest value + top-5 table"),
        ("`minimum salary`",        "Lowest value + bottom-5 table"),
        ("`show salary of Alice`",  "Specific person's value"),
        ("`above average salary`",  "Records above average"),
        ("`below average salary`",  "Records below average"),
        ("`bar chart`",             "Comparison bar chart"),
        ("`pie chart`",             "Share / proportion chart"),
        ("`trend`",                 "Line trend graph"),
        ("`histogram`",             "Frequency distribution"),
        ("`scatter`",               "Correlation scatter plot"),
        ("`sort by salary`",        "Ranked table ↓"),
        ("`columns`",               "Column schema info"),
        ("`count`",                 "Total rows in dataset"),
    ]
    for q, desc in examples:
        st.markdown(f"- {q} — {desc}")


# ─────────────────────────────────────────────────────────────────────────────
# FILE UPLOADER
# ─────────────────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "📂 Upload your data file (CSV, TXT, or Excel)",
    type=["csv", "txt", "xlsx"],
    help="Only CSV, TXT, and XLSX files are supported."
)

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.xlsx'):
            preview_df = pd.read_excel(uploaded_file)
        else:
            preview_df = pd.read_csv(uploaded_file)
        uploaded_file.seek(0)

        # ── Metric row ──────────────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📄 File",    uploaded_file.name)
        c2.metric("📝 Rows",    f"{len(preview_df):,}")
        c3.metric("📋 Columns", len(preview_df.columns))
        c4.metric("💾 Size",    f"{uploaded_file.size / 1024:.1f} KB")

        # ── Column pills (from templates.html class: pill) ──────────────────
        pills = "".join(
            f'<span class="pill">{col}</span>' for col in preview_df.columns
        )
        st.markdown(
            TEMPLATE_CSS + f"<p style='margin:6px 0 4px;font-weight:600;'>Detected columns:</p>{pills}",
            unsafe_allow_html=True
        )

        # ── Preview (collapsed) ─────────────────────────────────────────────
        with st.expander("👀 Preview first 5 rows", expanded=False):
            st.dataframe(preview_df.head(5), use_container_width=True)

    except Exception as e:
        # Error box from templates.html
        st.markdown(
            TEMPLATE_CSS + f'<div class="error-box">❌ Could not read file: {e}</div>',
            unsafe_allow_html=True
        )


# ─────────────────────────────────────────────────────────────────────────────
# CHAT HISTORY
# ─────────────────────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


def _render_result(result, df, idx):
    """Render one agent result block inside a chat_message context."""

    # ── Error ─────────────────────────────────────────────────────────────────
    if "error" in result:
        st.markdown(
            TEMPLATE_CSS + f'<div class="error-box">❌ {result["error"]}</div>',
            unsafe_allow_html=True
        )
        return

    # ── Text answer ───────────────────────────────────────────────────────────
    if "answer" in result:
        st.markdown(result["answer"])

    # ── Metric cards (total / average) ────────────────────────────────────────
    label    = result.get("label", "Value")
    has_tot  = "total_sales"   in result
    has_avg  = "average_sales" in result
    if has_tot or has_avg:
        mc1, mc2 = st.columns(2)
        if has_tot:
            mc1.metric(f"💰 Total {label}",   f"{result['total_sales']:,.2f}")
        if has_avg:
            mc2.metric(f"📊 Average {label}", f"{result['average_sales']:,.2f}")

    # ── Primary HTML table (pandas → templates.html styles) ──────────────────
    if "table" in result:
        st.markdown(result["table"], unsafe_allow_html=True)

    # ── Charts layout ─────────────────────────────────────────────────────────
    chart_keys = ["bar", "line", "pie", "histogram", "scatter"]
    captions   = {
        "bar":       "📊 Bar Chart",
        "line":      "📈 Line Trend",
        "pie":       "🥧 Pie Chart",
        "histogram": "📊 Histogram",
        "scatter":   "🔵 Scatter Plot",
    }
    present = [k for k in chart_keys if k in result]

    if len(present) == 1:
        k = present[0]
        st.markdown(
            TEMPLATE_CSS + '<div class="chart-wrapper">',
            unsafe_allow_html=True
        )
        st.image(result[k], caption=captions[k], use_column_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    elif len(present) > 1:
        # Render two charts per row
        pairs = [present[i:i+2] for i in range(0, len(present), 2)]
        for pair in pairs:
            cols = st.columns(len(pair))
            for col, k in zip(cols, pair):
                with col:
                    st.image(result[k], caption=captions[k], use_column_width=True)

    # ── Raw full-data table (collapsed expander) ──────────────────────────────
    if "raw_table" in result:
        with st.expander("📋 Full Data Table", expanded=False):
            st.markdown(result["raw_table"], unsafe_allow_html=True)

    # ── Download buttons — only show for data-heavy results ──────────────────
    has_chart = any(k in result for k in ["bar","line","pie","histogram","scatter"])
    has_table = "table" in result or "raw_table" in result
    if df is not None and (has_chart or has_table):
        st.markdown("**📥 Download results:**")
        dl1, dl2 = st.columns(2)

        # Excel
        excel_buf = io.BytesIO()
        try:
            df.to_excel(excel_buf, index=False, engine='openpyxl')
            dl1.download_button(
                "📗 Excel (.xlsx)",
                data=excel_buf.getvalue(),
                file_name=f"results_{idx}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"excel_{idx}",
                use_container_width=True,
            )
        except Exception:
            dl1.info("Install openpyxl for Excel export")

        # CSV
        dl2.download_button(
            "📄 CSV (.csv)",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name=f"results_{idx}.csv",
            mime="text/csv",
            key=f"csv_{idx}",
            use_container_width=True,
        )


# ── Render stored chat history ─────────────────────────────────────────────
for idx, chat in enumerate(st.session_state.chat_history):
    with st.chat_message("user"):
        st.write(chat["question"])
    with st.chat_message("assistant"):
        _render_result(chat["result"], chat["df"], idx)


# ─────────────────────────────────────────────────────────────────────────────
# QUERY INPUT
# ─────────────────────────────────────────────────────────────────────────────
query = st.chat_input(
    "Ask: summary, total salary, histogram, bar chart, scatter, sort by salary..."
)

if query:
    if uploaded_file is None:
        # Warning box from templates.html
        st.markdown(
            TEMPLATE_CSS +
            '<div class="warning-box">⚠️ Please upload a CSV, TXT, or XLSX file first!</div>',
            unsafe_allow_html=True
        )
    else:
        ext = uploaded_file.name.split('.')[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        try:
            with st.spinner("🔍 Analysing your data…"):
                result, df = run_agent(tmp_path, query)
        except Exception as e:
            result = {"error": str(e)}
            df     = None
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        st.session_state.chat_history.append({
            "question": query,
            "result":   result,
            "df":       df,
        })
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# CLEAR CHAT
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
ca, cb = st.columns([1, 6])
with ca:
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()