# rag_pipeline.py
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

class RAGPipeline:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url="http://localhost:11434"
        )
        self.db = None
        self._init_db()

    def _init_db(self):
        if os.path.exists("faiss_index"):
            self.db = FAISS.load_local("faiss_index", self.embeddings, allow_dangerous_deserialization=True)
        else:
            self.db = FAISS.from_texts(["Initial document"], self.embeddings)
            self.db.save_local("faiss_index")

    def add_paper(self, title: str, content: str, source: str = "Unknown"):
        if not content.strip():
            return
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_text(content)
        docs = [
            Document(page_content=chunk, metadata={"title": title, "source": source})
            for chunk in chunks
        ]
        self.db.add_documents(docs)

    def search(self, query: str, k: int = 4) -> str:
        docs = self.db.similarity_search(query, k=k)
        results = []
        for doc in docs:
            title = doc.metadata.get("title", "Untitled")
            source = doc.metadata.get("source", "N/A")
            results.append(f"📄 **{title}** ({source})\n{doc.page_content}")
        return "\n\n---\n\n".join(results)

    def save(self):
        self.db.save_local("faiss_index")