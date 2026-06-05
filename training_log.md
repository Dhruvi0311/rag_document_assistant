# Day 1: Project Setup & GenAI Fundamentals

### What I learned

* Basics of Generative AI and NLP
* Tokenization and Subword Tokenization
* Embeddings and Vector Representations
* Static vs Dynamic Embeddings
* Semantic Search and Embeddings in RAG Systems

### What I implemented

* Created the project structure for the chatbot project
* Initialized and organized the repository
* Uploaded the project to GitHub
* Set up the development environment

### Issues faced

* Understanding how embeddings capture semantic meaning
* Differentiating between static and contextual embeddings

### Tomorrow's plan

* Study sequence models (RNN, LSTM)
* Learn Seq2Seq architecture and Attention Mechanism
* Understand the evolution of Transformer-based models

---

# Day 2: Evolution of Transformers

### What I learned

* RNN and Hidden State
* Vanishing Gradient Problem
* LSTM (Cell State, Forget Gate, Input Gate, Output Gate)
* Seq2Seq Architecture
* Encoder, Decoder, Context Vector
* Teacher Forcing
* Attention Mechanism
* Query, Key, Value (QKV)
* Self-Attention and Cross-Attention
* Multi-Head Attention
* Transformer Architecture
* Positional Encoding
* Encoder-Only (BERT) and Decoder-Only (GPT) Models
* Evolution: RNN → LSTM → Seq2Seq → Attention → Transformer → BERT/GPT → LLMs

### What I implemented

* Studied and documented the complete evolution of sequence models to Transformers
* Created conceptual notes for Transformer architecture and attention mechanisms

### Issues faced

* Understanding the intuition behind QKV and attention score calculation
* Distinguishing between Encoder-only, Decoder-only, and Encoder-Decoder architectures

### Tomorrow's plan

* Study Large Language Models (LLMs)
* Learn Retrieval-Augmented Generation (RAG)
* Explore Vector Databases and Retrieval Pipelines
* Begin understanding Agentic AI concepts and workflows

---

# Day 3: LangChain, Embeddings, Vector Databases, Retrieval & RAG

### What I learned

* LangChain fundamentals:

  * Models
  * Prompt Templates
  * Chains
  * Output Parsers
  * LCEL (LangChain Expression Language)
* Embeddings and vector representations of text
* Semantic Search and Cosine Similarity
* Vector Databases:

  * FAISS
  * Chroma
  * Pinecone
  * Indexing and ANN Search
* Retrieval Systems:

  * Document Loaders
  * Chunking
  * Chunk Overlap
  * Retrievers
  * Top-K Retrieval
  * Re-ranking
* RAG (Retrieval Augmented Generation) architecture and workflow
* Difference between RAG and Fine-Tuning
* Real-world use cases of RAG in document chatbots and knowledge assistants

### What I implemented

* Studied end-to-end RAG pipeline architecture
* Explored document chunking and retrieval strategies
* Understood embedding generation and vector storage workflow
* Designed conceptual flow for document-based question answering systems

### Issues faced

* Understanding how embeddings capture semantic meaning
* Confusion between Vector Databases and Retrievers
* Understanding the role of Re-ranking in improving retrieval accuracy
* Visualizing complete RAG data flow from documents to final response

### Tomorrow's plan

* Memory Systems in LangChain
* Tool Calling and Custom Tools
* AI Agents and ReAct Framework
* LangGraph Fundamentals
* Building Agentic AI workflows and multi-step reasoning systems

# Day 4: LangChain Agentic AI Fundamentals

### What I learned

* Memory Systems in LangChain

  * Buffer Memory
  * Summary Memory
  * Vector Memory
  * Embeddings and Vector Databases
  * Similarity Search and Context Management
* Tool Calling and Function Calling

  * Tool execution workflow
  * External APIs and custom tool integration
* Custom Tools in LangChain

  * Building domain-specific tools for AI applications
* AI Agents

  * Agent architecture (LLM + Memory + Tools + Planning)
  * Agentic loops and autonomous decision-making
* ReAct Framework

  * Thought → Action → Observation cycle
  * Reasoning and tool usage patterns
* Retrieval-Augmented Generation (RAG)

  * Chunking, Embeddings, Retrieval, and Generation pipeline
* LangGraph Fundamentals

  * Nodes, Edges, StateGraph
  * Stateful workflows and shared state management
  * Conditional routing and cyclic workflows
* Advanced LangGraph Concepts

  * Persistence Layer and Checkpointers
  * Human-in-the-Loop (HITL)
  * Time Travel Debugging
  * Fault Tolerance, Retries, Timeouts, Error Handling
  * Multi-Agent Collaboration and Orchestration

### What I implemented

* Explored the architecture and workflow design of Agentic AI systems.
* Studied how LangChain and LangGraph can be used to build production-ready AI applications.
* Analyzed the end-to-end flow of RAG-based and agent-based systems.

### Issues faced

* Understanding the transition from simple LangChain chains to stateful LangGraph workflows.
* Grasping advanced concepts such as persistence, checkpointers, and multi-agent orchestration.

### Tomorrow's plan

* Learn LangGraph implementation with code examples.
* Build a basic LangGraph workflow with nodes, edges, and shared state.
* Explore LangChain Agents, AgentExecutor, and Tool integration practically.
* Integrate learned concepts into the RAG Document Assistant project.

