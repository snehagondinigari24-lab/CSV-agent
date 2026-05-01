import streamlit as st
from agent import run_agent
import tempfile
import os
import io
import pandas as pd

st.set_page_config(
    page_title="CSV Analyst Agent",
    page_icon="📊",
    layout="wide"
)

st.title("📊 CSV Data Analyst Agent")

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📘 How to Use")
    st.markdown("**Supported files:** CSV, TXT, XLSX")
    st.markdown("⚠️ PDF files are **not supported**")
    st.markdown("---")
    st.markdown("**Ask these questions:**")
    questions = [
        ("`total salary`", "→ Sum of salary"),
        ("`average age`", "→ Mean of age"),
        ("`maximum age`", "→ Highest age"),
        ("`minimum salary`", "→ Lowest salary"),
        ("`show age of John`", "→ Specific value"),
        ("`above average salary`", "→ Above avg"),
        ("`trend`", "→ Line Graph"),
        ("`bar chart`", "→ Bar Chart"),
        ("`pie chart`", "→ Pie Chart"),
        ("`summary`", "→ Full Report"),
        ("`columns`", "→ List columns"),
        ("`count`", "→ Total rows"),
    ]
    for q, desc in questions:
        st.markdown(f"- {q} {desc}")

# ── File Uploader (NO PDF) ─────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Upload your CSV, TXT or Excel file",
    type=["csv", "txt", "xlsx"],      # ← PDF REMOVED
    help="Only CSV, TXT, and XLSX files are supported."
)

# ── Show columns of uploaded file ─────────────────────────────────────────
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.xlsx'):
            preview_df = pd.read_excel(uploaded_file)
        else:
            preview_df = pd.read_csv(uploaded_file)
        uploaded_file.seek(0)

        col_str = ", ".join(preview_df.columns.tolist())
        st.info(f"📋 **Columns found:** {col_str}")
        st.caption(f"📁 {uploaded_file.name} | {len(preview_df)} rows × {len(preview_df.columns)} columns")

    except Exception as e:
        st.error(f"❌ Could not read file: {e}")

# ── Chat history ───────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display past chats
for idx, chat in enumerate(st.session_state.chat_history):
    with st.chat_message("user"):
        st.write(chat["question"])
    with st.chat_message("assistant"):
        result = chat["result"]

        if "answer" in result:
            st.success(result["answer"])

        label = result.get("label", "Value")
        col1, col2 = st.columns(2)
        if "total_sales" in result:
            col1.metric(f"💰 Total {label}", f"{result['total_sales']:,.0f}")
        if "average_sales" in result:
            col2.metric(f"📊 Average {label}", f"{result['average_sales']:,.2f}")

        if "line" in result:
            st.image(result["line"], caption="📈 Trend")
        if "bar" in result:
            st.image(result["bar"], caption="📊 Bar Chart")
        if "pie" in result:
            st.image(result["pie"], caption="🥧 Pie Chart")

        if "error" in result:
            st.error(f"Error: {result['error']}")

        # Download buttons
        if chat.get("df") is not None:
            df = chat["df"]
            st.markdown("**⬇️ Download:**")
            dcol1, dcol2 = st.columns(2)

            excel_buf = io.BytesIO()
            df.to_excel(excel_buf, index=False, engine='openpyxl')
            excel_buf.seek(0)
            dcol1.download_button(
                "📗 Excel",
                data=excel_buf,
                file_name=f"results_{idx}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"excel_{idx}"
            )

            csv_data = df.to_csv(index=False).encode('utf-8')
            dcol2.download_button(
                "📄 CSV",
                data=csv_data,
                file_name=f"results_{idx}.csv",
                mime="text/csv",
                key=f"csv_{idx}"
            )

# ── Query input ────────────────────────────────────────────────────────────
query = st.chat_input(
    "Ask: total salary, average age, maximum age, bar chart, pie chart..."
)

if query:
    if uploaded_file is None:
        st.warning("⚠️ Please upload a CSV, TXT, or XLSX file first!")
    else:
        ext = uploaded_file.name.split('.')[-1]
        with tempfile.NamedTemporaryFile(delete=False,
                                         suffix=f".{ext}") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        try:
            result, df = run_agent(tmp_path, query)
        except Exception as e:
            result = {"error": str(e)}
            df = None
        finally:
            os.unlink(tmp_path)

        st.session_state.chat_history.append({
            "question": query,
            "result": result,
            "df": df
        })
        st.rerun()

# ── Clear Chat ─────────────────────────────────────────────────────────────
st.divider()
if st.button("🗑️ Clear Chat"):
    st.session_state.chat_history = []
    st.rerun()