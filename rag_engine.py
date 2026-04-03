import os
import pandas as pd
from langchain_groq import ChatGroq
from langchain_community.document_loaders import WebBaseLoader, PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.output_parsers import StructuredOutputParser, ResponseSchema

class AssignmentRAG:
    def __init__(self, groq_api_key):
        self.llm = ChatGroq(
            temperature=0.2, 
            groq_api_key=groq_api_key, 
            model_name="llama-3.3-70b"
        )
        # Using a lightweight embedding model for speed
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    def process_document(self, doc_source):
        """Loads document from URL or Local Path and creates a vector store."""
        if doc_source.startswith("http"):
            loader = WebBaseLoader(doc_source)
        else:
            loader = PyMuPDFLoader(doc_source)
        
        docs = loader.load()
        chunks = self.text_splitter.split_documents(docs)
        vectorstore = FAISS.from_documents(chunks, self.embeddings)
        return vectorstore

    def get_structured_questions(self, vectorstore, topic, assignment_type, num_q=5):
        """Generates questions with hints and examples using RAG."""
        
        # Retrieve context relevant to the specific topic
        docs = vectorstore.similarity_search(topic, k=3)
        context = "\n".join([d.page_content for d in docs])

        # Define the output structure for the LLM
        response_schemas = [
            ResponseSchema(name="question", description="The actual question text"),
            ResponseSchema(name="hint", description="A subtle clue to help the student"),
            ResponseSchema(name="example", description="A similar example or logic application"),
            ResponseSchema(name="explanation", description="The correct logic/answer for grading later")
        ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()

        prompt = f"""
        You are an AI Tutor. Create {num_q} {assignment_type} questions based ONLY on the context below.
        
        Topic: {topic}
        Context: {context}

        For each question, provide:
        1. A helpful hint.
        2. A small example to clarify the concept.
        3. A brief explanation of the correct answer.

        {format_instructions}
        """

        response = self.llm.invoke(prompt)
        try:
            return output_parser.parse(response.content)
        except Exception as e:
            # Fallback in case of parsing errors
            return [{"question": "Error generating question", "hint": str(e), "example": "", "explanation": ""}]

    def update_student_excel(self, student_data, file_path="data/student_db.xlsx"):
        """Appends new submission data to the Student Tracking Excel."""
        if os.path.exists(file_path):
            df = pd.read_excel(file_path)
        else:
            df = pd.DataFrame(columns=[
                "USN", "Name", "Subject", "Topic", "Type", "Status", "Date", "Doc_Link"
            ])
        
        new_row = pd.DataFrame([student_data])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_excel(file_path, index=False)
        return df
