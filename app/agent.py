from utils import (
    load_csv, basic_analysis, get_columns,
    generate_line_plot, generate_bar_chart, generate_pie_chart,
    generate_histogram, generate_scatter_plot,
    generate_html_table, generate_summary_table_html, generate_schema_table_html,
)
import pandas as pd


def get_target_column(query, df):
    q = query.lower()
    for col in sorted(df.columns, key=len, reverse=True):
        if col.lower() in q:
            return col
    return None


def get_target_person(query, df):
    q = query.lower()
    for col in df.select_dtypes(include='object').columns:
        for val in df[col]:
            if str(val).lower() in q:
                return col, val
    return None, None


def run_agent(file_path, query="total"):
    df               = load_csv(file_path)
    total, avg       = basic_analysis(df)
    num_col, cat_col = get_columns(df)
    result           = {}
    q                = query.lower()

    target_col = get_target_column(query, df)
    active_num_col = (
        target_col
        if target_col and pd.api.types.is_numeric_dtype(df[target_col])
        else num_col
    )

    # ── SUMMARY → answer text + stats table + bar chart only
    if any(w in q for w in ["summary", "summarize", "overview", "report",
                             "analyse", "analyze", "describe"]):
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        lines = [f"### 📊 Data Summary\n- **Total Records:** {len(df):,}"]
        for col in numeric_cols:
            lines.append(
                f"- **{col}** → "
                f"Total: `{df[col].sum():,.2f}` | "
                f"Avg: `{df[col].mean():,.2f}` | "
                f"Max: `{df[col].max():,.2f}` | "
                f"Min: `{df[col].min():,.2f}`"
            )
        result["answer"] = "\n".join(lines)
        result["table"]  = generate_summary_table_html(df)
        result["bar"]    = generate_bar_chart(df, active_num_col, cat_col)

    # ── MAX → answer only
    elif any(w in q for w in ["maximum", "highest", "max", "most",
                               "best", "largest", "greatest"]):
        max_val = df[active_num_col].max()
        max_idx = df[active_num_col].idxmax()
        max_cat = df[cat_col][max_idx] if cat_col else f"Row {max_idx}"
        result["answer"] = (
            f"🏆 **Maximum {active_num_col}:** `{max_val:,.2f}`"
            + (f"\n\n📌 **{cat_col}:** {max_cat}" if cat_col else "")
        )

    # ── MIN → answer only
    elif any(w in q for w in ["minimum", "lowest", "min", "least",
                               "worst", "smallest", "bottom"]):
        min_val = df[active_num_col].min()
        min_idx = df[active_num_col].idxmin()
        min_cat = df[cat_col][min_idx] if cat_col else f"Row {min_idx}"
        result["answer"] = (
            f"📉 **Minimum {active_num_col}:** `{min_val:,.2f}`"
            + (f"\n\n📌 **{cat_col}:** {min_cat}" if cat_col else "")
        )

    # ── AVERAGE → answer only
    elif any(w in q for w in ["average", "avg", "mean"]):
        col_avg = df[active_num_col].mean()
        result["average_sales"] = col_avg
        result["label"]         = active_num_col
        result["answer"]        = f"📊 **Average {active_num_col}:** `{col_avg:,.2f}`"

    # ── TOTAL → answer only
    elif any(w in q for w in ["total", "sum", "overall", "combined"]):
        col_total = df[active_num_col].sum()
        result["total_sales"] = col_total
        result["label"]       = active_num_col
        result["answer"]      = f"💰 **Total {active_num_col}:** `{col_total:,.2f}`"

    # ── COUNT → answer only
    elif any(w in q for w in ["count", "how many", "number of",
                               "rows", "records", "entries"]):
        result["answer"] = f"🔢 **Total records in dataset:** `{len(df):,}`"

    # ── COLUMNS → schema table only
    elif any(w in q for w in ["column", "fields", "schema", "structure", "columns"]):
        col_list = ", ".join(f"`{c}`" for c in df.columns)
        result["answer"] = f"🗂️ **Columns ({len(df.columns)}):** {col_list}"
        result["table"]  = generate_schema_table_html(df)

    # ── SHOW VALUE → answer only
    elif any(w in q for w in ["show", "what is", "tell me", "find",
                               "get", "value", "of", "for", "fetch"]):
        person_col, person_val = get_target_person(query, df)
        if person_val and target_col:
            row = df[df[person_col] == person_val]
            val = row[target_col].values[0]
            result["answer"] = f"📌 **{person_val}** → **{target_col}:** `{val}`"
        elif person_val:
            row   = df[df[person_col] == person_val].iloc[[0]]
            lines = [f"📌 **{person_val}** details:"]
            for col in df.columns:
                lines.append(f"- **{col}:** {row[col].values[0]}")
            result["answer"] = "\n".join(lines)
        else:
            result["answer"] = (
                "❓ Please mention a column name or person's name.\n\n"
                "Examples: *`show salary of Alice`* or *`what is age of Bob`*"
            )

    # ── ABOVE AVERAGE → answer + filtered table only
    elif any(w in q for w in ["above average", "more than average",
                               "better than average", "above avg"]):
        col_avg = df[active_num_col].mean()
        above   = df[df[active_num_col] > col_avg].sort_values(active_num_col, ascending=False)
        names   = (", ".join(above[cat_col].astype(str).tolist()[:10])
                   if cat_col else f"{len(above)} records")
        result["answer"] = (
            f"📈 **Above Average {active_num_col}** (avg = `{col_avg:,.2f}`):\n\n"
            f"**{len(above)} records** → {names}"
        )
        result["table"] = generate_html_table(
            above, f"📈 Above Average {active_num_col}"
        )

    # ── BELOW AVERAGE → answer + filtered table only
    elif any(w in q for w in ["below average", "less than average",
                               "under average", "below avg"]):
        col_avg = df[active_num_col].mean()
        below   = df[df[active_num_col] < col_avg].sort_values(active_num_col)
        names   = (", ".join(below[cat_col].astype(str).tolist()[:10])
                   if cat_col else f"{len(below)} records")
        result["answer"] = (
            f"📉 **Below Average {active_num_col}** (avg = `{col_avg:,.2f}`):\n\n"
            f"**{len(below)} records** → {names}"
        )
        result["table"] = generate_html_table(
            below, f"📉 Below Average {active_num_col}"
        )

    # ── BAR CHART → bar chart only
    elif any(w in q for w in ["bar", "column chart", "compare"]):
        result["answer"] = f"📊 Bar chart — **{active_num_col}**"
        result["bar"]    = generate_bar_chart(df, active_num_col, cat_col)

    # ── PIE CHART → pie chart only
    elif any(w in q for w in ["pie", "share", "percentage",
                               "proportion", "breakdown"]):
        result["answer"] = f"🥧 Pie chart — **{active_num_col}**"
        result["pie"]    = generate_pie_chart(df, active_num_col, cat_col)

    # ── LINE / TREND → line chart only
    elif any(w in q for w in ["trend", "line", "graph", "plot",
                               "growth", "over time"]):
        result["answer"] = f"📈 Line trend — **{active_num_col}**"
        result["line"]   = generate_line_plot(df, active_num_col, cat_col)

    # ── HISTOGRAM → histogram only
    elif any(w in q for w in ["histogram", "frequency", "distribution",
                               "spread", "range"]):
        result["answer"]    = f"📊 Histogram — **{active_num_col}**"
        result["histogram"] = generate_histogram(df, active_num_col)

    # ── SCATTER → scatter chart only
    elif any(w in q for w in ["scatter", "correlation", "vs",
                               "versus", "relationship"]):
        num_cols = df.select_dtypes(include='number').columns.tolist()
        if len(num_cols) >= 2:
            x_col, y_col = num_cols[0], num_cols[1]
            for c in num_cols:
                if c.lower() in q:
                    y_col = c
                    break
            sc = generate_scatter_plot(df, x_col, y_col)
            if sc:
                result["answer"]  = f"🔵 Scatter — **{x_col}** vs **{y_col}**"
                result["scatter"] = sc
        else:
            result["answer"] = "Need at least 2 numeric columns for a scatter plot."

    # ── SORT → sorted table only
    elif any(w in q for w in ["sort", "rank", "order", "ranked"]):
        asc        = any(w in q for w in ["ascending", "lowest first"])
        sorted_df  = df.sort_values(active_num_col, ascending=asc)
        order_word = "Ascending ↑" if asc else "Descending ↓"
        result["answer"] = f"🔢 **{active_num_col}** sorted — {order_word}"
        result["table"]  = generate_html_table(
            sorted_df, f"📋 {active_num_col} — {order_word}"
        )

    # ── FALLBACK → help text only
    else:
        result["answer"] = (
            "🤖 **Try asking one of these:**\n\n"
            "- `summary` — Full data report\n"
            "- `total salary` — Sum of a column\n"
            "- `average age` — Mean of a column\n"
            "- `maximum sales` — Highest value\n"
            "- `minimum salary` — Lowest value\n"
            "- `show salary of Alice` — Specific person\n"
            "- `above average salary` — Above avg records\n"
            "- `bar chart` — Bar chart\n"
            "- `pie chart` — Pie chart\n"
            "- `trend` — Line graph\n"
            "- `histogram` — Distribution\n"
            "- `scatter` — Correlation plot\n"
            "- `sort by salary` — Ranked table\n"
            "- `columns` — Schema info\n"
            "- `count` — Total rows"
        )

    return result, df