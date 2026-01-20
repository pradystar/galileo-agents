"""
Customer Support Knowledge Base Tools for TechGadgets Inc.

This module provides instrumented search functions for the Customer Support KB demo.
Each search function creates retrieval spans with document-type-specific metadata.
"""

import json

from crewai.tools import tool
from opentelemetry import trace

# Get the tracer for creating retrieval spans
tracer = trace.get_tracer("customer-support-kb")

# Customer Support Knowledge Base for TechGadgets Inc.
SUPPORT_KB = {
    "faqs": [
        {
            "id": "faq1",
            "title": "Return Policy",
            "content": "Items can be returned within 30 days of purchase for a full refund. "
            "Products must be in original packaging and unused condition. "
            "Electronics with opened software are subject to a 15% restocking fee. "
            "To initiate a return, visit our website or contact customer support.",
        },
        {
            "id": "faq2",
            "title": "Shipping Times",
            "content": "Standard shipping: 5-7 business days. Express shipping: 2-3 business days. "
            "Next-day delivery available for orders placed before 2 PM EST. "
            "International shipping: 10-14 business days. "
            "Free shipping on orders over $50.",
        },
        {
            "id": "faq3",
            "title": "Warranty Coverage",
            "content": "All TechGadgets products include a 1-year manufacturer warranty. "
            "Extended warranties available for purchase up to 3 years. "
            "Warranty covers defects in materials and workmanship. "
            "Physical damage and water damage are not covered under standard warranty.",
        },
        {
            "id": "faq4",
            "title": "Payment Methods",
            "content": "We accept Visa, MasterCard, American Express, and Discover. "
            "PayPal and Apple Pay are also available. "
            "Financing options through TechGadgets Credit for purchases over $200. "
            "Gift cards can be applied at checkout.",
        },
        {
            "id": "faq5",
            "title": "Account Management",
            "content": "Create an account to track orders and save payment methods. "
            "Password reset available via email verification. "
            "Update shipping addresses in account settings. "
            "Order history available for the past 2 years.",
        },
    ],
    "troubleshooting": [
        {
            "id": "ts1",
            "title": "Device Won't Turn On",
            "content": "Step 1: Check if the battery is charged - connect to power for at least 30 minutes. "
            "Step 2: Try a hard reset by holding the power button for 15 seconds. "
            "Step 3: Check if the charging cable and adapter are working properly. "
            "Step 4: If still not working, the battery may need replacement - contact support.",
        },
        {
            "id": "ts2",
            "title": "Bluetooth Connection Issues",
            "content": "Step 1: Ensure Bluetooth is enabled on both devices. "
            "Step 2: Remove the device from paired list and re-pair. "
            "Step 3: Restart both devices and try connecting again. "
            "Step 4: Check for firmware updates on both devices. "
            "Step 5: If persistent, reset network settings on your device.",
        },
        {
            "id": "ts3",
            "title": "Screen Display Problems",
            "content": "Step 1: Adjust brightness settings in device menu. "
            "Step 2: Check for screen protector interference or damage. "
            "Step 3: Restart the device to clear display cache. "
            "Step 4: Update to latest firmware version. "
            "Step 5: If flickering persists, may indicate hardware issue - contact support.",
        },
        {
            "id": "ts4",
            "title": "Battery Draining Quickly",
            "content": "Step 1: Check battery health in device settings. "
            "Step 2: Reduce screen brightness and disable unused features. "
            "Step 3: Close background applications. "
            "Step 4: Disable location services when not needed. "
            "Step 5: If battery health below 80%, consider replacement.",
        },
        {
            "id": "ts5",
            "title": "Device Not Charging",
            "content": "Step 1: Inspect charging port for debris or damage. "
            "Step 2: Try a different charging cable and adapter. "
            "Step 3: Clean the charging port gently with compressed air. "
            "Step 4: Check if wireless charging works (if supported). "
            "Step 5: If none work, charging port may need repair - contact support.",
        },
    ],
    "policies": [
        {
            "id": "pol1",
            "title": "Refund Process",
            "content": "Refunds are processed within 5-7 business days after we receive the returned item. "
            "Original payment method will be credited. "
            "Shipping costs are non-refundable unless item was defective. "
            "Refund confirmation email sent once processed.",
        },
        {
            "id": "pol2",
            "title": "Warranty Claims",
            "content": "To file a warranty claim: 1) Locate your proof of purchase. "
            "2) Contact support with device serial number and description of issue. "
            "3) Receive RMA number and shipping instructions. "
            "4) Ship device to our service center. "
            "5) Repair or replacement completed within 10-14 business days.",
        },
        {
            "id": "pol3",
            "title": "Escalation Procedure",
            "content": "Issues unresolved after 48 hours are automatically escalated to senior support. "
            "Request supervisor callback by asking any support agent. "
            "Executive escalation available for issues over 7 days old. "
            "Written complaints can be sent to support@techgadgets.example.com.",
        },
        {
            "id": "pol4",
            "title": "Price Match Guarantee",
            "content": "We match prices from authorized retailers within 14 days of purchase. "
            "Competitor must have item in stock at lower price. "
            "Does not apply to clearance, refurbished, or membership pricing. "
            "Submit price match request through customer support.",
        },
        {
            "id": "pol5",
            "title": "Data Privacy Policy",
            "content": "Customer data is encrypted and stored securely. "
            "We do not sell personal information to third parties. "
            "Request data deletion by contacting privacy@techgadgets.example.com. "
            "Usage analytics are anonymized and used to improve service.",
        },
    ],
}


def _search_documents(
    query: str, doc_type: str, documents: list[dict]
) -> list[dict]:
    """
    Internal function to search documents with keyword matching.
    Creates an instrumented retrieval span with metadata.

    Args:
        query: The search query
        doc_type: Type of documents being searched (faq, troubleshooting, policy)
        documents: List of documents to search

    Returns:
        List of matching documents
    """
    with tracer.start_as_current_span(f"{doc_type}_retrieval") as span:
        # Set retrieval span attributes
        span.set_attribute("db.operation", "query")
        span.set_attribute("db.system", "knowledge_base")
        span.set_attribute("retrieval.document_type", doc_type)
        span.set_attribute("retrieval.query_type", "keyword")

        # Record the input query
        span.set_attribute("gen_ai.input.messages", f"[{{'role': 'user', 'content': '{query}'}}]")

        # Simple keyword search - match documents containing query terms
        query_terms = query.lower().split()
        results = []

        for doc in documents:
            doc_text = f"{doc['title']} {doc['content']}".lower()
            # Score based on how many query terms appear in the document
            score = sum(1 for term in query_terms if term in doc_text)
            if score > 0:
                results.append({**doc, "_score": score})

        # Sort by relevance score and take top results
        results.sort(key=lambda x: x["_score"], reverse=True)
        top_results = results[:3]  # Return top 3 matches

        # Remove internal score from results
        for r in top_results:
            del r["_score"]

        # Set retrieval metadata
        span.set_attribute("retrieval.num_results", len(top_results))

        # Record the output as a list of documents (required for RETRIEVER spans)
        # The processor expects content to be a list of dicts for retriever output
        documents_list = [
            {"content": r["content"], "metadata": {"title": r["title"], "id": r["id"]}}
            for r in top_results
        ]
        span.set_attribute(
            "gen_ai.output.messages",
            json.dumps([{"role": "assistant", "content": documents_list}]),
        )

        return top_results


@tool
def search_faqs(query: str) -> str:
    """
    Search the FAQ knowledge base for answers to common customer questions.
    Use this tool to find information about returns, shipping, warranties, payments, and accounts.

    Args:
        query: The customer's question or search terms

    Returns:
        Relevant FAQ entries that match the query
    """
    results = _search_documents(query, "faq", SUPPORT_KB["faqs"])

    if not results:
        return "No relevant FAQ entries found for your query."

    formatted = []
    for doc in results:
        formatted.append(f"**{doc['title']}**\n{doc['content']}")

    return "\n\n---\n\n".join(formatted)


@tool
def search_troubleshooting(query: str) -> str:
    """
    Search the troubleshooting guide for step-by-step solutions to technical issues.
    Use this tool when customers have problems with their devices.

    Args:
        query: Description of the technical issue

    Returns:
        Relevant troubleshooting guides with step-by-step instructions
    """
    results = _search_documents(query, "troubleshooting", SUPPORT_KB["troubleshooting"])

    if not results:
        return "No relevant troubleshooting guides found for this issue."

    formatted = []
    for doc in results:
        formatted.append(f"**{doc['title']}**\n{doc['content']}")

    return "\n\n---\n\n".join(formatted)


@tool
def search_policies(query: str) -> str:
    """
    Search company policies for information about refunds, warranty claims, escalations, and more.
    Use this tool for policy-related questions or when escalating issues.

    Args:
        query: The policy topic or question

    Returns:
        Relevant policy documents
    """
    results = _search_documents(query, "policy", SUPPORT_KB["policies"])

    if not results:
        return "No relevant policy documents found for your query."

    formatted = []
    for doc in results:
        formatted.append(f"**{doc['title']}**\n{doc['content']}")

    return "\n\n---\n\n".join(formatted)
