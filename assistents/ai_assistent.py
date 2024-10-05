import asyncio

from agents.chatbot_agent import ChatbotAgent
from agents.music_agent import MusicCreationAgent
from agents.research_agent import AIResearchAgent
from agents.video_agent import VideoProcessingAgent
from agents.webpage_agent import WebsiteProcessingAgent
from ai_tools.speech.app_speech import SpeechApp
from agents.writer_agent import AIWriterAgent
from utils.loggers import LoggerSetup


class AIAssistant:
    def __init__(self, tts_model, transcribe, speak, listen):
        self.transcribe = transcribe
        self.tts_model = tts_model
        self.speech_app = SpeechApp(tts_model)

        self._speak = speak
        self._listen = listen

        # Store agent context for session
        self.session_context = {
            "last_command": None,
            "websites_visited": [],
            "youtube_summaries": [],
        }

        # Setup logger
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger("AIAssistant", "ai_assistant.log")

        # llm mode
        self.llm_mode = None

        # Log initialization
        self.logger.info("AI Assistant initialized.")

    def _load_agent(self, agent_type):
        """Load the specific agent when it's first needed."""
        if agent_type == "youtube" and not hasattr(self, "youtube_agent"):
            self.youtube_agent = VideoProcessingAgent(self.transcribe)
            self.logger.info("YouTube agent loaded.")
        elif agent_type == "website" and not hasattr(self, "web_agent"):
            self.web_agent = WebsiteProcessingAgent()
            self.logger.info("Website agent loaded.")
        elif agent_type == "music" and not hasattr(self, "music_agent"):
            self.music_agent = MusicCreationAgent()
            self.logger.info("Music agent loaded.")
        elif agent_type == "research" and not hasattr(self, "research_agent"):
            self.research_agent = AIResearchAgent()
            self.logger.info("AIResearchAgent loaded.")
        elif agent_type == "chatbot" and not hasattr(self, "chatbot_agent"):
            self.chatbot_agent = ChatbotAgent()  # Load ChatbotAgent
            self.logger.info("ChatbotAgent loaded.")
        elif agent_type == "writer assistent" and not hasattr(self, "writer_agent"):
            self.writer_agent = AIWriterAgent()  # Load AIWriterAssistant
            self.logger.info("AIWriterAssistant loaded.")

    async def _determine_task(self, query):
        """Determine which task to execute based on the user's input."""
        try:
            if "youtube" in query:
                self.logger.info("YouTube task detected.")
                self._load_agent("youtube")
                await self._summarize_youtube(query)
            elif "website" in query or "site" in query:
                self.logger.info("Website task detected.")
                self._load_agent("website")
                await self._learn_site(query)
            elif "music loop" in query:
                self.logger.info("Music loop task detected.")
                self._load_agent("music")
                await self._make_loop(query)
            elif "research" in query:
                self.logger.info("Research task detected.")
                self._load_agent("research")
                await self._handle_research(query)
            elif "critique" in query or "reflect" in query or "chatbot" in query:
                self._load_agent("chatbot")
                self.logger.info("Chatbot or AI task detected.")
                await self._handle_chatbot(query)  # Use ChatbotAgent for these tasks
            elif "write" in query or "story" in query or "book" in query:
                self.logger.info("Writing assistent task detected.")
                self._load_agent("writer assistent")  # Load the AIWriterAssistant
                await self._handle_writer_task(query)  # Use AIWriterAssistant
            else:
                self.logger.warning(f"Unknown task for query: {query}")
                await self._unknown_task(query)
        except Exception as e:
            self.logger.error(f"Error determining task: {str(e)}")

    def set_llm_mode(self, mode=None):
        """Set the LLM mode in ChatbotAgent (e.g., critique, reflecting)."""
        self.llm_mode = mode
        if mode in ["critique", "reflecting"]:
            # Ensure chatbot_agent is loaded
            self._load_agent("chatbot")

            # Set ChatbotAgent to the selected mode
            self.chatbot_agent.current_mode = mode
            self.logger.info(f"{mode.capitalize()} mode enabled via ChatbotAgent.")
            return f"{mode.capitalize()} mode enabled."
        else:
            self.llm_mode = None
            self.logger.info("Invalid mode selected, no LLM mode enabled.")
            return "Invalid mode selected."

    async def _handle_writer_task(self, query):
        """Handle writing-related tasks using AIWriterAssistant."""
        try:
            if "create" in query or "story" in query:
                await self.writer_agent.handle_mode_selection()
            else:
                await self._speak(
                    "I can assist with writing tasks. Please specify if you want to create a story or book."
                )
        except Exception as e:
            self.logger.error(f"Error during writing task: {str(e)}")

    async def _handle_chatbot(self, query):
        """Handle chatbot-related tasks."""
        try:
            # Step 1: Ask for the chatbot mode (reflecting or critique)
            mode_response = await self.chatbot_agent.handle_mode_selection()
            await self._speak(mode_response)

            # Step 2: Handle the chatbot query based on the selected mode
            query_response = await self.chatbot_agent.handle_chatbot_query()
            await self._speak(query_response)
        except Exception as e:
            self.logger.error(f"Error during chatbot task: {str(e)}")

    async def _unknown_task(self, query):
        """Handle unrecognized commands."""
        try:
            await self._speak("I'm sorry, I didn't understand that request.")
            self.logger.warning(f"Unknown task encountered for query: {query}")
        except Exception as e:
            self.logger.error(f"Error handling unknown task: {str(e)}")

    async def _summarize_youtube(self, query):
        """Handle YouTube summarization task asynchronously."""
        try:
            await self._speak("Please provide the YouTube video URL.")
            video_url = await asyncio.to_thread(input, "YouTube video URL: ")

            if video_url:
                self.logger.info(f"Received YouTube URL: {video_url}")

                # Check if the URL is valid and summarize the video using VideoProcessingAgent
                full_text, summary = await asyncio.to_thread(
                    self.youtube_agent.handle_user_input, video_url
                )

                if not full_text or not summary:
                    await self._speak(f"An error occurred: {summary}")
                    return

                if self.llm_mode is not None:
                    # Ensure chatbot_agent is loaded before handling LLM tasks
                    self._load_agent("chatbot")

                    # Convert summary to string if it's not already
                    if isinstance(summary, dict):
                        summary = str(summary)

                    # Let ChatbotAgent handle the LLM processing based on mode (e.g., critique, reflecting)
                    critique_result = (
                        await self.chatbot_agent.process_with_current_mode(
                            summary, full_text
                        )
                    )

                    await self._speak("Here is the summary and critique:")
                    print(f"Summary: {summary}")
                    print(f"Critique: {critique_result}")
                    self.logger.info(f"YouTube video summarized")
            else:
                self.logger.warning("No YouTube URL provided.")
                await self._speak("No valid YouTube URL provided.")
        except Exception as e:
            self.logger.error(f"Error during YouTube summarization: {str(e)}")
            await self._speak(f"An error occurred during summarization: {str(e)}")

    async def _learn_site(self, query):
        """Handle website summarization task using the Web agent."""
        try:
            # Step 1: Ask for the URL
            await self._speak("Please provide the website URL.")
            website_url = await asyncio.to_thread(input, "Website URL: ")

            if website_url:
                self.logger.info(f"Received website URL: {website_url}")
                self.session_context["websites_visited"].append(website_url)

                # Step 2: Ask for the question related to the website
                await self._speak("What question do you want to ask about the website?")
                question = await asyncio.to_thread(input, "Question: ")

                if question:
                    self.logger.info(f"Received question for website: {question}")

                    # Use WebPageSummarizer to summarize the website with the provided question
                    result = await asyncio.to_thread(
                        self.web_agent.summarize_website, website_url, question
                    )

                    # Step 3: Provide the summary and handle any errors
                    if result and "summary" in result:
                        await self._speak("Here is the summary:")
                        print(result["summary"])
                        await self._speak("Summary provided.")
                        self.logger.info(f"Website summarized: {result['summary']}")
                    else:
                        await self._speak("Sorry, I couldn't generate a summary.")
                        self.logger.warning("No summary generated for the website.")
                else:
                    await self._speak("No question provided. Please try again.")
                    self.logger.warning("No question provided for the website.")
            else:
                await self._speak("No website URL provided. Please try again.")
                self.logger.warning("No website URL provided.")
        except Exception as e:
            self.logger.error(f"Error during site summarization: {str(e)}")
            await self._speak(
                f"An error occurred while processing the website: {str(e)}"
            )

    async def _research_site(self, query):
        """Handle website research task using the Web agent."""
        try:
            # Step 1: Ask for the research category
            await self._speak("Please provide the research category.")
            category = asyncio.to_thread(input, "Research category: ")

            if category:
                self.logger.info(f"Received research category: {category}")
                await self._speak(f"Setting up research for category: {category}")

                # Use the WebPageResearchAgent to set up research
                result = await asyncio.to_thread(
                    self.web_agent.handle_research_category
                )

                if result:
                    await self._speak(f"Research setup complete: {result}")
                    self.logger.info(f"Research setup complete: {result}")
                else:
                    await self._speak("Sorry, I couldn't set up the research.")
                    self.logger.warning("Research setup failed.")
            else:
                await self._speak("No research category provided.")
                self.logger.warning("No research category provided.")
        except Exception as e:
            self.logger.error(f"Error during site research: {str(e)}")
            await self._speak(
                f"An error occurred while processing the research: {str(e)}"
            )

    async def _make_loop(self, query):
        """Handle music loop generation task using the Music agent."""
        try:
            await self._speak("Making a music loop...")
            prompt = await asyncio.to_thread(
                input, "What kind of music loop do you want: "
            )
            bpm = await asyncio.to_thread(input, "What BPM do you want: ")

            if prompt and bpm:
                self.logger.info(
                    f"Music loop request with prompt: {prompt} and BPM: {bpm}"
                )
                output = await asyncio.to_thread(
                    self.music_agent.create_music_loop, prompt, int(bpm)
                )
                if output:
                    await self._speak(f"Music loop generated: {output}")
                    self.logger.info(f"Music loop generated: {output}")
            else:
                self.logger.warning("Invalid prompt or BPM for music loop.")
        except Exception as e:
            self.logger.error(f"Error during loop making: {str(e)}")

    async def _handle_research(self, query):
        """Handle research-related tasks using the AIResearchAgent."""
        try:
            research_result = await self.research_agent.handle_research(query)
            await self._speak(f"Research result: {research_result}")
        except Exception as e:
            self.logger.error(f"Error during research task: {str(e)}")
            await self._speak(f"An error occurred during research: {str(e)}")

    async def _handle_summarization(self, query):
        """Handle text summarization using the AIResearchAgent."""
        try:
            # Ask the user for the text they want to summarize
            await self._speak("Please provide the text you want to summarize.")
            text_to_summarize = await asyncio.to_thread(input, "Text to summarize: ")

            if text_to_summarize:
                summary_result = await self.research_agent.handle_text_summarization(
                    text_to_summarize
                )
                await self._speak(f"Summarized text: {summary_result}")
            else:
                self.logger.warning("No text provided for summarization.")
                await self._speak("No text provided. Please try again.")
        except Exception as e:
            self.logger.error(f"Error during text summarization: {str(e)}")
            await self._speak(f"An error occurred during summarization: {str(e)}")


# Example usage
if __name__ == "__main__":
    assistant = AIAssistant(tts_model=None, transcribe=None, speak=print, listen=None)
    asyncio.run(assistant._determine_task("website research"))
