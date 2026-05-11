import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io
import os

# ─────────────────────────────────────────────────────────────────────────────
# LOAD CSS FROM templates.html
# CSS class names (data-table, stats-table, etc.) are defined there.
# Edit templates.html to change styles — no need to touch this file.
# ─────────────────────────────────────────────────────────────────────────────
_TABLE_CLASS  = "data-table"
_STATS_CLASS  = "data-table stats-table"
_SCHEMA_CLASS = "data-table schema-table"

def _load_css():
    """Extract <style>…</style> block from templates.html."""
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

TEMPLATE_CSS = _load_css()      # loaded once at import time


# ─────────────────────────────────────────────────────────────────────────────
# FILE LOADING
# ─────────────────────────────────────────────────────────────────────────────
def load_csv(file_path):
    if file_path.endswith('.xlsx'):
        return pd.read_excel(file_path)
    if file_path.endswith('.txt'):
        try:
            df = pd.read_csv(file_path, sep='\t')
            if len(df.columns) > 1:
                return df
        except Exception:
            pass
    return pd.read_csv(file_path)


# ─────────────────────────────────────────────────────────────────────────────
# COLUMN DETECTION
# ─────────────────────────────────────────────────────────────────────────────
def get_columns(df):
    """Auto-detect best numeric + categorical columns. Skips ID columns."""
    all_numeric  = df.select_dtypes(include='number').columns.tolist()
    numeric_cols = []
    for col in all_numeric:
        cl = col.lower()
        if cl == 'id' or cl.endswith('_id') or cl.endswith('id'):
            continue
        if df[col].nunique() == len(df) and df[col].dtype in ['int64', 'int32']:
            continue
        numeric_cols.append(col)
    if not numeric_cols:
        numeric_cols = all_numeric

    text_cols = df.select_dtypes(include='object').columns.tolist()
    cat_col   = None
    for col in text_cols:
        if col.lower() == 'name':
            cat_col = col
            break
    if cat_col is None:
        cat_col = text_cols[0] if text_cols else None

    num_col = numeric_cols[0] if numeric_cols else (all_numeric[0] if all_numeric else None)
    return num_col, cat_col


def basic_analysis(df):
    num_col, _ = get_columns(df)
    if num_col:
        return df[num_col].sum(), df[num_col].mean()
    return len(df), 0


# ─────────────────────────────────────────────────────────────────────────────
# HTML TABLE BUILDERS
# All class names come from templates.html
# ─────────────────────────────────────────────────────────────────────────────
def _wrap(table_html, title="", note="", css_class=_TABLE_CLASS):
    """Wrap a pandas .to_html() table with template container divs."""
    table_html = table_html.replace('class="dataframe"', f'class="{css_class}"')
    title_div  = f'<div class="table-title">{title}</div>'  if title else ""
    note_div   = f'<div class="table-note">{note}</div>'    if note  else ""
    return (
        TEMPLATE_CSS
        + f'<div class="table-container">{title_div}{note_div}{table_html}</div>'
    )


def generate_html_table(df, title="Data Table", max_rows=50):
    """Styled data table from any DataFrame using classes from templates.html."""
    display_df = df.head(max_rows).copy()
    for col in display_df.select_dtypes(include='float'):
        display_df[col] = display_df[col].round(2)
    note = f"Showing {len(display_df)} of {len(df)} rows" if len(df) > max_rows else ""
    html = display_df.to_html(index=False, border=0, justify='left')
    return _wrap(html, title, note, _TABLE_CLASS)


def generate_summary_table_html(df):
    """Statistical summary table (describe) for all numeric columns."""
    num_df = df.select_dtypes(include='number')
    if num_df.empty:
        return ""
    stats = num_df.describe().T
    stats = stats[['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']].round(2)
    stats.columns = ['Count', 'Mean', 'Std Dev', 'Min', '25%', 'Median', '75%', 'Max']
    html = stats.to_html(border=0)
    return _wrap(html, "📊 Statistical Summary", css_class=_STATS_CLASS)


def generate_schema_table_html(df):
    """Column info: type, non-null count, unique count, sample value."""
    info = pd.DataFrame({
        "Column":   df.columns,
        "Type":     df.dtypes.astype(str).values,
        "Non-Null": df.count().values,
        "Unique":   df.nunique().values,
        "Sample":   [str(df[c].iloc[0]) if len(df) > 0 else "" for c in df.columns],
    })
    html = info.to_html(index=False, border=0, justify='left')
    return _wrap(html, "🗂️ Column Schema", css_class=_SCHEMA_CLASS)


def generate_column_pills_html(df):
    """Inline pills for each column name (used after file upload)."""
    pills = "".join(f'<span class="pill">{c}</span>' for c in df.columns)
    return (
        TEMPLATE_CSS
        + '<p style="margin:6px 0 4px;font-weight:600;">Detected columns:</p>'
        + pills
    )


# ─────────────────────────────────────────────────────────────────────────────
# CHART PALETTE & AXIS STYLING
# ─────────────────────────────────────────────────────────────────────────────
_PALETTE = [
    "#4f46e5", "#7c3aed", "#2563eb", "#0891b2",
    "#059669", "#d97706", "#dc2626", "#db2777",
    "#65a30d", "#0f766e",
]

def _style_ax(ax, title=""):
    ax.set_title(title, fontsize=13, fontweight='bold', pad=12, color='#1f2937')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#d1d5db')
    ax.spines['bottom'].set_color('#d1d5db')
    ax.tick_params(colors='#6b7280', labelsize=9)
    ax.set_facecolor('#f9fafb')

def _fig_to_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=130)
    buf.seek(0)
    plt.close(fig)
    return buf


# ─────────────────────────────────────────────────────────────────────────────
# CHART GENERATORS
# ─────────────────────────────────────────────────────────────────────────────
def generate_line_plot(df, num_col=None, cat_col=None):
    if not num_col or not cat_col:
        _n, _c = get_columns(df)
        num_col = num_col or _n
        cat_col = cat_col or _c

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor('white')

    if cat_col and cat_col in df.columns:
        x_labels = df[cat_col].astype(str)
        y_vals   = df[num_col]
        xs = range(len(x_labels))
        ax.plot(xs, y_vals, marker='o', color='#4f46e5', linewidth=2.5,
                markersize=7, markerfacecolor='white', markeredgewidth=2.5)
        ax.fill_between(xs, y_vals, alpha=0.12, color='#4f46e5')
        ax.set_xticks(xs)
        ax.set_xticklabels(x_labels, rotation=30, ha='right')
        ax.set_xlabel(cat_col, fontsize=10, color='#6b7280', labelpad=6)
        for xi, yi in zip(xs, y_vals):
            ax.text(xi, yi + max(y_vals) * 0.015, f'{yi:,.0f}',
                    ha='center', fontsize=8, color='#374151')
    else:
        ax.plot(df[num_col], marker='o', color='#4f46e5', linewidth=2.5, markersize=6)

    ax.set_ylabel(num_col, fontsize=10, color='#6b7280')
    _style_ax(ax, f"📈 {num_col} Trend")
    plt.tight_layout()
    return _fig_to_bytes(fig)


def generate_bar_chart(df, num_col=None, cat_col=None):
    if not num_col or not cat_col:
        _n, _c = get_columns(df)
        num_col = num_col or _n
        cat_col = cat_col or _c

    plot_df = df.nlargest(15, num_col) if (cat_col and num_col) else df

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('white')

    if cat_col and cat_col in df.columns:
        colors = [_PALETTE[i % len(_PALETTE)] for i in range(len(plot_df))]
        bars   = ax.bar(plot_df[cat_col].astype(str), plot_df[num_col],
                        color=colors, edgecolor='white', linewidth=0.8)
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2,
                    h + max(plot_df[num_col]) * 0.01,
                    f'{h:,.0f}', ha='center', va='bottom', fontsize=8, color='#374151')
        ax.set_xticklabels(plot_df[cat_col].astype(str), rotation=30, ha='right')
        ax.set_xlabel(cat_col, fontsize=10, color='#6b7280')
    else:
        ax.bar(range(len(plot_df)), plot_df[num_col], color='#4f46e5')

    ax.set_ylabel(num_col, fontsize=10, color='#6b7280')
    _style_ax(ax, f"📊 {num_col} by {cat_col}" if cat_col else f"📊 {num_col}")
    plt.tight_layout()
    return _fig_to_bytes(fig)


def generate_pie_chart(df, num_col=None, cat_col=None):
    if not num_col or not cat_col:
        _n, _c = get_columns(df)
        num_col = num_col or _n
        cat_col = cat_col or _c

    plot_df = df.nlargest(10, num_col) if (cat_col and num_col) else df

    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor('white')
    labels = plot_df[cat_col].astype(str) if cat_col else range(len(plot_df))
    colors = [_PALETTE[i % len(_PALETTE)] for i in range(len(plot_df))]

    wedges, texts, autotexts = ax.pie(
        plot_df[num_col], labels=labels, autopct='%1.1f%%',
        startangle=140, colors=colors,
        wedgeprops=dict(edgecolor='white', linewidth=2)
    )
    for at in autotexts:
        at.set_fontsize(9)
        at.set_color('#1f2937')

    ax.set_title(f"🥧 {num_col} Distribution",
                 fontsize=13, fontweight='bold', color='#1f2937', pad=15)
    plt.tight_layout()
    return _fig_to_bytes(fig)


def generate_histogram(df, num_col=None):
    if not num_col:
        num_col, _ = get_columns(df)

    fig, ax = plt.subplots(figsize=(9, 4))
    fig.patch.set_facecolor('white')
    data = df[num_col].dropna()
    n, bins, patches = ax.hist(data, bins=20, edgecolor='white', alpha=0.9)

    cmap = plt.cm.Blues
    for i, patch in enumerate(patches):
        patch.set_facecolor(cmap(0.4 + 0.6 * i / len(patches)))

    mean_val = data.mean()
    ax.axvline(mean_val, color='#dc2626', linewidth=2, linestyle='--')
    ax.text(mean_val, max(n) * 0.93,
            f'  Mean\n  {mean_val:,.1f}', color='#dc2626', fontsize=9)

    ax.set_xlabel(num_col, fontsize=10, color='#6b7280')
    ax.set_ylabel('Frequency', fontsize=10, color='#6b7280')
    _style_ax(ax, f"📊 {num_col} Distribution (Histogram)")
    plt.tight_layout()
    return _fig_to_bytes(fig)


def generate_scatter_plot(df, x_col=None, y_col=None):
    num_cols = df.select_dtypes(include='number').columns.tolist()
    if len(num_cols) < 2:
        return None
    x_col = x_col or num_cols[0]
    y_col = y_col or num_cols[1]

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor('white')
    ax.scatter(df[x_col], df[y_col], color='#4f46e5', alpha=0.7,
               edgecolors='white', linewidth=0.5, s=70)
    try:
        z  = np.polyfit(df[x_col].dropna(), df[y_col].dropna(), 1)
        p  = np.poly1d(z)
        xs = np.linspace(df[x_col].min(), df[x_col].max(), 100)
        ax.plot(xs, p(xs), color='#dc2626', linewidth=1.5,
                linestyle='--', alpha=0.8, label='Trend')
        ax.legend(fontsize=9)
    except Exception:
        pass

    ax.set_xlabel(x_col, fontsize=10, color='#6b7280')
    ax.set_ylabel(y_col, fontsize=10, color='#6b7280')
    _style_ax(ax, f"🔵 {x_col} vs {y_col}")
    plt.tight_layout()
    return _fig_to_bytes(fig)