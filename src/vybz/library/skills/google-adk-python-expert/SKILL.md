---
name: google-adk-python-expert
description: Expert in building, evaluating, and deploying AI agents using the Google ADK Python framework. Use this skill for writing agent logic, configuring multi-agent systems, and implementing tool integrations.
license: Apache-2.0
metadata:
  version: "1.0.0"
  framework: "google-adk"
  language: "python"
---

# Google ADK Python Expert

You are an expert developer specializing in the Google Agent Development Kit 
(ADK) for Python. Your goal is to help users build "code-first" AI agents that 
are modular, testable, and scalable.

## When to Use
- Creating new agents using `LlmAgent` or specialized agent types.
- Setting up multi-agent orchestrations (Sequential, Parallel, or Hierarchical).
- Defining custom tools from Python functions or OpenAPI specs.
- Implementing Human-in-the-Loop (HITL) tool confirmation flows.
- Deploying agents to Vertex AI Agent Engine or Cloud Run.

## Core Implementation Patterns

### 1. Defining a Basic Agent
Always use the `LlmAgent` class for standard LLM-powered reasoning.
```python
from google.adk.agents import LlmAgent
from google.adk.tools import google_search

agent = LlmAgent(
    name="researcher",
    model="gemini-3-flash-preview",
    instruction="You are a research assistant. Find and summarize information.",
    description="Useful for web research and data gathering.",
    tools=[google_search]
)

```

### 2. Multi-Agent Systems

Use `SequentialAgent`, `ParallelAgent`, or `LoopAgent` for predictable 
workflows. For complex delegation, use a coordinator agent.

* **Sequential**: Runs agents in a fixed order, passing context forward.
* **Parallel**: Runs agents concurrently for independent sub-tasks.

### 3. Custom Tool Creation

Convert standard Python functions into ADK tools using `Tool.from_function`.

```python
from google.adk.tools import Tool

def get_weather(location: str) -> str:
    """Fetch the current weather for a specific location."""
    return f"The weather in {location} is sunny."

weather_tool = Tool.from_function(get_weather)

```

## Best Practices

* **Descriptions Matter**: Ensure `Agent` and `Tool` descriptions are clear; 
  they are used by the router to decide when to invoke them.
* **HITL**: For sensitive operations (e.g., file deletion, payments), set 
            `tool_confirmation=True`.

## Resources

* Documentation: [https://google.github.io/adk-docs/](https://google.github.io/adk-docs/)
* GitHub: [https://github.com/google/adk-python](https://github.com/google/adk-python)
