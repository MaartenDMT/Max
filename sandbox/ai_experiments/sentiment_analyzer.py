from latent_space_activation import ReasoningAgent
from langchain_core.messages import HumanMessage, AIMessage

def analyze_sentiment(text: str) -> AIMessage:
    """
    Analyzes the sentiment of the given text using the ReasoningAgent.
    Returns an AIMessage containing the sentiment (positive, negative, or neutral).
    """
    agent = ReasoningAgent()
    prompt = f"Analyze the sentiment of the following text and classify it as positive, negative, or neutral. Provide only the sentiment word (e.g., Positive, Negative, Neutral).\n\nText: {text}"
    sentiment_response = agent.expert_bot(prompt)
    return sentiment_response

if __name__ == "__main__":
    print("--- Sentiment Analysis Examples ---")

    texts = [
        "I love this product! It's amazing and works perfectly.",
        "This is absolutely terrible. I'm very disappointed.",
        "The weather today is neither good nor bad.",
        "The service was okay, but nothing special."
    ]

    for i, text in enumerate(texts):
        print(f"\nExample {i+1}:\nText: {text}")
        sentiment = analyze_sentiment(text)
        print(f"Sentiment: {sentiment.content}")
