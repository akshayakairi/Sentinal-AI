"""Retrieval abstractions and security knowledge for RAG reasoning."""

from dataclasses import dataclass
import re
from typing import Protocol


@dataclass(frozen=True)
class KnowledgeDocument:
    """A retrievable, attributable security knowledge record."""

    id: str
    title: str
    content: str
    source_url: str
    tags: tuple[str, ...]


class KnowledgeRetriever(Protocol):
    """Retrieves evidence relevant to an investigation query."""

    def retrieve(self, query: str, limit: int) -> list[KnowledgeDocument]:
        """Return the strongest matching documents for a query."""


MITRE_DOCUMENTS = (
    KnowledgeDocument(
        id="mitre-t1003",
        title="MITRE ATT&CK T1003: OS Credential Dumping",
        content=(
            "Adversaries may attempt to dump credentials from operating systems. "
            "LSASS process memory is a common target. Investigate process ancestry, "
            "command line arguments, module loads, and access to lsass.exe."
        ),
        source_url="https://attack.mitre.org/techniques/T1003/",
        tags=("T1003", "credential", "dumping", "lsass"),
    ),
    KnowledgeDocument(
        id="mitre-t1059-001",
        title="MITRE ATT&CK T1059.001: PowerShell",
        content=(
            "Adversaries may abuse PowerShell for execution. Encoded commands can "
            "obscure intent. Review decoded content, script block logs, parent process, "
            "network connections, persistence changes, and user context."
        ),
        source_url="https://attack.mitre.org/techniques/T1059/001/",
        tags=("T1059.001", "powershell", "encoded", "execution"),
    ),
    KnowledgeDocument(
        id="mitre-t1110",
        title="MITRE ATT&CK T1110: Brute Force",
        content=(
            "Adversaries may use brute force to gain access to accounts. Investigate "
            "failed authentication volume, targeted accounts, source hosts, timing, "
            "and successful logons following failures. Apply rate controls and reset "
            "affected credentials where appropriate."
        ),
        source_url="https://attack.mitre.org/techniques/T1110/",
        tags=("T1110", "brute", "force", "authentication", "logon"),
    ),
)


class InMemoryKnowledgeRetriever:
    """Deterministic lexical retriever suitable for local development and tests."""

    def __init__(self, documents: tuple[KnowledgeDocument, ...] = MITRE_DOCUMENTS) -> None:
        self._documents = documents

    def retrieve(self, query: str, limit: int) -> list[KnowledgeDocument]:
        """Rank documents by overlapping normalized query terms."""
        query_terms = set(_tokenize(query))
        scored_documents = [(self._score(document, query_terms), document) for document in self._documents]
        return [
            document
            for score, document in sorted(scored_documents, key=lambda item: item[0], reverse=True)
            if score > 0
        ][:limit]

    @staticmethod
    def _score(document: KnowledgeDocument, query_terms: set[str]) -> int:
        document_terms = set(_tokenize(" ".join((document.title, document.content, *document.tags))))
        return len(query_terms & document_terms)


def _tokenize(value: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9.]+", value.lower())
