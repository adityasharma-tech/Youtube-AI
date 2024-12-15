import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_core.messages import HumanMessage, SystemMessage

class NotebookLmApp:
    def __init__(self, channel_id, api_key, model_name="gemini-1.5-flash"):
        self.api_key = api_key
        self.channel_id = channel_id
        
        # Initialize LangChain components
        self.llm = ChatGoogleGenerativeAI(model=model_name, api_key=self.api_key)

        self.system_message = SystemMessage(content=(
            "You are an intelligent assistant for a YouTube channel archive. "
            "Your role is to analyze video transcripts and metadata provided from a specific YouTube channel. "
            "You must answer questions about the channel's videos, their content, titles, and publication dates. "
            "You exist to provide clear, accurate, and context-aware answers based on the video transcripts and metadata."
        ))

        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=self.api_key)

        # Load and process subtitle documents
        self.documents = self.load_subtitles()
        print("documents loaded")

        self.vectorstore = FAISS.from_documents(self.documents, self.embeddings)
        print("vectorstore loaded")

        self.retriever = self.vectorstore.as_retriever()
        print("retriever loaded")

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever = self.retriever,
            chain_type="stuff",
            return_source_documents=True,
            system_message=self.system_message
        )




    def load_subtitles(self):
        documents = []
        with open(os.path.join('data', f"{self.channel_id}.videos.json"), 'r', encoding='utf-8') as file:
            videos = json.load(file)
            for video in videos:
                subtitle_path = os.path.join('data', self.channel_id, 'subtitles', f"{video['id']}.subtitles.txt")

                loader = TextLoader(subtitle_path, encoding='utf-8')
                document = loader.load()
                document[0].metadata = {
                    "video_id": video['id'],
                    "title": video['title'],
                    "publishedAt": video['publishedAt']
                }

                documents.extend(document)
                
        return documents
    
    def query(self, query):
        response = self.qa_chain.invoke([
            HumanMessage(content=query)
        ])
        result = response["result"]
        sources = response["source_documents"]

        # Optionally, you can format the output to include sources
        print("\nSources:")
        for source in sources:
            print(f"\tVideo ID: {source.metadata['video_id']}")
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

            
if __name__ == "__main__":
    API_KEY = "AIzaSyADIgPArEEIgcvfpEBz4GkgxG6xLSz5YO4"

    app = NotebookLmApp("UCwpr_shE_KEjoOVFqbwaGYQ", API_KEY)
    app.run()