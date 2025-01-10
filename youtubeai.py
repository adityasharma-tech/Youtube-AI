import os
import json
from cachetools import TTLCache  # Importing cachetools for caching
import psycopg2  # Importing psycopg2 for PostgreSQL
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Pinecone
from langchain_core.messages import SystemMessage
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Global cache for vectorstores
VECTORSTORE_CACHE = TTLCache(maxsize=100, ttl=1800)  # Max 100 items, 30 minutes TTL

class YoutubeChannelLm:
    def __init__(self, channel_id, api_key, postgres_config, model_name="gemini-1.5-flash"):
        self.api_key = api_key
        self.channel_id = channel_id
        self.postgres_config = postgres_config

        self.system_message = SystemMessage(content=(
            "You are an intelligent assistant for a YouTube channel archive. "
            "Your role is to analyze video transcripts and metadata provided from a specific YouTube channel. "
            "You must answer questions about the channel's videos, their content, titles, and publication dates. "
            "You exist to provide clear, accurate, and context-aware answers based on the video transcripts and metadata."
        ))

        self.qa_system_prompt = """You are an assistant for question-answering tasks only related to the context not too much other than that, you can do some. \
        {context}"""

        # Initialize LangChain components
        self.llm = ChatGoogleGenerativeAI(model=model_name, api_key=self.api_key)
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=self.api_key)

        # Load subtitle documents
        self.documents = self.load_subtitles()
        print("Documents loaded")

        # Load vectorstore with caching and Pinecone
        self.load_vectorstore()
        print("Vectorstore loaded")

        self.retriever = self.vectorstore.as_retriever()
        print("Retriever initialized")

        self.qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        self.store = {}
        self.question_answer_chain = create_stuff_documents_chain(self.llm, self.qa_prompt)
        self.rag_chain = create_retrieval_chain(self.retriever, self.question_answer_chain)
        self.conversational_rag_chain = RunnableWithMessageHistory(
            self.rag_chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]

    def update_status_in_db(self, status):
        try:
            conn = psycopg2.connect(**self.postgres_config)
            cursor = conn.cursor()

            query = """
            INSERT INTO channel_status (channel_id, status, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (channel_id) DO UPDATE
            SET status = EXCLUDED.status, updated_at = EXCLUDED.updated_at;
            """
            cursor.execute(query, (self.channel_id, status))

            conn.commit()
            cursor.close()
            conn.close()
            print(f"Status updated in DB: {status}")
        except Exception as e:
            print(f"Failed to update status in DB: {e}")

    def load_vectorstore(self):
        global VECTORSTORE_CACHE

        # Check cache first
        if self.channel_id in VECTORSTORE_CACHE:
            print(f"Vectorstore loaded from cache for channel_id: {self.channel_id}")
            self.vectorstore = VECTORSTORE_CACHE[self.channel_id]
        else:
            try:
                # Initialize Pinecone vectorstore
                self.vectorstore = Pinecone.from_documents(
                    self.documents,
                    self.embeddings,
                    index_name=self.channel_id  # Assuming Pinecone index is named after the channel ID
                )
                print(f"Vectorstore created in Pinecone for channel_id: {self.channel_id}")

                # Add to cache
                VECTORSTORE_CACHE[self.channel_id] = self.vectorstore

                # Update status in the database
                self.update_status_in_db("Vectorstore created")

            except Exception as e:
                self.update_status_in_db("Vectorstore creation failed")
                print(f"Error creating vectorstore: {e}")

    def load_subtitles(self):
        documents = []
        with open(os.path.join('data', f"{self.channel_id}.videos.json"), 'r', encoding='utf-8') as file:
            videos = json.load(file)
            for video in videos:
                subtitle_path = os.path.join('data', self.channel_id, 'subtitles', f"{video['id']}.subtitles.txt")
                loader = TextLoader(subtitle_path, encoding='utf-8')
                document = loader.load()
                document[0].page_content = (
                    f"Title: {video['title']}\n"
                    f"Published At: {video['publishedAt']}\n"
                    f"Transcript: {document[0].page_content}"
                )
                document[0].metadata = {
                    "video_id": video['id'],
                    "title": video['title'],
                    "publishedAt": video['publishedAt'],
                    "channel_id": self.channel_id
                }
                documents.extend(document)
        return documents

    def query(self, query):
        response = self.conversational_rag_chain.invoke(
            {"input": query},
            config={
                "configurable": {"session_id": "abc123"}
            },
        )
        result = response["answer"]
        return result

    def run(self):
        print("Welcome to the Video Notebook Application!")
        print("Type your query below (type 'exit' to quit):")

        while True:
            user_query = input("\nYour Query: ")
            if user_query.lower() == 'exit':
                break

            response = self.query(user_query)
            print("\nResponse:")
            print(f"\t{response}")
