from latent_space_activation import ReasoningAgent

def explore_latent_space(initial_query: str, control_strings: list):
    """
    Explores the effect of different latent space control strings on the expert bot's output.
    """
    print(f"Exploring Latent Space for Query: {initial_query}\n")

    for control in control_strings:
        print(f"--- Latent Space Control: '{control}' ---")
        agent = ReasoningAgent(latent_space_control=control)
        expert_response = agent.expert_bot(initial_query)
        print(f"Expert Bot Response: {expert_response.content}\n")

    print("Latent space exploration complete.")

if __name__ == "__main__":
    # Example usage:
    query = "Describe the process of photosynthesis."
    controls = [
        "be highly creative and imaginative",
        "be strictly factual and scientific",
        "be concise and to the point",
        "explain like I am a 5-year-old",
        "write in a poetic style"
    ]
    explore_latent_space(query, controls)
