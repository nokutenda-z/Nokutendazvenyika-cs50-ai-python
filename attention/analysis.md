# Analysis

## Layer 6, Head 1 - Each token attends to the previous token

In this head, each token appears to pay strong attention to the token immediately before it. For example, in "We turned down a narrow lane and passed through a small [MASK].", "turned" attends to "we", "down" attends to "turned", and "lane" attends to "narrow". This creates a bright diagonal in the diagram. This suggests the head has learned to keep track of the previous word to understand local order.

Example sentences:
1. "We turned down a narrow lane and passed through a small [MASK]."
2. "The cat sat on the [MASK]."

## Layer 8, Head 11 - Verbs attend to their direct objects

In this head, verbs appear to pay attention to their direct objects. For example, in "She gave him a [MASK] for his birthday.", "gave" attends strongly to the masked word, which is the thing being given. In "The dog chased the [MASK] across the park.", "chased" attends strongly to the masked word, which is the thing being chased. This suggests the head has learned the relationship between a verb and what the verb acts on.

Example sentences:
1. "She gave him a [MASK] for his birthday."
2. "The dog chased the [MASK] across the park."