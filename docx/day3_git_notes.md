# Day 3 Ultra-Short Notes

## LangChain

**Framework for building LLM applications**

* Models → AI brain
* Prompt Templates → Dynamic prompts
* Chains → Connect multiple steps
* Output Parsers → Structured output
* LCEL → `prompt | model | parser`

---

## Embeddings

**Text → Numbers (Vectors)**

* Capture semantic meaning
* Similar meaning = Similar vectors
* Used for semantic search
* Foundation of RAG

Example:

* Dog ≈ Puppy
* Leave ≈ Vacation

---

## Cosine Similarity

**Measures similarity between vectors**

* 1 → Very similar
* 0 → Unrelated
* Higher score = More similar

---

## Vector Database

**Stores embeddings and performs similarity search**

Examples:

* FAISS
* Chroma
* Pinecone

Purpose:

* Fast retrieval of relevant information

---

## Chunking

**Large document → Small chunks**

Why?

* LLM can't process huge documents efficiently
* Better retrieval accuracy

### Chunk Overlap

Repeats some text between chunks to preserve context.

---

## Retriever

**Finds relevant chunks for a query**

```text
Question
↓
Retriever
↓
Relevant Chunks
```

---

## Top-K Retrieval

**Retrieve K most relevant chunks**

Example:

```text
K = 5
```

Return top 5 chunks.

---

## Re-ranking

**Improves retrieved results**

Retriever:

```text
A B C D E
```

Reranker:

```text
C A B D E
```

Most relevant chunks moved to top.

**Retriever = Find candidates**
**Reranker = Pick best candidates**

---

## RAG

**Retrieval Augmented Generation**

Instead of:

```text
Question
↓
LLM
↓
Guess
```

Use:

```text
Question
↓
Retriever
↓
Context
↓
LLM
↓
Answer
```

Benefits:

* Uses private documents
* Reduces hallucinations
* No retraining needed

---

## Complete Flow

```text
Documents
↓
Chunking
↓
Embeddings
↓
Vector DB
↓
Retriever
↓
Top-K Chunks
↓
Reranking
↓
LLM
↓
Answer
```

### One-Line Summary

**LangChain builds the pipeline, Embeddings understand meaning, Vector DB stores vectors, Retriever finds relevant chunks, Reranker improves them, and RAG uses those chunks to generate accurate answers.** 
