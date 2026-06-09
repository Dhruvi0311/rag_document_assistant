# Agentic AI & LangGraph Short Notes

## Memory Systems

* **Buffer Memory** → Stores complete conversation history.
* **Summary Memory** → Stores summarized chat history to reduce tokens.
* **Vector Memory** → Stores embeddings in a vector database for semantic retrieval.
* **Embedding** → Numerical representation of text preserving meaning.
* **Vector DB** → Stores embeddings (FAISS, Chroma, Pinecone).
* **Cosine Similarity** → Measures semantic similarity between vectors.

---

## Tool Calling

* Enables LLMs to use external functions/APIs.
* Flow:

  ```text
  User → LLM → Tool → Result → Final Answer
  ```
* Reduces hallucinations.
* Used for weather, search, databases, calculators, etc.

---     

## Custom Tools   

* User-defined functions accessible by agents.
* Examples:

  * Resume Parser
  * Skill Extractor         
  * Job Search Tool
  * Course Recommendation Tool

---

## AI Agents

* LLM + Memory + Tools + Planning.
* Can reason, choose tools, observe results, and make decisions.
* Agent Loop:   

  ```text
  Think → Act → Observe → Repeat
  ```

---

## ReAct Framework   

* **ReAct = Reason + Act**
* Pattern: 

  ```text
  Thought → Action → Observation
  ```
* Improves reasoning and tool usage.

---

## RAG (Retrieval-Augmented Generation)

* Uses external knowledge instead of relying only on LLM memory.
* Pipeline:

  ```text
  Documents → Chunking → Embeddings
            → Vector DB → Retrieval → LLM 
  ```
* Key Terms:

  * Chunking
  * Retriever
  * Top-K Retrieval
  * Semantic Search

---

## LangGraph

* Framework for building stateful AI workflows.
* Supports:

  * Loops
  * Conditional Branching
  * Multi-Agent Systems
  * Persistence

---

## Graph Components

### Node

* Individual task/function.
* Example:

  * Parse Resume
  * Search Jobs

### Edge

* Connection between nodes.

### Conditional      

* Dynamic routing based on conditions.

---

## StateGraph

* Core LangGraph abstraction.
* Shared state accessible across all nodes.
* Example:

  ```python
  state = {
      "resume": ...,
      "skills": ...,
      "jobs": ...
  }
  ```

---

## Cyclic Workflows

* Allows loops and retries.
* Example:

  ```text
  Search → Evaluate
      ↑      ↓
      └ Retry ┘
  ```

---

## Persistence Layer

* Saves workflow state during execution.
* Enables recovery after crashes/failures.

---

## Checkpointers

* Save state after each step.
* Similar to game save checkpoints.
* Allows workflow resume from last successful step.

---

## Human-in-the-Loop (HITL)

* Human approval before critical actions.
* Example:

  ```text
  Agent → Human Review → Continue
  ```

---

## Time Travel

* Rewind workflow to a previous state.
* Useful for debugging and experimentation.

---

## Fault Tolerance

### Retry Policies

* Automatically retry failed operations.

### Timeouts

* Stop long-running tasks after a limit.

### Error Handlers

* Fallback logic instead of workflow failure.

---

## Multi-Agent Systems

### Specialized Agents

* Resume Agent
* Job Agent
* Learning Agent

### Supervisor Agent

* Coordinates all agents and combines outputs.

---

## LangChain vs LangGraph

| Feature            | LangChain | LangGraph |
| ------------------ | --------- | --------- |
| Linear Chains      | ✅         | ✅         |
| Loops              | ❌         | ✅         |
| Shared State       | Limited   | ✅         |
| Persistence        | Limited   | ✅         |
| HITL               | Difficult | ✅         |
| Multi-Agent        | Difficult | ✅         |
| Production Systems | Medium    | ✅         |

---

## One-Line Definitions

* **Memory:** Store and retrieve conversation context.
* **Embedding:** Numerical representation of text.
* **Tool Calling:** LLM uses external functions/APIs.
* **Custom Tool:** Developer-defined callable function.
* **Agent:** LLM capable of reasoning and acting.
* **ReAct:** Thought → Action → Observation framework.
* **RAG:** Retrieval + LLM generation.
* **LangGraph:** Stateful graph-based agent framework.
* **StateGraph:** Graph with shared persistent state.
* **Checkpointer:** Saves workflow state for recovery.
* **HITL:** Human approval during execution.
* **Multi-Agent System:** Multiple specialized agents collaborating.
