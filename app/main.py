from agent import run_agent

if __name__ == "__main__":
    file_path = "../data/employees.csv"   # change to your file

    test_queries = [
        "summary",
        "total salary",
        "average salary",
        "maximum sales",
        "minimum salary",
        "above average salary",
        "histogram",
        "bar chart",
        "pie chart",
        "trend",
        "scatter",
        "sort by salary",
        "columns",
        "count",
        "show salary of Alice",
    ]

    for q in test_queries:
        print(f"\n{'═'*55}")
        print(f"  Query : {q}")
        print(f"{'─'*55}")
        result, df = run_agent(file_path, q)
        print(result.get("answer", "(no answer)"))
        if "table" in result:
            print("  [HTML table generated ✓]")
        charts = [k for k in ("bar","line","pie","histogram","scatter") if k in result]
        if charts:
            print(f"  [Charts generated: {', '.join(charts)} ✓]")