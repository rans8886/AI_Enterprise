## In the MCP ecosystem:
- The **MCP host** is the application where the AI model runs (e.g., a chatbot interface, AI agents, IDEs).
- The **MCP client** resides within the host and is responsible for making requests to external tools and data sources. It acts on behalf of the AI model and maintains 1:1 connections with the server while residing inside the host.
- The **MCP server** exposes an external tool or data source (like a database, API, or local file system). It serves information and capabilities to the client in a standardized format that the AI can understand.




## **How MCP actually works**

**Tools:** **Tools** are the action-oriented **functions** the **agent can execute.** Think of them as verbs; they actively do something, like creating a calendar entry, sending an email, or updating a database record. This is conceptually similar to a POST request in a traditional API, as it causes a change or performs an action.


**Resources:** Resources, on the other hand, **are read-only sources of information, essentially the nouns in the conversation.** They allow the agent to retrieve data for context, such as getting a list of files in a folder or reading today’s meeting schedule. This is analogous to a GET request, where the goal is simply to fetch information without altering it.


**Prompts:** Prompts are pre-defined recipes for interaction that reside on the server. They provide an optimized and reusable way to perform common tasks, saving users from the overhead of complex prompt engineering.

