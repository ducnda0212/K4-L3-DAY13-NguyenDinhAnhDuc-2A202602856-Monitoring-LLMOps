from __future__ import annotations

import time

from .incidents import STATE
from .pii import summarize_text
from .tracing import get_langfuse_client, observe

CORPUS = {
    "refund": ["Refunds are available within 7 days with proof of purchase."],
    "monitoring": ["Metrics detect incidents, logs identify affected requests, traces localize the root cause."],
    "policy": ["Do not expose PII in logs. Use sanitized summaries only."],
}


@observe(
    name="retrieval",
    as_type="retriever",
    capture_input=False,
    capture_output=False,
)
def retrieve(message: str) -> list[str]:
    langfuse_client = get_langfuse_client()
    query_preview = summarize_text(message)

    langfuse_client.update_current_span(
        metadata={
            "query_preview": query_preview,
            "tool_name": "retrieval",
        }
    )

    if STATE["tool_fail"]:
        langfuse_client.update_current_span(
            metadata={
                "query_preview": query_preview,
                "tool_name": "retrieval",
                "tool_success": False,
            }
        )
        raise RuntimeError("Vector store timeout")

    if STATE["rag_slow"]:
        time.sleep(2.5)

    lowered = message.lower()
    result = ["No domain document matched. Use general fallback answer."]

    for key, docs in CORPUS.items():
        if key in lowered:
            result = docs
            break

    langfuse_client.update_current_span(
        output={"doc_count": len(result)},
        metadata={
            "query_preview": query_preview,
            "doc_count": len(result),
            "tool_name": "retrieval",
            "tool_success": True,
        },
    )

    return result
