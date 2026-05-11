📊 CSV Data Analyst Agent

An enterprise-grade **AI-powered data analysis tool** designed to transform static CSV, TXT, and Excel files into interactive, actionable insights. This agent uses natural language processing to handle complex queries, generate professional visualizations, and provide instant statistical reports.

---

## 🛠️ Tech Stack
* **Core Engine:** Python
* **Data Processing:** Pandas, OpenPyXL 
* **Visualization:** Matplotlib
* **Interface:** Streamlit 

---

## ✨ Key Features
* **Natural Language Querying:** Ask questions like "total salary," "average age," or "who earns above average?" to get instant answers.
* **Automated Visualizations:** Dynamically generate **Line Graphs**, **Bar Charts**, and **Pie Charts** based on your dataset.
* **Smart Column Detection:** Automatically identifies categorical data (like names) and numerical data while filtering out noise like ID columns.
* **Multi-Format Support:** Seamlessly process `.csv`, `.txt`, and `.xlsx` files.
* **Export Capabilities:** Download your processed analysis results back into Excel or CSV format directly from the chat interface.

---

## ⚙️ Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/snehagondinigari24-lab/CSV-agent.git
    cd csv-analyst-agent
    ```

2.  **Initialize Environment**
    ```bash
    python -m venv venv
    # Windows
    .\\venv\\Scripts\\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

---

## 🚀 Usage

To launch the interactive web dashboard:
```bash
streamlit run app/streamlit_app.py

📁 Project Structure   

agent.py: The core logic for query detection and data analysis.

streamlit_app.py: The Streamlit frontend and chat interface management.

utils.py: Helper functions for file loading and chart generation.

main.py: Entry point for non-UI agent execution.

requirements.txt: Project dependency list.
