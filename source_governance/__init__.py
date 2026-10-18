"""
Expose deterministic source governance independently of model execution.
The package reads repository source and configuration; it never calls inference.
Command entrypoints live in scripts and delegate to these bounded components.
"""
