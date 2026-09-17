# RAG Test Questions — Final Results (Week 4, Day 5)

Pipeline: vector search (top 10) → keyword boost → re-ranking (LLM judge, top 3)
Chunk size: [fill in whichever performed best from Day 1 testing]

---

## Results

| # | Question | Expected Topic | Status |
|---|----------|---------------|--------|
| 1 | What does standard shipping cost? | Shipping costs | ✅ PASS |
| 2 | How long does international shipping take? | International shipping | ✅ PASS |
| 3 | Can I return a worn item? | Return conditions | ✅ PASS |
| 4 | How long do I have to return something? | Return window | ✅ PASS |
| 5 | Can I cancel my order? | Order cancellation | ✅ PASS |
| 6 | How do I find my size? | Sizing guide | ✅ PASS |
| 7 | What payment methods do you accept? | Payment options | ✅ PASS |
| 8 | Can I use two discount codes at once? | Discount codes | ✅ PASS |
| 9 | What are customer support hours? | Support hours | ✅ PASS |
| 10 | Does free shipping apply to express delivery? | Express shipping | ✅ PASS |

**Final score: 10/10**

---

## Pipeline Evolution

- **Week 3 baseline:** vector search only, top 3 results
- **Week 4 Day 1:** tested chunk sizes (100 / 300 / 500 tokens) — [fill in winner]
- **Week 4 Day 2:** added keyword boosting — exact matches promoted to front of candidate list
- **Week 4 Day 3-4:** added LLM re-ranking — top 10 candidates scored by a second model call, best 3 selected

---

## Notes

- Question 3 (worn item) returned an empty reply on first re-ranker run — confirmed one-off model fluke, resolved on re-run
- Discount codes question (Q8) previously triggered an incorrect escalation tool call before re-ranking was added
- Re-ranking noticeably stabilized results for semantically ambiguous queries