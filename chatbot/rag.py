from langchain.text_splitter import RecursiveCharacterTextSplitter
from chromadb import EmbeddingFunction
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import os
import json
import chromadb
from uuid import uuid4
from langfuse.decorators import observe
from sentence_transformers import SentenceTransformer
import torch
from langfuse.openai import OpenAI
from langfuse import Langfuse
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
    def __init__(self, dbpath):
        self.custom_emb_func = MultilingualEmbeddingFunction()
        self.dbclient = chromadb.PersistentClient(path=dbpath)
        self.client_gemini = OpenAI(api_key=os.environ["GEMINI_API_KEY"], base_url=os.environ["GEMINI_BASE_URL"])
    
    def _createDbCollection(self, files):
        dbcollection = self.dbclient.create_collection(
            name="USERINPUT", embedding_function=self.custom_emb_func
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
                metadatas={"source": self.filename, "chunk": i},
            )

        return dbcollection

    def _getDbCollection(self):
        return self.dbclient.get_collection(name="USERINPUT", embedding_function=self.custom_emb_func)
    
    @observe(name="gemini_infer")
    def _infer_gemini(self,messages):
        response = self.client_gemini.chat.completions.create(
            model="gemini-2.0-flash",
            messages=messages,
            temperature=0.1,
            top_p=0.1
        )
        return response.choices[0].message.content.strip()
    
    @observe(name="split_user_query")
    def _split_user_query(self,user_query, chat_history):

        temp = {
            "user_input": user_query,
            "chat_history": chat_history
        }

        user_prompt = process_template("prompt/split_user_query_prompt.jinja", temp)

        messages = [
            {"role": "user", "content": user_prompt}
        ]

        response = self._infer_gemini(messages)

        sub_queries = json.loads(response)

        return sub_queries
    
    @observe(name="retrieve_contexts")
    def retrieve_contexts(self, conversation_log, files, top_k=3):
        user_query = conversation_log[-1]['content']
        chat_history = [msg['content'] for msg in conversation_log[:-1] if msg['role'] != 'system']

        sub_queries = self._split_user_query(user_query, chat_history)

        if len(sub_queries) == 0:
            return "No relevant information found."
        else:
            context_list = []            
            for subquery in sub_queries:
                results = self.dbcollection.query(
                    query_texts=subquery,
                    n_results=top_k,
                )
                for doc in results['documents'][0]:
                    context_list.append(doc)

        context = "\n".join(doc for doc in context_list)

        return context
    