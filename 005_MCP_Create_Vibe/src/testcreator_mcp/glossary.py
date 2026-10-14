"""Glossary content served as an MCP resource.

The per-module lines describe the screens and actions that actually appear in the corpus
(for example ``Funnels`` is tested via the funnel builder, step drop-off and segment
comparison), so the glossary stays traceable to the data rather than to product marketing.
"""

from __future__ import annotations

VWO_OVERVIEW = """\
VWO (Visual Website Optimizer) - Overview

VWO is a digital experience optimization platform used by product, marketing and growth
teams to improve website and application performance through experimentation, analytics
and personalization.

Core capabilities: A/B testing, multivariate testing, feature experimentation,
behaviour analytics (heatmaps, session recordings, funnels, form analytics) and
personalization.

Typical workflow: identify a problem with analytics, form a hypothesis, create an
experiment, run it on real users, analyse results, roll out the winning variation.
"""

MODULE_GLOSSARY: dict[str, str] = {
    "A/B Testing": "Comparing variations of a page or campaign; cases cover traffic allocation and campaign creation.",
    "Account & Billing": "Workspace-level account and subscription concerns; cases cover plan seats and seat limits.",
    "Feature Rollout": "Controlled release of features behind flags; cases cover flag creation and percentage rollout.",
    "Form Analytics": "Form performance reporting; cases cover submission rate, field drop-off and error tracking.",
    "Funnels": "Multi-step conversion analysis; cases cover the funnel builder, step drop-off and segment comparison.",
    "Goals & Metrics": "Conversion goal configuration and reporting; cases cover revenue and engagement goals.",
    "Heatmaps": "Visual click and attention maps; cases cover the click map and segment filters.",
    "Integrations": "Third-party connections; cases cover CRM push and webhook delivery.",
    "Multivariate Testing": "Testing several changes at once; cases cover winner analysis.",
    "Personalization": "Tailored experiences per audience segment; cases cover dynamic content, campaign targeting and scheduling.",
    "Reports": "Report generation and distribution; cases cover report export, scheduled email and segment reports.",
    "SDK / Server-Side API": "Programmatic integration surface; cases cover the getVariation call, tracking conversions and schema validation.",
    "Session Recordings": "Replaying visitor sessions; cases cover recording capture, privacy masking and rage-click detection.",
    "SmartCode": "The VWO tracking snippet loaded on the site; cases cover data collection.",
    "Split URL Testing": "Experiments where each variation is served from its own URL; cases cover split-URL experiment setup.",
    "Surveys": "On-site visitor feedback; cases cover NPS scoring and response export.",
    "User Management": "Workspace users and access; cases cover inviting users, role permissions, deactivation and SSO login.",
}


def render_glossary() -> str:
    lines = ["VWO module glossary", "", VWO_OVERVIEW.strip(), "", "Modules in the corpus:"]
    for module in sorted(MODULE_GLOSSARY):
        lines.append(f"- {module}: {MODULE_GLOSSARY[module]}")
    return "\n".join(lines)
