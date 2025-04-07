import streamlit as st
import os
import json
import time
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")


st.title("SHL Assessment Recommender System")


llm = ChatGroq(groq_api_key=groq_api_key, model_name="Llama3-8b-8192")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


prompt = ChatPromptTemplate.from_template(
    """
    You are an expert in recommending SHL assessments. 
    Answer the question using only the context below (which lists assessments with details).

    <context>
    {context}
    </context>

    Question: {input}
    """
)


def create_vector_embedding():
    if "vectors" not in st.session_state:
        with open("assessments.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        documents = [Document(page_content=json.dumps(item, indent=2)) for item in data]

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_docs = text_splitter.split_documents(documents)

        st.session_state.vectors = FAISS.from_documents(split_docs, embeddings)


user_prompt = st.text_input("Enter your query about SHL assessments")

if st.button("Suggest"):
    create_vector_embedding()
    st.success("Vector database created from assessment.json")


if user_prompt and "vectors" in st.session_state:
    document_chain = create_stuff_documents_chain(llm, prompt)
    retriever = st.session_state.vectors.as_retriever()
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    start = time.process_time()
    response = retrieval_chain.invoke({'input': user_prompt})
    st.write("### Answer:")
    st.write(response['answer'])
    st.caption(f"⏱️ Response time: {time.process_time() - start:.2f} seconds")

    with st.expander("🔍 Matched Documents"):
        for i, doc in enumerate(response.get('context', [])):
            st.write(doc.page_content)
            st.markdown("---")
