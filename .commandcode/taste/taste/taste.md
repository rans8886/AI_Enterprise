# Taste
- Prefers to discuss and agree on a plan before implementation; explicitly instructs the agent not to write code yet ("Lets discuss don't code", "Lets create a plan"). Confidence: 0.8
- Wants planning artifacts written to disk as markdown files in the project folder, using a numbered filename convention (e.g. `01_TestCreatorMCP.plan.md`). Confidence: 0.7
- Prefers to commit and push everything in the repo, including auto-managed local config (`.commandcode/settings.json`, `.commandcode/taste/`, skills), rather than excluding or gitignoring it — even after being warned it will cause recurring small commits. Confidence: 0.6
- Organizes projects as numbered folders under a parent workspace directory (e.g. `D:\AI_Enterprise\006_JobTrackerAI`). Confidence: 0.6
- Keeps the entire workspace in a single GitHub repo (e.g. `github.com/rans8886/AI_Enterprise`) and expects finished work to be committed and pushed there. Confidence: 0.5
- Uses FastMCP to build MCP servers. Confidence: 0.6
- Wants the workspace root README kept accurate and in sync with the actual repo structure — a single index of every project folder with real descriptions, a directory tree, and setup commands for each runnable project. Confidence: 0.6
- Builds tooling intended to be shareable with other QA and Dev team members, not just for personal use. Confidence: 0.6
- Prefers to author document/spec content (e.g. a project's `prompt.md`) themselves rather than have the agent synthesize or reconstruct it from prior context — chose to paste the text in manually when offered an auto-filled version. Confidence: 0.5
