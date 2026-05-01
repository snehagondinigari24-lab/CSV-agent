import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import io


def load_csv(file_path):
    if file_path.endswith('.xlsx'):
        return pd.read_excel(file_path)
    return pd.read_csv(file_path)


def get_columns(df):
    """
    Auto-detect the best numeric and categorical columns.
    Skips ID-like columns (single word 'id', ends with '_id', or all unique ints).
    Returns: (num_col, cat_col)
    """
    # Numeric columns - exclude ID-like columns
    all_numeric = df.select_dtypes(include='number').columns.tolist()
    numeric_cols = []
    for col in all_numeric:
        col_lower = col.lower()
        # Skip columns that look like IDs
        if col_lower == 'id' or col_lower.endswith('_id') or col_lower.endswith('id'):
            continue
        # Skip if all values are unique integers (likely an ID)
        if df[col].nunique() == len(df) and df[col].dtype in ['int64', 'int32']:
            continue
        numeric_cols.append(col)

    # If all numeric cols were filtered out, use any numeric col
    if not numeric_cols:
        numeric_cols = all_numeric

    # Categorical columns
    text_cols = df.select_dtypes(include='object').columns.tolist()

    # Prefer 'Name' column as cat_col if it exists
    cat_col = None
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
    total = df[num_col].sum()
    avg = df[num_col].mean()
    return total, avg


def fig_to_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf


def generate_line_plot(df):
    num_col, cat_col = get_columns(df)
    fig, ax = plt.subplots(figsize=(9, 4))
    if cat_col:
        ax.plot(df[cat_col], df[num_col], marker='o',
                color='steelblue', linewidth=2)
        ax.set_xlabel(cat_col)
        plt.xticks(rotation=45, ha='right')
    else:
        ax.plot(df[num_col], marker='o', color='steelblue', linewidth=2)
    ax.set_title(f"{num_col} Trend (Line)")
    ax.set_ylabel(num_col)
    plt.tight_layout()
    return fig_to_bytes(fig)


def generate_bar_chart(df):
    num_col, cat_col = get_columns(df)
    fig, ax = plt.subplots(figsize=(9, 4))
    if cat_col:
        bars = ax.bar(df[cat_col], df[num_col],
                      color='coral', edgecolor='black')
        ax.set_xlabel(cat_col)
        plt.xticks(rotation=45, ha='right')
        # Add value labels on bars
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.5,
                    f'{bar.get_height():,.0f}',
                    ha='center', va='bottom', fontsize=8)
    else:
        ax.bar(range(len(df)), df[num_col],
               color='coral', edgecolor='black')
    ax.set_title(f"{num_col} Bar Chart")
    ax.set_ylabel(num_col)
    plt.tight_layout()
    return fig_to_bytes(fig)


def generate_pie_chart(df):
    num_col, cat_col = get_columns(df)
    fig, ax = plt.subplots(figsize=(7, 7))
    labels = df[cat_col] if cat_col else range(len(df))
    ax.pie(df[num_col], labels=labels,
           autopct='%1.1f%%', startangle=140)
    ax.set_title(f"{num_col} Distribution (Pie)")
    plt.tight_layout()
    return fig_to_bytes(fig)