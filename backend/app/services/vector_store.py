"""Chroma-based vector retrieval adapter."""

from app.services.knowledge_base import KnowledgeDocument


class ChromaKnowledgeRetriever:
    """Persist curated security knowledge in Chroma using Sentence Transformers."""

    def __init__(
        self,
        documents: tuple[KnowledgeDocument, ...],
        persist_directory: str,
        embedding_model_name: str,
    ) -> None:
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise RuntimeError(
                "Chroma retrieval requires chromadb and sentence-transformers dependencies."
            ) from error

        self._embedder = SentenceTransformer(embedding_model_name)
        client = chromadb.PersistentClient(path=persist_directory)
        self._collection = client.get_or_create_collection(name="security_knowledge")
        self._documents = {document.id: document for document in documents}
        self._collection.upsert(
            ids=[document.id for document in documents],
            documents=[document.content for document in documents],
            metadatas=[
                {
                    "title": document.title,
                    "source_url": document.source_url,
                    "tags": ",".join(document.tags),
                }
                for document in documents
            ],
            embeddings=self._embed([self._document_text(document) for document in documents]),
        )

    def retrieve(self, query: str, limit: int) -> list[KnowledgeDocument]:
        """Return vector-similar knowledge records for the query."""
        result = self._collection.query(
            query_embeddings=self._embed([query]),
            n_results=min(limit, len(self._documents)),
        )
        ids = result.get("ids", [[]])[0]
        return [self._documents[document_id] for document_id in ids if document_id in self._documents]

    def _embed(self, texts: list[str]) -> list[list[float]]:
        return self._embedder.encode(texts, normalize_embeddings=True).tolist()

    @staticmethod
    def _document_text(document: KnowledgeDocument) -> str:
        return " ".join((document.title, document.content, *document.tags))
