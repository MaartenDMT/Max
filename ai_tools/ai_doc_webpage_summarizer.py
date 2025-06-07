import os
import tempfile
import time
import logging
import asyncio  # Import asyncio for to_thread

import requests
import spacy
import validators
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    PyPDFLoader,
    WebBaseLoader,
)
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms.ollama import Ollama
from langchain_community.vectorstores import Chroma
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

    async def validate_url(self, url):
        """Validates the given URL asynchronously."""
        if not validators.url(url):
            raise ValueError(f"Invalid URL: {url}")

        try:
            response = await asyncio.to_thread(
                requests.head, url, allow_redirects=True, timeout=5
            )
            if response.status_code >= 400:
                raise ValueError(
                    f"URL is not accessible, status code: {response.status_code}"
                )
        except requests.RequestException as e:
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
            except requests.RequestException as e:
                attempts += 1
                self.logger.warning(
                    f"Attempt {attempts} failed: {e}. Retrying in {self.retry_delay ** attempts} seconds..."
                )
                await asyncio.sleep(self.retry_delay**attempts)
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
            response = await asyncio.to_thread(
                requests.head, url, allow_redirects=True, timeout=5
            )
            content_type = response.headers.get("Content-Type", "")
            if "text/html" in content_type:
                return "html"
            elif "application/pdf" in content_type:
                return "pdf"
            else:
                return None
        except requests.RequestException as e:
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
        response = await asyncio.to_thread(requests.get, url)
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
        embedding = OllamaEmbeddings(model="nomic-embed-text")
        vector_store = await asyncio.to_thread(
            Chroma.from_documents, docs, embedding=embedding
        )
        return vector_store

    def create_chain(self, vector_store, summary_length="detailed"):
        """Create a retrieval chain for processing questions with summary length control."""
        model = Ollama(
            model="gemma2:2b",
            temperature=0.4,
        )
        self.logger.info("Creating a retrieval chain.")
        if summary_length == "brief":
            prompt_text = "Provide a brief summary based on the context: {context}"
        else:
            prompt_text = "Provide a detailed summary based on the context: {context}"

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompt_text),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )

        chain = create_stuff_documents_chain(llm=model, prompt=prompt)

        retriever = vector_store.as_retriever(search_kwargs={"k": 3})

        retriever_prompt = ChatPromptTemplate.from_messages(
            [
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                (
                    "human",
                    "Given the above conversation, generate a search query to look up in order to get information relevant to the conversation",
                ),
            ]
        )

        history_aware_retriever = create_history_aware_retriever(
            llm=model, retriever=retriever, prompt=retriever_prompt
        )

        retrieval_chain = create_retrieval_chain(history_aware_retriever, chain)

        return retrieval_chain

    async def process_chat(self, chain, question, chat_history):
        """Process the chat by invoking the chain asynchronously."""
        self.logger.info("Processing chat with the retrieval chain.")
        response = await asyncio.to_thread(
            chain.invoke, {"input": question, "chat_history": chat_history}
        )
        return response["answer"]

    async def extract_keywords(self, text, num_keywords=5):
        """Extract keywords from the summarized text asynchronously."""
        self.logger.info("Extracting keywords from the summarized text.")
        doc = await asyncio.to_thread(self.nlp, text)
        keywords = [token.text for token in doc if token.is_alpha and not token.is_stop]
        vectorizer = TfidfVectorizer(max_features=num_keywords)
        X = await asyncio.to_thread(vectorizer.fit_transform, [" ".join(keywords)])
        keywords = vectorizer.get_feature_names_out()
        return keywords

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
