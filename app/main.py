from agent import run_agent

if __name__ == "__main__":
    file_path = "../data/sales.txt"
    result = run_agent(file_path)
    print("RESULT:")
    print(result)