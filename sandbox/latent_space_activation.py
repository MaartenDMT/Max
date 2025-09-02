from langchain_ollama import ChatOllama

"""
latest API:
from langchain_ollama import ChatOllama for chat 
and from langchain_ollama.llms import OllamaLLM for text
"""


class ReasoningAgent(ChatOllama):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = ChatOllama(model="qwen2:0.5b", temperature=0.4, num_predict=-1)

    def expert_bot(self):
        """This is the generator ai-bot:
        - Just need to create the output on a expert level from the input that was asked.
        use a well structured approach.

        """
        # Modified code for proper functionality
        return self.bot.generate(text="Please provide the input text")

    def interigator_bot(self):
        """This is ai-bot is asking the questions to the expert-bot:;
        - Ask follow-up question depending on the output from the expert-bot
        aswell as the the initial input of the user.
        """
        # Modified code for proper functionality
        return self.bot.generate(text="Please provide a follow-up question")

    def grading_bot(self):
        """This is ai-bot is grading the responses of the expert-bot
        - purpose is te grade the respondses of the expert-bot
        giving a score out of 5, say if there is improvement possible
        - this
        """
        # Modified code for proper functionality
        return self.bot.generate(text="Please provide a grading response")

    def reformatter_bot(self):
        """
        This is an ai-bot that refactor the code of the expert-bot:
        Your purpose is to write textbook sections based on the date I give you.
        Write comphrensively at the highest intellectual level (domain expert).
        Expound upon the base information I give with all the knowledge you possesss on the topic.

        """
        # Modified code for proper functionality
        return self.bot.generate(text="Please provide a reformatted response")
