from latent_space_activation import ReasoningAgent
from langchain_core.messages import HumanMessage, AIMessage

def run_text_summarization_agent(long_text: str):
    """
    Runs a text summarization and critique workflow using the ReasoningAgent.
    """
    agent = ReasoningAgent()
    print("--- Original Text ---")
    print(long_text)
    print("\n" + "="*30 + "\n")

    # 1. Expert Bot summarizes the text
    print("--- Expert Bot: Generating Initial Summary ---")
    initial_summary_prompt = f"Summarize the following text concisely and accurately: {long_text}"
    initial_summary = agent.expert_bot(initial_summary_prompt)
    print(f"Initial Summary: {initial_summary.content}\n")

    # 2. Grading Bot critiques the summary
    print("--- Grading Bot: Critiquing Initial Summary ---")
    critique_prompt = f"Original text: {long_text}\nSummary: {initial_summary.content}\nCritique this summary for accuracy, conciseness, and completeness. Provide a score out of 5 and suggestions for improvement."
    summary_critique = agent.grading_bot(long_text, initial_summary)
    print(f"Summary Critique: {summary_critique.content}\n")

    # 3. Reformatter Bot refines the summary based on the critique
    print("--- Reformatter Bot: Refining Summary ---")
    refined_summary_prompt = f"Original text: {long_text}\nInitial summary: {initial_summary.content}\nCritique: {summary_critique.content}\nRefine the initial summary based on the critique to make it more accurate, concise, and complete."
    refined_summary = agent.reformatter_bot(AIMessage(content=refined_summary_prompt)) # Pass as AIMessage content
    print(f"Refined Summary: {refined_summary.content}\n")

    print("Text summarization and critique workflow complete.")

if __name__ == "__main__":
    example_text = """
    Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to the natural intelligence displayed by animals and humans. Leading AI textbooks define the field as the study of "intelligent agents": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. Colloquially, the term "artificial intelligence" is often used to describe machines (or computers) that mimic "cognitive" functions that humans associate with the human mind, such as "learning" and "problem-solving".

    AI applications include advanced web search engines (e.g., Google Search), recommendation systems (used by YouTube, Amazon, and Netflix), understanding human speech (such as Siri and Alexa), self-driving cars (e.g., Waymo), and competing at the highest level in strategic game systems (such as chess and Go). As machines become increasingly capable, tasks considered to require "intelligence" are often removed from the definition of AI, a phenomenon known as the AI effect. For instance, optical character recognition is frequently excluded from the definition of AI, having become a routine technology.

    AI was founded as an academic discipline in 1956, and in the years since has experienced several waves of optimism, followed by disappointment and the loss of funding (known as an "AI winter"), followed by new approaches, success, and renewed funding. AI research has received funding from a number of sources, including DARPA. The current trend of AI research is to combine machine learning, machine reasoning, and knowledge representation to create more robust and general AI systems.
    """
    run_text_summarization_agent(example_text)
