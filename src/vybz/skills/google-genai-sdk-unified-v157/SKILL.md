---
name: google-genai-sdk-unified-v157
description: Standards and constraints for the unified google-genai library.
---

# Google GenAI SDK (Unified v1.57)
_Standards and constraints for the unified google-genai library._

## Knowledge
* We are strictly using the Unified Google Gen AI SDK (v1.57+).
* Target models: Gemini 3.0 Flash/Pro.
* Use the new unified Google Gen AI SDK (google-genai)
* The legacy `google-generativeai` library is forbidden.
* Use `client.aio.models.generate_content(...)` for async operations.
* If utilizing the `google-genai` SDK, assume version 1.57 syntax.
* ##### SYNTAX ENFORCER (DO NOT DEVIATE)
      The user is utilizing the **Unified SDK**. You must align your code with these patterns:
  
      | Concept | Legacy (FORBIDDEN) | Unified v1.57 (REQUIRED) |
      | :--- | :--- | :--- |
      | **Package** | `import google.generativeai` | `from google import genai` |
      | **Client** | `genai.configure(...)` | `client = genai.Client(...)` |
      | **Async** | `genai.ChatSession` | `client.aio.models.generate_content(...)` |
      | **Methods** | `model.supported_methods` | `model.supported_actions` |
      | **Config** | `generation_config={...}` | `config=types.GenerateContentConfig(...)` |
* ## CRITICAL: GOOGLE GEN AI SDK (v1.57+) STANDARDS
      You are strictly forbidden from using `google.generativeai`. You must use the 
      unified `google-genai` library. Because this library is new, you must adhere to
      the following interface definitions to avoid hallucinations:
  
      1.  **Import:** `from google import genai`
      2.  **Client:** `client = genai.Client(api_key=...)`
      3.  **List Models:**
         ```python
          # CORRECT
          for model in client.models.list():
              print(model.name)
              print(model.supported_actions) # NOT supported_methods
          ```
      4.  **Generation:**
          ```python
          response = client.models.generate_content(
              model='gemini-3-flash-preview',
              contents='Hello'
          )
          print(response.text)
          ```
      5.  **Types:** Use `from google.genai import types` for type hinting config 
          objects.

## Abilities
* Excells at precice code that targets the correct API version.
