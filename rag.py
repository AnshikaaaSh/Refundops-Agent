"""
RAG (Retrieval-Augmented Generation) module for policy document retrieval.

Loads policy markdown documents from data/policy_docs/, splits them into chunks,
embeds them using Claude's embeddings via LangChain, stores in ChromaDB vector store,
and exposes a retriever function for policy search.
"""

import os
from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

POLICY_DOCS_DIR = "data/policy_docs"
PERSIST_DIR = "data/chroma_store"

_vectorstore = None


def _build_vectorstore():
    """Loads policy docs, splits them into chunks, embeds, and stores in Chroma."""
    # Create directory if it doesn't exist
    Path(POLICY_DOCS_DIR).mkdir(parents=True, exist_ok=True)
    
    loader = DirectoryLoader(POLICY_DOCS_DIR, glob="*.md", loader_cls=TextLoader)
    docs = loader.load()
    
    if not docs:
        print(f"Warning: No policy documents found in {POLICY_DOCS_DIR}")
        return None

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    # Use HuggingFace embeddings (free, no API key required)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIR,
    )
    return vectorstore


def get_vectorstore():
    """Get or build the vectorstore for policy documents."""
    global _vectorstore
    if _vectorstore is None:
        # Always rebuild to ensure fresh data (for development)
        # In production, you'd load from persist_directory if it exists
        if os.path.exists(PERSIST_DIR):
            # Try loading from disk if it exists
            try:
                embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                _vectorstore = Chroma(
                    persist_directory=PERSIST_DIR, 
                    embedding_function=embeddings
                )
            except Exception as e:
                print(f"Failed to load from persist_dir: {e}. Rebuilding...")
                _vectorstore = _build_vectorstore()
        else:
            _vectorstore = _build_vectorstore()
    return _vectorstore


def retrieve_policy(query: str, k: int = 3) -> str:
    """
    Retrieve relevant policy clauses for a given dispute query.
    
    Args:
        query: The dispute type or policy question (e.g., "duplicate charge", "fraud")
        k: Number of top results to return
    
    Returns:
        Formatted policy context with citations or a message if nothing found
    """
    vectorstore = get_vectorstore()
    
    if vectorstore is None:
        return "Policy database not available. Please run setup_data.py first."
    
    results = vectorstore.similarity_search(query, k=k)

    context_parts = []
    seen_sources = set()
    
    for doc in results:
        source = os.path.basename(doc.metadata.get("source", "unknown"))
        # Avoid duplicate sources in output
        if source not in seen_sources:
            context_parts.append(f"[Policy: {source}]\n{doc.page_content}")
            seen_sources.add(source)

    if context_parts:
        return "\n\n---\n\n".join(context_parts)
    else:
        return f"No relevant policy information found for: {query}"
