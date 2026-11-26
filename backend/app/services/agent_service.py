"""Lightweight multi-step agent workflow tailored for small local LLMs."""

import time

from app.services.ollama_service import OllamaService
from app.services.rag_service import rag_service


class AgentService:
    """Execute a compact Plan -> Retrieve -> Synthesize workflow."""

    def __init__(self, ollama: OllamaService | None = None) -> None:
        self.ollama = ollama or OllamaService()

    async def run_workflow(
        self,
        user_id: str,
        goal: str,
        model: str,
        use_rag: bool = True,
    ) -> dict:
        """Run a deterministic 3-step reasoning loop without overloading 4 GB RAM hosts."""
        start = time.perf_counter()
        steps: list[dict[str, str]] = []
        total_tokens = 0

        # Step 1: Decompose the goal into a focused sub-plan.
        plan_res = await self.ollama.chat_complete(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Break the user's goal into 2-3 concise action steps.",
                },
                {"role": "user", "content": goal},
            ],
            temperature=0.3,
        )
        total_tokens += plan_res.total_tokens
        steps.append({"step": "plan", "output": plan_res.content})

        # Step 2: Gather local document context via RAG when enabled.
        context_block = ""
        if use_rag:
            chunks = rag_service.query(user_id=user_id, query_text=goal, top_k=3)
            if chunks:
                context_block = "\n\n".join(
                    f"[{c['filename']}] {c['content']}" for c in chunks
                )
                steps.append(
                    {
                        "step": "retrieve_context",
                        "output": f"Retrieved {len(chunks)} relevant document chunks.",
                    }
                )
            else:
                steps.append(
                    {"step": "retrieve_context", "output": "No matching local documents found."}
                )

        # Step 3: Synthesize the final response.
        synthesis_prompt = (
            f"Goal: {goal}\n\nPlan:\n{plan_res.content}\n\n"
            + (f"Local Knowledge Context:\n{context_block}\n\n" if context_block else "")
            + "Provide a clear, accurate final answer."
        )
        final_res = await self.ollama.chat_complete(
            model=model,
            messages=[
                {"role": "system", "content": "You are a concise, helpful offline AI agent."},
                {"role": "user", "content": synthesis_prompt},
            ],
            temperature=0.5,
        )
        total_tokens += final_res.total_tokens
        steps.append({"step": "synthesize", "output": final_res.content})

        elapsed_ms = round((time.perf_counter() - start) * 1000.0, 2)
        return {
            "goal": goal,
            "model": model,
            "steps": steps,
            "final_answer": final_res.content,
            "total_tokens": total_tokens,
            "response_time_ms": elapsed_ms,
        }
