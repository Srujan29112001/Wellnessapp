#!/usr/bin/env python3
"""
Initialize Vector Store with Knowledge Base

This script loads all knowledge base documents (supplements, Ayurveda, etc.)
and indexes them in the vector store for RAG (Retrieval Augmented Generation).
"""

import os
import json
import sys
from pathlib import Path
from typing import List, Dict

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


def load_supplement_knowledge(kb_path: Path) -> List[Document]:
    """Load supplement database into documents"""
    supplements_file = kb_path / "supplements" / "supplements_db.json"

    if not supplements_file.exists():
        print(f"Warning: {supplements_file} not found")
        return []

    with open(supplements_file, 'r') as f:
        data = json.load(f)

    documents = []
    supplements = data.get("supplements", [])

    for supp in supplements:
        # Create main document for supplement
        content = f"""
{supp['name']} ({supp['category']})

Description: {supp['description']}

Benefits:
{chr(10).join(f"- {b}" for b in supp['benefits'])}

Mechanism of Action: {supp['mechanism_of_action']}

Dosage:
- Typical: {supp['dosage']['typical']}
- Range: {supp['dosage']['range']}
- Timing: {supp['dosage']['timing']}
- Forms: {', '.join(supp['dosage']['forms'])}

Contraindications:
{chr(10).join(f"- {c}" for c in supp['contraindications'])}

Drug Interactions:
{chr(10).join(f"- {i}" for i in supp['drug_interactions'])}

Side Effects:
{chr(10).join(f"- {s}" for s in supp['side_effects'])}

Scientific Evidence:
{chr(10).join(f"- {e['title']} (PMID: {e['pubmed_id']})" for e in supp.get('scientific_evidence', []))}

Ayurvedic Properties:
- Rasa (Taste): {', '.join(supp['ayurvedic']['rasa'])}
- Virya (Energy): {supp['ayurvedic']['virya']}
- Effect on Doshas: {supp['ayurvedic']['dosha_effect']}
"""

        documents.append(Document(
            page_content=content,
            metadata={
                "source": "supplements",
                "name": supp['name'],
                "category": supp['category'],
                "type": "supplement_info"
            }
        ))

    # Add supplement stacks
    stacks = data.get("supplement_stacks", [])
    for stack in stacks:
        content = f"""
Supplement Stack: {stack['name']}

Purpose: {stack['purpose']}

Supplements:
{chr(10).join(f"- {s['supplement']}: {s['dosage']} ({s['timing']})" for s in stack['supplements'])}

Expected Benefits:
{chr(10).join(f"- {b}" for b in stack['expected_benefits'])}

Precautions:
{chr(10).join(f"- {p}" for p in stack['precautions'])}
"""

        documents.append(Document(
            page_content=content,
            metadata={
                "source": "supplements",
                "type": "supplement_stack",
                "stack_name": stack['name'],
                "purpose": stack['purpose']
            }
        ))

    print(f"Loaded {len(documents)} supplement documents")
    return documents


def load_ayurveda_knowledge(kb_path: Path) -> List[Document]:
    """Load Ayurveda knowledge into documents"""
    ayurveda_file = kb_path / "ayurveda" / "doshas.json"

    if not ayurveda_file.exists():
        print(f"Warning: {ayurveda_file} not found")
        return []

    with open(ayurveda_file, 'r') as f:
        data = json.load(f)

    documents = []
    doshas = data.get("doshas", [])

    for dosha in doshas:
        # Create main dosha document
        content = f"""
Ayurvedic Dosha: {dosha['name']} ({dosha['primary_element']}, {dosha['secondary_element']})

Description: {dosha['description']}

Physical Characteristics:
{chr(10).join(f"- {c}" for c in dosha['physical_characteristics'])}

Mental Characteristics:
{chr(10).join(f"- {c}" for c in dosha['mental_characteristics'])}

When Balanced:
{chr(10).join(f"- {c}" for c in dosha['when_balanced'])}

Signs of Imbalance:
{chr(10).join(f"- {s}" for s in dosha['imbalance_signs'])}

Balancing Foods (Favor):
{chr(10).join(f"- {f}" for f in dosha['balancing_foods']['favor'])}

Balancing Foods (Avoid):
{chr(10).join(f"- {f}" for f in dosha['balancing_foods']['avoid'])}

Recommended Herbs:
{chr(10).join(f"- {h['name']}: {h['properties']}" for h in dosha['recommended_herbs'])}

Lifestyle Recommendations:
{chr(10).join(f"- {r}" for r in dosha['lifestyle_recommendations'])}
"""

        documents.append(Document(
            page_content=content,
            metadata={
                "source": "ayurveda",
                "dosha": dosha['name'],
                "type": "dosha_profile"
            }
        ))

    print(f"Loaded {len(documents)} Ayurveda documents")
    return documents


def initialize_vector_store():
    """Initialize the vector store with all knowledge base documents"""

    print("=" * 60)
    print("Initializing Vector Store with Knowledge Base")
    print("=" * 60)

    # Paths
    kb_path = PROJECT_ROOT / "knowledge_base"
    vector_store_path = PROJECT_ROOT / "data" / "vector_store"

    if not kb_path.exists():
        print(f"Error: Knowledge base path not found: {kb_path}")
        return False

    # Create vector store directory
    vector_store_path.mkdir(parents=True, exist_ok=True)

    # Load all knowledge documents
    print("\n1. Loading knowledge documents...")
    all_documents = []

    all_documents.extend(load_supplement_knowledge(kb_path))
    all_documents.extend(load_ayurveda_knowledge(kb_path))

    if not all_documents:
        print("Error: No documents loaded!")
        return False

    print(f"\nTotal documents loaded: {len(all_documents)}")

    # Split documents into smaller chunks
    print("\n2. Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )

    split_docs = text_splitter.split_documents(all_documents)
    print(f"Created {len(split_docs)} document chunks")

    # Initialize embeddings
    print("\n3. Initializing embeddings model...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    print("Embeddings model loaded")

    # Create vector store
    print("\n4. Creating vector store...")
    print("This may take a few minutes...")

    vector_store = Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings,
        persist_directory=str(vector_store_path)
    )

    # Persist to disk
    print("\n5. Persisting vector store to disk...")
    vector_store.persist()

    print("\n" + "=" * 60)
    print("✓ Vector store initialized successfully!")
    print(f"  Location: {vector_store_path}")
    print(f"  Documents: {len(all_documents)}")
    print(f"  Chunks: {len(split_docs)}")
    print("=" * 60)

    # Test retrieval
    print("\n6. Testing vector store retrieval...")
    test_query = "What supplements help with stress?"
    results = vector_store.similarity_search(test_query, k=3)

    print(f"\nTest Query: '{test_query}'")
    print(f"Retrieved {len(results)} results:")
    for i, doc in enumerate(results, 1):
        print(f"\n  Result {i}:")
        print(f"  Source: {doc.metadata.get('source', 'unknown')}")
        print(f"  Type: {doc.metadata.get('type', 'unknown')}")
        print(f"  Preview: {doc.page_content[:200]}...")

    return True


if __name__ == "__main__":
    success = initialize_vector_store()
    sys.exit(0 if success else 1)
