import asyncio  # Import asyncio for to_thread
import os
import tempfile
from operator import itemgetter

import httpx
import spacy
import validators
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sklearn.feature_extraction.text import TfidfVectorizer

from utils.loggers import LoggerSetup


class WebPageSummarizer:
    def __init__(self, max_retries=3, retry_delay=2):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.nlp = spacy.load(
            "en_core_web_sm"
        )  # Load a small English model for keyword extraction

        # Setup logger
        log_setup = LoggerSetup()
        self.logger = log_setup.get_logger(
            "WebPageSummarizer", "web_page_summarizer.log"
        )
        self.logger.info("WebPageSummarizer initialized.")

        # Lazy initialization for OllamaEmbeddings and Ollama LLM
        self._embedding_model = None
        self._llm_model = None

    @property
    def embedding_model(self):
        if self._embedding_model is None:
            self.logger.info("Lazy loading OllamaEmbeddings model.")
            self._embedding_model = OllamaEmbeddings(model="nomic-embed-text")
        return self._embedding_model

    @property
    def llm_model(self):
        if self._llm_model is None:
            self.logger.info("Lazy loading Ollama LLM model.")
            # Use ChatOllama from langchain-ollama (recommended in LangChain 0.3+)
            self._llm_model = ChatOllama(
                model="gemma2:2b",
                temperature=0.4,
            )
        return self._llm_model

    async def validate_url(self, url):
        """Validates the given URL asynchronously."""
        if not validators.url(url):
            raise ValueError(f"Invalid URL: {url}")

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=5) as client:
                response = await client.head(url)
            if response.status_code >= 400:
                raise ValueError(
                    f"URL is not accessible, status code: {response.status_code}"
                )
        except httpx.HTTPError as e:
            raise ValueError(f"Error accessing URL: {e}")

    def validate_question(self, question):
        """Validates the input question."""
        if not question or not isinstance(question, str) or not question.strip():
            raise ValueError("Question must be a non-empty string.")

    async def retry_on_failure(self, func, *args, **kwargs):
        """Retry mechanism with exponential backoff for network-related functions asynchronously."""
        attempts = 0
        while attempts < self.max_retries:
            try:
                return await func(*args, **kwargs)
            except (httpx.HTTPError, TimeoutError) as e:
                attempts += 1
                self.logger.warning(
                    f"Attempt {attempts} failed: {e}. Retrying in {self.retry_delay ** attempts} seconds..."
                )
                await asyncio.sleep(self.retry_delay ** attempts)
        self.logger.error(
            f"Failed after {self.max_retries} attempts to call {func.__name__}."
        )
        raise Exception(f"Failed after {self.max_retries} attempts")

    async def get_documents(self, url):
        """Load and split documents from a URL with retry mechanism asynchronously."""
        content_type = await self._determine_content_type(url)

        if content_type == "html":
            docs = await self.retry_on_failure(self._load_html, url)
        elif content_type == "pdf":
            docs = await self.retry_on_failure(self._load_pdf, url)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=20,
        )
        split_docs = splitter.split_documents(docs)

        return split_docs

    async def _determine_content_type(self, url):
        """Determine the content type of the URL asynchronously."""
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=5) as client:
                response = await client.head(url)
            content_type = response.headers.get("content-type", "")
            if "text/html" in content_type:
                return "html"
            elif "application/pdf" in content_type:
                return "pdf"
            else:
                return None
        except httpx.HTTPError as e:
            raise ValueError(f"Failed to determine content type: {e}")

    async def _load_html(self, url):
        """Load HTML content, filter it, and convert it to a document asynchronously."""
        try:
            docs = await asyncio.to_thread(WebBaseLoader(url).load)
            self.logger.info("Loading HTML from %s", url)
            return docs
        except Exception as e:
            self.logger.error(f"Failed to load HTML from {url}: {e}")
            return []  # Return empty list on failure to avoid NoneType errors

    async def _load_pdf(self, url):
        """Load and process a PDF document from the URL asynchronously."""
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

        self.logger.info("Loading PDF from %s", url)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(response.content)
            pdf_loader = PyPDFLoader(temp_pdf.name)
            docs = await asyncio.to_thread(pdf_loader.load)

        os.remove(temp_pdf.name)
        return docs

    async def create_db(self, docs):
        """Create a vector store database from documents asynchronously."""
        self.logger.info("Creating the vector database.")
        vector_store = await asyncio.to_thread(
            Chroma.from_documents, docs, embedding=self.embedding_model
        )
        return vector_store

    def create_chain(self, vector_store, summary_length="detailed"):
        """
        Create an LCEL retrieval-augmented generation chain.

        This replaces legacy create_stuff_documents_chain/create_history_aware_retriever
        with a pure LCEL composition:
          {"context": (rewrite_query -> retriever -> format_docs),
           "input": passthrough,
           "chat_history": passthrough}
          | answer_prompt | llm | StrOutputParser
        """
        self.logger.info("Creating an LCEL retrieval chain.")

        # Answering prompt (stuff-style over {context})
        if summary_length == "brief":
            prompt_text = "Provide a brief summary based on the context: {context}"
        else:
            prompt_text = "Provide a detailed summary based on the context: {context}"

        answer_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompt_text),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )

        # History-aware query rewrite prompt
        retriever_prompt = ChatPromptTemplate.from_messages(
            [
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                (
                    "human",
                    "Given the above conversation, generate a concise search query to retrieve information relevant to the conversation.",
                ),
            ]
        )

        retriever = vector_store.as_retriever(search_kwargs={"k": 3})

        # LCEL subchain: (input, history) -> query string
        rewrite_chain = {
            "input": itemgetter("input"),
            "chat_history": itemgetter("chat_history"),
        } | retriever_prompt | self.llm_model | StrOutputParser()

        # From query -> Documents
        docs_chain = rewrite_chain | retriever

        # Format documents into a single string for the answer prompt
        format_docs = RunnableLambda(
            lambda docs: "\n\n".join(getattr(d, "page_content", str(d)) for d in (docs or []))
        )

        # Final LCEL chain: build context, then answer
        chain = {
            "context": docs_chain | format_docs,
            "input": itemgetter("input"),
            "chat_history": itemgetter("chat_history"),
        } | answer_prompt | self.llm_model | StrOutputParser()

        return chain

    async def process_chat(self, chain, question, chat_history):
        """Process the chat by invoking the LCEL chain asynchronously (returns a string)."""
        self.logger.info("Processing chat with the retrieval chain.")
        response = await asyncio.to_thread(
            chain.invoke, {"input": question, "chat_history": chat_history}
        )
        # StrOutputParser returns a plain string
        return response

    async def extract_keywords(self, text, num_keywords=5):
        """Extract keywords from the summarized text asynchronously."""
        self.logger.info("Extracting keywords from the summarized text.")
        doc = await asyncio.to_thread(self.nlp, text)
        tokens = [token.text for token in doc if token.is_alpha and not token.is_stop]
        vectorizer = TfidfVectorizer(max_features=num_keywords)
        await asyncio.to_thread(vectorizer.fit_transform, [" ".join(tokens)])
        return list(vectorizer.get_feature_names_out())

    async def summarize_website(self, url, question, summary_length="detailed"):
        """Main method to summarize a website with advanced features asynchronously."""
        await self.validate_url(url)
        self.validate_question(question)

        docs = await self.get_documents(url)
        vector_store = await self.create_db(docs)
        chain = self.create_chain(vector_store, summary_length=summary_length)
        chat_history = []
        response = await self.process_chat(chain, question, chat_history)
        keywords = await self.extract_keywords(response)

        return {"summary": response, "keywords": keywords}
