import asyncio

from ai_tools.ai_doc_webpage_summarizer import (
    WebPageSummarizer,
)  # Import the WebPageSummarizer
from ai_tools.ai_webpage_research_agent import (
    AIWebPageResearchAgent,
)  # Import the AIWebPageResearchAgent


class WebsiteProcessingAgent:
    def __init__(self):
        """
        Initialize the agent with a WebPageSummarizer tool and AIWebPageResearchAgent.
        """
        self.summarizer = WebPageSummarizer()
        self.research_agent = AIWebPageResearchAgent()  # Initialize the research agent
        self.current_url = None  # Store the current URL for the session

    async def handle_url_input(self):
        """
        Handle the user's URL input and store it for the session.
        """
        try:
            await self._speak("Please provide the website URL.")
            website_url = await asyncio.get_event_loop().run_in_executor(
                None, input, "Website URL: "
            )

            if website_url:
                self.current_url = website_url
                return f"URL received: {website_url}"
            else:
                return "No valid URL provided."
        except Exception as e:
            return f"Error processing URL: {str(e)}"

    async def handle_question_input(self):
        """
        Handle the user's question input after the URL is provided.
        """
        if not self.current_url:
            return "Please provide a valid URL first."

        try:
            await self._speak("What question do you want to ask about the website?")
            question = await asyncio.get_event_loop().run_in_executor(
                None, input, "Question: "
            )

            if question:
                # Proceed to summarize the web page with the question
                return await self.summarize_website(self.current_url, question)
            else:
                return "No question provided."
        except Exception as e:
            return f"Error processing question: {str(e)}"

    async def summarize_website(self, url, question):
        """
        Summarize the web page using the provided URL and question.
        """
        try:
            # Delegate the summarization task to the WebPageSummarizer tool
            result = self.summarizer.summarize_website(
                url, question, summary_length="detailed"
            )
            summary = result["summary"]
            keywords = result["keywords"]
            return f"Summary: {summary}\nKeywords: {', '.join(keywords)}"
        except Exception as e:
            return f"Error summarizing website: {str(e)}"

    async def handle_research_category(self):
        """
        Handle research input using the AIWebPageResearchAgent's research capabilities.
        """
        try:
            # Ask the user for the research category (e.g., "book_research_urls")
            await self._speak("Please provide the research category.")
            category = await asyncio.get_event_loop().run_in_executor(
                None, input, "Research category: "
            )

            if category:
                # Set up the research process for the specified category
                self.research_agent.setup_research(category)
                await self._speak(f"Research setup for category: {category}")
                return f"Research setup for category: {category}"
            else:
                return "No research category provided."
        except Exception as e:
            return f"Error handling research category: {str(e)}"

    async def handle_research_question(self):
        """
        Handle a research question using the AIWebPageResearchAgent.
        """
        try:
            # Ask the user for the research question
            await self._speak("Please provide your research question.")
            question = await asyncio.get_event_loop().run_in_executor(
                None, input, "Research question: "
            )

            if question:
                # Process the research question using AIWebPageResearchAgent
                response = self.research_agent.process_chat(question)
                await self._speak(f"Research result: {response}")
                return f"Research result: {response}"
            else:
                return "No research question provided."
        except Exception as e:
            return f"Error processing research question: {str(e)}"

    async def _speak(self, message):
        """Placeholder method for speaking or printing messages."""
        print(message)


# Example usage in an asyncio loop
async def run_agent():
    agent = WebsiteProcessingAgent()

    # First, handle URL input
    url_response = await agent.handle_url_input()
    print(url_response)

    # Then, handle the question input
    question_response = await agent.handle_question_input()
    print(question_response)

    # Handle research category input
    research_category_response = await agent.handle_research_category()
    print(research_category_response)

    # Handle research question input
    research_question_response = await agent.handle_research_question()
    print(research_question_response)


if __name__ == "__main__":
    asyncio.run(run_agent())
