# Llama Guard adapter

This CPU-friendly adapter implements the gateway's `/classify` contract and sends request/response
messages to the real `llama-guard3:1b` model hosted by the stack's private Ollama service. It parses
the model's textual `safe` or `unsafe` output and optional `S` category code.
