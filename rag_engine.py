import os
from langchain_groq import ChatGroq
from langchain_community.document_loaders import WebBaseLoader, PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

class AssignmentRAG:
    def __init__(self, api_key):
        self.llm = ChatGroq(api_key=api_key, model_name="llama-3.3-70b", temperature=0.3)
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    def process_doc(self, path):
        loader = WebBaseLoader(path) if path.startswith("http") else PyMuPDFLoader(path)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = splitter.split_documents(docs)
        return FAISS.from_documents(chunks, self.embeddings)

    def get_questions(self, vectorstore, topic, a_type):
        context = "\n".join([d.page_content for d in vectorstore.similarity_search(topic, k=3)])
        
        schemas = [
            ResponseSchema(name="question", description="The question"),
            ResponseSchema(name="hint", description="A subtle hint"),
            ResponseSchema(name="example", description="A practical example")
        ]
        parser = StructuredOutputParser.from_response_schemas(schemas)
        
        prompt = f"Context: {context}\nTopic: {topic}\nType: {a_type}\n{parser.get_format_instructions()}"
        res = self.llm.invoke(prompt)
        return parser.parse(res.content)
