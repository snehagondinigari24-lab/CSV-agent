from utils import (load_csv, basic_analysis, get_columns,
                   generate_line_plot, generate_bar_chart, generate_pie_chart)
import pandas as pd


def get_target_column(query, df):
    """Detect which column the user is asking about from the query."""
    q = query.lower()
    for col in df.columns:
        if col.lower() in q:
            return col
    return None


def get_target_person(query, df):
    """Detect if user mentioned a specific row value (e.g., a person's name)."""
    q = query.lower()
    for col in df.select_dtypes(include='object').columns:
        for val in df[col]:
            if str(val).lower() in q:
                return col, val
    return None, None


def run_agent(file_path, query="total"):
    df = load_csv(file_path)
    total, avg = basic_analysis(df)
    num_col, cat_col = get_columns(df)

    q = query.lower()
    result = {}

    # ── Detect specific column mentioned in query ──────────────────────────
    target_col = get_target_column(query, df)

    # Use target column if it's numeric, else fall back to default num_col
    if target_col and pd.api.types.is_numeric_dtype(df[target_col]):
        active_num_col = target_col
    else:
        active_num_col = num_col  # default (e.g., Salary)

    # ── SUMMARY ────────────────────────────────────────────────────────────
    if any(w in q for w in ["summary", "summarize", "overview", "report",
                             "analyse", "analyze", "all", "describe"]):
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        summary_lines = [f"### 📊 Data Summary\n- 📋 **Total Records:** {len(df)}"]
        for col in numeric_cols:
            summary_lines.append(
                f"- **{col}** → Total: {df[col].sum():,.0f} | "
                f"Avg: {df[col].mean():,.2f} | "
                f"Max: {df[col].max():,.0f} | "
                f"Min: {df[col].min():,.0f}"
            )
        result["answer"] = "\n".join(summary_lines)
        result["line"] = generate_line_plot(df)

    # ── MAX / HIGHEST ──────────────────────────────────────────────────────
    elif any(w in q for w in ["maximum", "highest", "max", "most", "top",
                               "best", "largest", "greatest"]):
        max_val = df[active_num_col].max()
        max_idx = df[active_num_col].idxmax()
        max_cat = df[cat_col][max_idx] if cat_col else f"Row {max_idx}"
        result["answer"] = (
            f"🏆 **Maximum {active_num_col}:** `{max_val:,.0f}`"
            + (f"\n👤 Person/Category: **{max_cat}**" if cat_col else "")
        )

    # ── MIN / LOWEST ───────────────────────────────────────────────────────
    elif any(w in q for w in ["minimum", "lowest", "min", "least",
                               "worst", "smallest"]):
        min_val = df[active_num_col].min()
        min_idx = df[active_num_col].idxmin()
        min_cat = df[cat_col][min_idx] if cat_col else f"Row {min_idx}"
        result["answer"] = (
            f"📉 **Minimum {active_num_col}:** `{min_val:,.0f}`"
            + (f"\n👤 Person/Category: **{min_cat}**" if cat_col else "")
        )

    # ── AVERAGE ────────────────────────────────────────────────────────────
    elif any(w in q for w in ["average", "avg", "mean"]):
        col_avg = df[active_num_col].mean()
        result["average_sales"] = col_avg
        result["label"] = active_num_col
        result["answer"] = f"📊 **Average {active_num_col}:** `{col_avg:,.2f}`"

    # ── TOTAL ──────────────────────────────────────────────────────────────
    elif any(w in q for w in ["total", "sum", "overall", "combined"]):
        col_total = df[active_num_col].sum()
        result["total_sales"] = col_total
        result["label"] = active_num_col
        result["answer"] = f"💰 **Total {active_num_col}:** `{col_total:,.0f}`"

    # ── COUNT ──────────────────────────────────────────────────────────────
    elif any(w in q for w in ["count", "how many", "number of", "rows",
                               "records", "entries"]):
        result["answer"] = f"📋 **Total records in dataset:** `{len(df)}`"

    # ── COLUMNS / FIELDS ───────────────────────────────────────────────────
    elif any(w in q for w in ["column", "what data", "fields", "preview",
                               "show data", "schema", "structure"]):
        col_list = ", ".join(df.columns.tolist())
        result["answer"] = f"📋 **Columns ({len(df.columns)}):** {col_list}"

    # ── SHOW VALUE for specific person/row ────────────────────────────────
    elif any(w in q for w in ["show", "what is", "tell me", "find",
                               "get", "value", "of", "for"]):
        person_col, person_val = get_target_person(query, df)
        if person_val and target_col:
            row = df[df[person_col] == person_val]
            val = row[target_col].values[0]
            result["answer"] = (
                f"📌 **{person_val}** → **{target_col}:** `{val}`"
            )
        elif person_val:
            row = df[df[person_col] == person_val].iloc[0]
            lines = [f"📌 **{person_val}** details:"]
            for col in df.columns:
                lines.append(f"  - {col}: `{row[col]}`")
            result["answer"] = "\n".join(lines)
        elif target_col:
            vals = df[target_col].tolist()
            result["answer"] = (
                f"📋 **{target_col}** values:\n"
                + "\n".join([f"  - {v}" for v in vals[:20]])
                + (f"\n  _(showing first 20 of {len(vals)})_" if len(vals) > 20 else "")
            )
        else:
            result["answer"] = (
                "❓ Please mention a column name or person's name.\n"
                "Example: *'show age of John'* or *'what is salary of Jane'*"
            )

    # ── ABOVE AVERAGE ──────────────────────────────────────────────────────
    elif any(w in q for w in ["above average", "more than average",
                               "better than average", "above avg"]):
        col_avg = df[active_num_col].mean()
        above = df[df[active_num_col] > col_avg]
        if cat_col:
            items = ", ".join(above[cat_col].tolist())
        else:
            items = str(len(above))
        result["answer"] = (
            f"📈 **Above average {active_num_col}** (avg = {col_avg:,.2f}):\n"
            f"**{len(above)} records** → {items}"
        )

    # ── BELOW AVERAGE ──────────────────────────────────────────────────────
    elif any(w in q for w in ["below average", "less than average",
                               "under average", "below avg"]):
        col_avg = df[active_num_col].mean()
        below = df[df[active_num_col] < col_avg]
        if cat_col:
            items = ", ".join(below[cat_col].tolist())
        else:
            items = str(len(below))
        result["answer"] = (
            f"📉 **Below average {active_num_col}** (avg = {col_avg:,.2f}):\n"
            f"**{len(below)} records** → {items}"
        )

    # ── BAR CHART ──────────────────────────────────────────────────────────
    elif any(w in q for w in ["bar", "column chart", "compare"]):
        result["bar"] = generate_bar_chart(df)

    # ── PIE CHART ──────────────────────────────────────────────────────────
    elif any(w in q for w in ["pie", "share", "percentage",
                               "proportion", "distribution"]):
        result["pie"] = generate_pie_chart(df)

    # ── LINE / TREND ───────────────────────────────────────────────────────
    elif any(w in q for w in ["trend", "line", "graph", "plot",
                               "growth", "over time"]):
        result["line"] = generate_line_plot(df)

    # ── DEFAULT ────────────────────────────────────────────────────────────
    else:
        result["answer"] = (
            "🤖 **Try asking:**\n"
            "- `summary` — Full data report\n"
            "- `total salary` — Sum of salary column\n"
            "- `average age` — Mean of age column\n"
            "- `maximum age` — Highest age value\n"
            "- `minimum salary` — Lowest salary\n"
            "- `show age of John` — Specific person's value\n"
            "- `above average salary` — Who earns above avg\n"
            "- `bar chart` — Bar chart\n"
            "- `pie chart` — Pie chart\n"
            "- `trend` — Line graph\n"
            "- `columns` — List all columns"
        )

    return result, df