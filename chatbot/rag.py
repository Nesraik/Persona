from http.client import responses
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chromadb import EmbeddingFunction
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from utils.parser import clean_context_text, extract_json_dict
import os
import json
import chromadb
from uuid import uuid4
from sentence_transformers import SentenceTransformer
import torch
from langfuse.openai import OpenAI
from langfuse import Langfuse, observe
from langchain_community.document_loaders import PDFPlumberLoader
from dotenv import load_dotenv
from utils.jinjaProcessor import process_template
load_dotenv()
langfuse = Langfuse()

class MultilingualEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name=os.environ['EMBEDDING_MODEL'], device=None):
        super().__init__()
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = SentenceTransformer(model_name, device=self.device)

    def __call__(self, input):
        if isinstance(input, str):
            input = [input]

        texts = [f"query: {x}" for x in input]

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        return embeddings.tolist()
    
class ContextRetriever:
    def __init__(self, files, session_id, dbpath = "vectordb"):
        self.custom_emb_func = MultilingualEmbeddingFunction()
        self.dbclient = chromadb.PersistentClient(path=dbpath)
        self.client= OpenAI(api_key=os.environ["GEMINI_API_KEY"], base_url=os.environ["GEMINI_BASE_URL"])

        if files:
            self.dbcollection = self._appendDbCollection(files=files, session_id=session_id)
        else:
            self.dbcollection = self._getDbCollection(session_id=session_id)
    
    def _appendDbCollection(self, files, session_id):
        dbcollection = self.dbclient.create_collection(
            name=session_id, embedding_function=self.custom_emb_func
        )

        # initialize text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )

        # load documents and split into chunks
        chuck_text_docs_list = []

        for file in files:
            document_loader = PDFPlumberLoader(file)
            raw_documents = document_loader.load()
            chunk_text_docs = text_splitter.split_documents(raw_documents)
            chuck_text_docs_list.extend(chunk_text_docs)

        for i, doc in enumerate(chuck_text_docs_list):
            dbcollection.add(
                documents=str(doc),
                ids=str(uuid4()),
                metadatas={"chunk": i},
            )

        return dbcollection

    def _getDbCollection(self, session_id):
        return self.dbclient.get_collection(name=session_id, embedding_function=self.custom_emb_func)
    
    @observe(name = "Rewrite Query")
    def _rewriteQuery(self,messages):
        response = self.client.chat.completions.create(
            model = "gemini-2.0-flash",
            messages = messages,
            temperature=0.1,
            top_p=0.1,
            presence_penalty=0.0,
        )
        return response.choices[0].message.content
    
    def _retrieveSubQueryContext(self, subquery):
        results = self.dbcollection.query(
            query_texts=subquery,
            n_results=2,
        )
        chunks = []
        for i, doc in enumerate(results['documents'][0]):
            print(doc)
            chunks.append(f"===Chunk {i}===\n{clean_context_text(doc)}\n")
        print("test")
        return chunks
    
    @observe()
    # Retrieve and Generate (RAG)
    def retrieveContext(self, user_message, chat_history):

        if len(chat_history) != 0:
            chat_history.pop(0)
        
        temp = {
            "user_message": user_message,
            "chat_history": chat_history
        }

        user_prompt = process_template('prompts/query_rewritter_prompt.jinja', temp)

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that rewrites user message into relevant query for RAG."
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        response = self._rewriteQuery(messages)
        response = extract_json_dict(response)
        
        if response['Rewritten query'] == "NONE":
            return "No relevant information found."
        else:
            context_list = []
            with ThreadPoolExecutor(max_workers=5) as executor:  
                futures = [executor.submit(self._retrieveSubQueryContext, sq) for sq in response['Subquery']]
                for future in as_completed(futures):
                    context_list.extend(future.result())
        
        context = "\n".join(doc for doc in context_list)
        return context
    
