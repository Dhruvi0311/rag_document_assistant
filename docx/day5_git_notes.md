Aaj ki saari chat ka ek crisp aur structural **Technical Summary Report (Short Notes)** niche diya gaya hai. Ise aap apne reference ya future documentation ke liye save karke rakh sakti hain.

---

## 🏗️ 1. Overall Pipeline Architecture & Workflow

Hamara complete System Pipeline 3 stages mein divided hai jo structured aur unstructured formats (Scanned/Unscanned) ko chatbot-ready vectors mein convert karta hai:

```
[Raw Files Folder] ──> [1. Document Loader] ──> [2. Document Chunker] ──> [3. Vector Store]
                       (Parsing & OCR)          (LangChain Splitter)     (ChromaDB Indexing)

```

---

## 📄 2. File-by-File Breakdown & Workflow

### 📁 A. `src/document_loader.py` (The Extraction Layer)

* **Workflow:** Target folder se saari files fetch karta hai ──> File extension verify karke correct parsing function text layer par bhejta hai ──> Empty ya scanned page milne par **Tesseract OCR Fallback** activate karke text image se extract karta hai.
* **Important Features:**
* **Format Routing:** Clean PDFs (`pypdf`), Word Docs (`python-docx`), and Tables (`csv`) ko uniquely extract karta hai.
* **Initial Identity Generation:** Har file ka ek absolute SHA-256 binary string compute karke uniquely mapped `doc_id` generate karta hai.



### ✂️ B. `src/document_chunker.py` (The Processing Layer)

* **Workflow:** Loader se raw text blocks and metadata array accept karta hai ──> Standard text paragraph/prose par **LangChain's Recursive Character Splitter** chalata hai ──> CSV rows aur structured tables ko bina kaate poora single chunk rakhta hai.
* **Important Features:**
* **Sliding Window Constraint:** Context split optimization ke liye `chunk_size=500` aur `chunk_overlap=100` handle karta hai.
* **Strict Lineage Tracking:** Metadata dictionaries ke andar parent documents ke dynamic parameters like `page_number` ya `row_index` loop back maintain rakhta hai.



### 🗄️ C. `src/vector_store.py` (The Storage & Search Layer)

* **Workflow:** Chunks array receive karta hai ──> In-built HuggingFace **`all-MiniLM-L6-v2`** model ke through texts ke **384-dimensional mathematical arrays (embeddings)** banata hai ──> Collections create karke vector indexes disk (`chroma_db/`) par persist karta hai.
* **Important Features:**
* **Metadata Filtering:** Query ke dauran strict search filter execute karne ke liye `where={"file_name": file_filter}` conditions run karta hai taaki ek single file ke top chunks separate dikh sakein.
* **Idempotent Execution (`upsert`):** Purane identical records ko duplicate karne ke bajaye overwrite karta hai.



### 🧪 D. `src/test_pipeline.py` (The Verification Runner)

* **Workflow:** Pure components system ko sequence mein call karta hai ──> System pipeline logs coordinate karke run output directly shell display screen par print karta hai.

---

## ⚡ 3. Critical Learnings & Important Technical Points

### 🚨 Memory Optimization & The Framework Crash

* **Problem:** Python execution environment ke andar `langchain-text-splitters` load karte waqt background package mapping engine (`sentence-transformers`, `scipy`) memory stack overflow ho gaya aur process Linux OS dwara forcefully freeze ho gayi.
* **Fix:** Variable warning optimization hook pipeline implement kiya (`warnings.filterwarnings("ignore")`). Yeh process compiler ko heavy auxiliary routines skip karne pe force karta hai, jisse pipeline framework RAM control limits ke andar cleanly load ho jata hai.

### 📐 Embedding Space & Cosine Distance

* **Concept:** Embeddings text characters ko check nahi karte balki exact mathematical angles map karte hain.
* **Search Thresholds:** `Distance` score jitna `0.0000` ke paas hoga, similarity utni hi high hoti hai. Test query run par hamne notice kiya ki `7.pdf` (conceptual context) ne **0.62** score diya, jabki unaligned `sample.csv` rows ka distance score **0.97** tha, jo semantic search accuracy ko optimize karne ke liye critical matrix hai.

### 🧐 Commercial Upgrades Strategy (LLMWhisperer)

* **Insight:** Standard pixel OCR (Tesseract) multi-column text layouts ko merge kar deta hai aur tables ko left-to-right break karta hai, jisse data corrupted vectors mein convert ho jata hai. Unstract ka **LLMWhisperer API** multi-column layouts aur tabular formats ko structural white-space padding se read karke perfect retrieval accuracy maintain rakhta hai.