1. RNN (Recurrent Neural Network)
Purpose
    Handle sequential data.
Core Idea
    Current Input + Previous Memory
    ↓
    Output + New Memory
Key Terms
    Hidden State (h) → Memory of previous inputs
    Recurrent Connection → Passes memory forward
Problems
    Vanishing Gradient
    Long-Term Dependency Problem
    Sequential Processing (Slow)


2. LSTM (Long Short-Term Memory)
Purpose
    Solve RNN memory problem.
Core Idea
    Remember Important
    Forget Unimportant
Key Terms
    Cell State (Ct) → Long-term memory
    Hidden State (ht) → Current memory/output
Gates
    Forget Gate → What to remove?
    Input Gate → What to store?
    Output Gate → What to output?
Advantages
    Better long-term memory
    Reduces vanishing gradient


3. Seq2Seq (Sequence-to-Sequence)
Purpose
    Convert one sequence into another.
Examples:
    Translation
    Summarization
    QA
Architecture
    Input
    ↓
    Encoder
    ↓
    Context Vector
    ↓
    Decoder
    ↓
    Output
Key Terms
    Encoder → Understands input
    Decoder → Generates output
    Context Vector → Compressed summary
    Teacher Forcing → Uses actual previous token during training
Problem
    Context Vector Bottleneck (Long inputs lose information)



4. Attention
Purpose
    Fix Context Vector Bottleneck.
Core Idea
    Focus on Important Words
    Instead of: One Summary
    Use: Look at Entire Input
QKV Mechanism
    Query (Q) -> What am I looking for?
    Key (K) -> What information do I contain?
    Value (V) -> Actual information.
Formula
    Score = Q × K
    ↓
    Softmax
    ↓
    Weights × Values
    ↓
    Attention Output
Types of Attention
    Self-Attention -> Word attends to words in same sequence.
    Cross-Attention -> Decoder attends to encoder output.
    Global Attention -> Whole sequence.
    Local Attention -> Nearby tokens only.


5. Transformer
Paper: Attention Is All You Need
Purpose
    Remove recurrence completely.
Core Idea
    Attention
    +
    Parallel Processing
Transformer Block
    Input
    ↓
    Embedding
    ↓
    Positional Encoding
    ↓
    Multi-Head Attention
    ↓
    Feed Forward Network
    ↓
    Output
Important Terms
    Token Embedding -> Token → Vector
    Positional Encoding -> Adds word position information.
    Multi-Head Attention -> Multiple attentions in parallel.
    Feed Forward Network (FFN) -> Additional processing layer.
    Residual Connection -> Skip connection for stable training.
    Layer Normalization -> Normalizes activations.
Encoder Block
    Multi-Head Attention
    +
    FFN
    +
    Residual
    +
    LayerNorm
Decoder Block
    Masked Self-Attention
    +
    Cross-Attention
    +
    FFN
Masked Self-Attention -> Cannot see future tokens.Used in GPT.
Transformer Types
    Encoder Only
        Example: BERT
        Use: Classification, Search , Embeddings
    Decoder Only 
        Examples: GPT, Llama
        Use:Text Generation
    Encoder + Decoder
        Examples:T5, BART
        Use:Translation, Summarization
Complete Evolution
RNN
↓
LSTM
↓
Seq2Seq
↓
Attention
↓
Transformer
↓
BERT / GPT
↓
LLMs