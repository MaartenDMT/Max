from latent_space_activation import ReasoningAgent
from langchain_core.messages import HumanMessage, AIMessage

def run_multi_agent_workflow(initial_query: str, max_iterations: int = 3):
    """
    Runs a multi-agent workflow involving an expert, interrogator, and grader bot.
    The expert bot provides an answer, the interrogator asks a follow-up,
    and the grader evaluates the expert's response.
    """
    agent = ReasoningAgent()
    print(f"Initial Query: {initial_query}\n")

    expert_response = agent.expert_bot(initial_query)
    print(f"Expert Bot Initial Response: {expert_response.content}\n")

    for i in range(max_iterations):
        print(f"--- Iteration {i + 1} ---")

        # Interrogator asks a follow-up question
        interrogator_question = agent.interigator_bot(initial_query, expert_response)
        print(f"Interrogator Bot Question: {interrogator_question.content}\n")

        # Expert refines its response based on the interrogator's question
        expert_response = agent.expert_bot(f"{initial_query}\nFollow-up question: {interrogator_question.content}")
        print(f"Expert Bot Refined Response: {expert_response.content}\n")

        # Grader evaluates the expert's refined response
        grader_feedback = agent.grading_bot(initial_query, expert_response)
        print(f"Grader Bot Feedback: {grader_feedback.content}\n")

        # Optional: Add a condition to break the loop if grading is satisfactory

    print("Multi-agent workflow complete.")

if __name__ == "__main__":
    # Example usage:
    query = "Explain the concept of quantum entanglement in simple terms."
    run_multi_agent_workflow(query)
