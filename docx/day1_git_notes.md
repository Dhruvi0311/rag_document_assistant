1. Tokenization -> The process of breaking text into smaller units called tokens.

2. Subword Tokenization -> Splits words into smaller meaningful parts.
Benefits:
Handles rare words
Reduces vocabulary size
Improves efficiency

3. BPE (Byte Pair Encoding) -> A tokenization algorithm used by GPT models.
Repeatedly merges frequently occurring character pairs.
Helps build an efficient vocabulary.

4. Embeddings -> Numerical vector representations of text.
Convert language into numbers that models can understand.

5. Static (Pretrained) Embeddings
Examples:
Word2Vec
GloVe
fastText
Characteristics:
One fixed vector per word.
Cannot understand context.

6. Dynamic (Contextual) Embeddings
Examples:
BERT
GPT
ELMo
Characteristics:
Embeddings change based on context.
Better understanding of language.

7. WordPiece: Similar to BPE, but rather than just merging the most frequent pairs, it merges the pairs that most significantly increase the overall likelihood of the training data. It is famously used in BERT and its variants

8. SentencePiece: Unlike BPE and WordPiece, which require pre-segmented text, SentencePiece treats the entire input as a raw stream of bytes, including spaces
This makes it entirely language-agnostic and highly effective for languages without clear word boundaries (like Japanese or Chinese). It is utilized by models like T5 and ALBERT

