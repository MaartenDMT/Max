import pandas as pd
from latent_space_activation import ReasoningAgent
from langchain_core.messages import HumanMessage, AIMessage

class DataAnalysisAgent:
    def __init__(self, data_filepath: str):
        self.data_filepath = data_filepath
        self.df = self._load_data()
        self.reasoning_agent = ReasoningAgent()

    def _load_data(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(self.data_filepath)
            print(f"Data loaded successfully from {self.data_filepath}")
            print("DataFrame head:")
            print(df.head())
            return df
        except FileNotFoundError:
            print(f"Error: Data file not found at {self.data_filepath}")
            return pd.DataFrame()

    def analyze_query(self, query: str) -> AIMessage:
        """
        Analyzes a natural language query about the dataset and provides an answer.
        """
        if self.df.empty:
            return AIMessage(content="No data loaded to analyze.")

        # Use ReasoningAgent to interpret the query and suggest a pandas operation
        # This is a simplified approach; a more robust solution would involve function calling or more complex parsing.
        prompt = f"Given the following DataFrame columns: {list(self.df.columns)}, and the query: '{query}'.\n\nSuggest a Python pandas operation to answer this query. Be very concise and only provide the pandas code snippet. If the query asks for a summary, provide a general summary of the data."
        
        # Set a specific latent space control for data analysis context
        self.reasoning_agent.set_latent_space_control("Focus on data analysis, statistics, and pandas operations.")
        
        pandas_suggestion = self.reasoning_agent.expert_bot(prompt).content
        print(f"\nAI's Pandas suggestion: {pandas_suggestion}")

        try:
            # Attempt to execute the pandas suggestion
            # WARNING: Executing arbitrary code from LLM is a security risk in a real application.
            # This is for sandbox experimentation only.
            if "df." in pandas_suggestion:
                # Prepend 'self.' to df if it's a method call on self.df
                executable_code = pandas_suggestion.replace("df.", "self.df.")
            else:
                executable_code = pandas_suggestion

            # Evaluate the code. Use a limited global/local scope for safety in a real app.
            result = eval(executable_code, {'pd': pd, 'self': self})
            return AIMessage(content=f"Analysis Result: {result}")
        except Exception as e:
            return AIMessage(content=f"Could not perform analysis. Error: {e}\nAI's suggestion: {pandas_suggestion}")

if __name__ == "__main__":
    data_agent = DataAnalysisAgent("sample_data.csv")

    print("\n--- Data Analysis Queries ---")

    queries = [
        "What are the average ages of people in each city?",
        "Show me the maximum salary.",
        "How many people are Engineers?",
        "What is the average salary for each occupation?",
        "Describe the data."
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        response = data_agent.analyze_query(query)
        print(f"Response: {response.content}")
