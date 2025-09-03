from latent_space_activation import ReasoningAgent
from langchain_core.messages import HumanMessage, AIMessage

def run_self_correction_loop(initial_query: str, max_refinements: int = 2):
    """
    Runs a self-correction loop where the expert bot refines its answer based on grader feedback.
    """
    agent = ReasoningAgent()
    print(f"Initial Query: {initial_query}\n")

    expert_response = agent.expert_bot(initial_query)
    print(f"Expert Bot Initial Response: {expert_response.content}\n")

    for i in range(max_refinements):
        print(f"--- Refinement Iteration {i + 1} ---")

        # Grader evaluates the current expert response
        grader_feedback = agent.grading_bot(initial_query, expert_response)
        print(f"Grader Bot Feedback: {grader_feedback.content}\n")

        # Expert attempts to refine its response based on the grader's feedback
        refinement_prompt = f"Initial query: {initial_query}\nPrevious response: {expert_response.content}\nGrader feedback: {grader_feedback.content}\nRefine the previous response based on the feedback to improve it."
        expert_response = agent.expert_bot(refinement_prompt)
        print(f"Expert Bot Refined Response: {expert_response.content}\n")

    print("Self-correction loop complete.")

if __name__ == "__main__":
    # Example usage:
    query = "Explain the concept of artificial intelligence, including its history and future prospects."
    run_self_correction_loop(query)
