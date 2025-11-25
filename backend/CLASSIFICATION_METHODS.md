# Expense Category Classification Methods

This document explains the different OpenAI API methods available for expense category classification.

## Available Methods

### 1. Embeddings API (Recommended) ⭐

**Best for**: Production use, high volume, cost-sensitive applications

**How it works**:
- Converts expense descriptions and category descriptions into vector embeddings
- Uses cosine similarity to find the best matching category
- Fast and cost-effective

**Pros**:
- ✅ **Much cheaper**: ~$0.0001 per request (vs $0.001-0.002 for chat)
- ✅ **Faster**: Lower latency, better for real-time classification
- ✅ **Efficient**: Perfect for fixed category classification tasks
- ✅ **Scalable**: Can handle high volume of requests

**Cons**:
- ⚠️ Less context understanding (trip location, amount context)
- ⚠️ Requires good category descriptions

**Cost**: ~$0.0001 per classification (text-embedding-3-small)

### 2. Chat Completions API

**Best for**: Complex context, when accuracy is more important than cost

**How it works**:
- Uses GPT models to understand context and classify expenses
- Can consider trip destination, amount, and complex descriptions
- More "intelligent" classification

**Pros**:
- ✅ **Better context understanding**: Understands trip location, amount, nuances
- ✅ **More accurate**: Better at handling ambiguous descriptions
- ✅ **Flexible**: Can adapt to new patterns

**Cons**:
- ⚠️ **More expensive**: ~$0.001-0.002 per request (10-20x more)
- ⚠️ **Slower**: Higher latency due to generation
- ⚠️ **Overkill**: Full language model for simple classification

**Cost**: ~$0.001-0.002 per classification (gpt-3.5-turbo)

## Comparison

| Feature | Embeddings API | Chat Completions |
|---------|---------------|------------------|
| **Cost per request** | ~$0.0001 | ~$0.001-0.002 |
| **Speed** | Fast (~200ms) | Slower (~500-1000ms) |
| **Context understanding** | Limited | Excellent |
| **Accuracy** | Good (85-90%) | Excellent (90-95%) |
| **Best for** | High volume, production | Complex cases, accuracy-critical |

## Recommendation

**Use Embeddings API** for most cases because:
1. **Cost-effective**: 10-20x cheaper
2. **Fast**: Better user experience
3. **Sufficient accuracy**: 85-90% accuracy is good enough for expense categorization
4. **Scalable**: Can handle thousands of requests efficiently

**Use Chat Completions** only if:
- You need maximum accuracy (95%+)
- You have complex, ambiguous expense descriptions
- Cost is not a concern
- You need to understand nuanced context (e.g., "small shop in Japan" vs "large store")

## Configuration

Set in `.env` file:

```env
# Use embeddings (recommended)
OPENAI_CLASSIFICATION_METHOD=embeddings
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Or use chat completions
OPENAI_CLASSIFICATION_METHOD=chat
OPENAI_MODEL=gpt-3.5-turbo
```

## Web Search API?

**Not recommended** for this use case because:
- ❌ We have **fixed, predefined categories** - no web search needed
- ❌ Adds unnecessary cost and latency
- ❌ Categories don't change based on web results
- ❌ Expense descriptions are self-contained

Web search is useful for:
- Real-time information lookup
- Current events
- Dynamic data that changes frequently

But for expense categorization with fixed categories, embeddings or chat completions are more appropriate.

