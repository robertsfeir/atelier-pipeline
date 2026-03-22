# Citation List

**Article:** "When Your AI Agents Remember: Building Institutional Memory for Synthetic Minds"
**Author:** Robert Sfeir
**Date:** March 21, 2026

---

## Academic Papers

1. **Park, J.S., O'Brien, J.C., Cai, C.J., Morris, M.R., Liang, P., & Bernstein, M.S. (2023).** "Generative Agents: Interactive Simulacra of Human Behavior." *UIST 2023, Stanford University / Google Research.* Three-axis memory scoring formula (recency × importance × relevance), reflection mechanism, crowdworker believability study. https://arxiv.org/abs/2304.03442

2. **Packer, C., Wooders, S., Lin, K., Fang, V., Patil, S.G., Stoica, I., & Gonzalez, J.E. (2023).** "MemGPT: Towards LLMs as Operating Systems." *arXiv:2310.08560.* Virtual memory hierarchy for LLM agents, strategic forgetting through summarization, two-tier architecture (main context + archival). https://arxiv.org/abs/2310.08560

3. **Choudhury, T., et al. (2025).** "Mem0: Building Production-Ready AI Agent Memory." *arXiv:2504.19413.* 26% improvement over OpenAI built-in memory, 91% lower p95 latency, >90% token cost reduction. LOCOMO benchmark evaluation. https://arxiv.org/abs/2504.19413

4. **Hindsight (2025).** "Hindsight: A Multi-Channel Memory Retrieval System for AI Agents." *arXiv:2512.12818.* Four parallel retrieval channels merged via Reciprocal Rank Fusion: semantic similarity, BM25 keyword, graph traversal via spreading activation, temporal filtering with decay. https://arxiv.org/html/2512.12818v1

5. **Radhakrishnan, A., et al. (2025).** "Graphiti: Building Real-time Knowledge Graphs for Agentic Systems." *arXiv:2501.13956, Zep.* Write-time conflict detection, bi-temporal model (t_valid, t_invalid, t'_created, t'_expired), LLM classification of contradiction/duplicate/novel. https://arxiv.org/html/2501.13956v1

6. **HEMA (2025).** "HEMA: A Dual-Memory System for Long-Context AI Agents." *arXiv:2504.16754.* Hippocampus-inspired compact + vector memory, age-weighted semantic pruning, factual recall improvement from 41% to 87%. https://arxiv.org/abs/2504.16754

7. **Agent Drift Study (2026).** *arXiv:2601.04170.* Task success rate declined 42%, human interventions increased 216%, inter-agent conflicts increased 487.5% when agent roles are not clearly separated. https://arxiv.org/abs/2601.04170

8. **Knowledge Graph Inconsistency Survey (2025).** *arXiv:2502.19023.* Detection, fixing, and reasoning-in-presence-of inconsistencies. TBox, ABox, and combined approaches. Update-based repairing preserves information. https://arxiv.org/html/2502.19023v1

9. **Kusupati, A., et al. (2022).** "Matryoshka Representation Learning." *NeurIPS 2022.* Truncating embeddings to 50% of dimensions loses only 1-4 percentage points across tasks. At 8% of dimensions, retains 98.37% of quality. https://arxiv.org/abs/2205.13147

## Industry & Production Systems

10. **GitHub Copilot Team (2026).** "Building an Agentic Memory System for GitHub Copilot." *GitHub Blog.* Query-time self-healing, adversarial memory testing, agents consistently caught contradictions and stored corrected versions. https://github.blog/ai-and-ml/github-copilot/building-an-agentic-memory-system-for-github-copilot/

11. **Google Cloud Platform (2026).** "Always-On Memory Agent." *Generative AI repository.* Three-agent system (Ingest, Consolidate, Query), timer-based consolidation (default 30 min), mimics sleep-based memory consolidation. SQLite + LLM reasoning, no vector database. https://github.com/GoogleCloudPlatform/generative-ai/tree/main/gemini/agents/always-on-memory-agent

12. **Anthropic (2025).** "Effective Context Engineering for AI Agents." *Anthropic Engineering Blog.* "Intelligence is not the bottleneck, context is." File-based memory, LLM-curated markdown, just-in-time data loading. Longer context windows often make things worse. https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

13. **Microsoft Azure AI Search Team.** "Outperforming Vector Search with Hybrid Retrieval and Reranking." *Azure AI Foundry Blog.* Pipeline design matters 6x more than embedding model choice. Vector only NDCG@3 = 43.8 → Hybrid + reranker = 60.1 (37% improvement, same embedding model). https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/azure-ai-search-outperforming-vector-search-with-hybrid-retrieval-and-reranking/3929167

14. **Microsoft (2025).** "Agent Framework (Semantic Kernel + AutoGen)." *Microsoft Learn.* First-class Memory abstraction with pluggable vector store backends, just-in-time data loading pattern. https://learn.microsoft.com/en-us/agent-framework/overview/

15. **Confident AI.** "Why We Replaced Pinecone with pgvector." *Confident AI Blog.* Under 5,000 documents, brute-force cosine similarity over pgvector outperforms ANN indexes. Network latency, not search, is the bottleneck. https://confident-ai.com/blog/why-we-replaced-pinecone-with-pgvector

16. **OpenAI (2024).** "New Embedding Models and API Updates." *OpenAI Blog.* text-embedding-3-large truncated to 256 dims outperforms ada-002 at full 1536 dims on MTEB. https://openai.com/index/new-embedding-models-and-api-updates/

## Practitioner References

17. **Jones, Nate B. (2025).** "Every AI You Use Forgets You. Here's How to Fix That." *Nate's Newsletter / OB1.* Single-axis scoring (cosine similarity only), Zettelkasten-style atomic thoughts, tight embedding units make multi-axis scoring less necessary at small scale. https://natesnewsletter.substack.com/p/every-ai-you-use-forgets-you-heres

18. **Thomas, Chris (2025).** "Match Embedding Dimensions to Your Domain, Not Defaults." *christhomas.co.uk.* "3072 dimensions gets no benefit over 768 dimensions for four out of five domains." Under 1,000 docs → 256 dims suffice. https://christhomas.co.uk/blog/2025/10/31/match-embedding-dimensions-to-your-domain-not-defaults/

19. **Bernhardsson, Erik.** "Nearest Neighbors and Vector Models — Epilogue: Curse of Dimensionality." *erikbern.com.* Real embeddings lie on low-dimensional manifolds. Freebase 1000D vectors behave like 16D normal data. https://erikbern.com/2015/10/20/nearest-neighbors-and-vector-models-epilogue-curse-of-dimensionality.html

20. **Brian M.** "Ook — Local Semantic Search." *GitHub.* Local embeddings via multi-qa-mpnet-base-cos-v1 + ONNX runtime, 768 dimensions, fully on-device, zero API cost. https://github.com/brianm/ook

## Foundational References

21. **Nygard, Michael (2011).** "Documenting Architecture Decisions." *Cognitect Blog.* Original ADR format — append-only, four statuses (Proposed, Accepted, Deprecated, Superseded). "The motivation behind previous decisions is visible for everyone, present and future." https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions

22. **Fowler, Martin & Harmel-Law, Andrew.** "Scaling Architecture Conversationally." *martinfowler.com.* ADRs as "thinking and decision lore," Advice section capturing contributor context, accumulation as learning ground. https://martinfowler.com/articles/scaling-architecture-conversationally.html

---

*21 unique sources. Compiled from mybrain research capture (March 18-21, 2026).*
