from helpers import get_file_contents
from langchain_ollama import ChatOllama

model_ = ChatOllama(
    # sam4096/qwen2tools:0.5b
    model="llama3.1",
    temperature=0.7,
    num_predict=-1,
)

text_source = "story.txt"
text = get_file_contents(f"data/{text_source}")


model_.invoke(text)
