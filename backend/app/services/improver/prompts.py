"""
Prompt Templates for Writing Improver Modes.

CRITICAL DIRECTIVES ACROSS ALL MODES:
1. NEVER add new facts, claims, or outside information.
2. NEVER alter technical terminology, names, dates, or numbers.
3. PRESERVE exact placeholder tokens (e.g. __PROTECTED_SPAN_0__) verbatim without editing or moving them out of their logical clauses.
4. Output ONLY the improved text. Do not include commentary, preface, or markdown quotes.
"""

from typing import Dict, Tuple, Optional
from backend.app.models.improver import ImproverMode

BASE_SYSTEM_INSTRUCTIONS = """You are an expert writing improvement engine focused on clarity, flow, readability, and syntactic elegance.
Your task is strictly to polish the user's prose according to the specified style.

MANDATORY EDITORIAL CONSTRAINTS:
1. PRESERVE FACTUAL MEANING: Do NOT add new facts, claims, interpretations, or assumptions.
2. PRESERVE TERMINOLOGY: Keep domain-specific terminology, technical jargon, and named entities intact.
3. PRESERVE PLACEHOLDERS: Tokens matching `__PROTECTED_SPAN_X__` represent verified citations, numbers, units, code, or quotes. You MUST keep every single `__PROTECTED_SPAN_X__` token exactly as written in its proper grammatical position.
4. DIRECT OUTPUT ONLY: Output ONLY the revised text. Do not provide greetings, markdown codeblocks, or explanations.
"""

MODE_TEMPLATES: Dict[ImproverMode, str] = {
    "natural_conversational": """STYLE: Natural and Conversational
- Rephrase stiff, awkward, or bureaucratic wording into fluid, engaging, human-sounding language.
- Vary sentence rhythms with natural transitions.
- Maintain an approachable, engaging cadence while preserving exact meaning and all placeholders.
""",

    "academic_clarity": """STYLE: Academic Clarity
- Optimize for scholarly precision, syntactic cohesion, and objective academic tone.
- Eliminate colloquialisms, redundancies, and vague generalizations.
- Ensure rigorous logical connectivity between clauses while keeping citations and placeholders in their precise grammatical positions.
""",

    "professional": """STYLE: Professional & Executive
- Optimize for crisp business communication, workplace clarity, and executive impact.
- Use direct, active voice where appropriate.
- Eliminate filler phrases and passive ambiguity while preserving all business metrics and placeholders.
""",

    "simple_readable": """STYLE: Simple & Readable
- Optimize for maximum accessibility, plain English, and smooth readability.
- Break up overly dense, convoluted compound sentences into clear, digestible thoughts.
- Use clear everyday vocabulary without dumbing down the core factual meaning or modifying placeholders.
""",

    "concise": """STYLE: Concise & Tight
- Optimize for brevity, removing unnecessary filler words, nominalizations, and repetitive clauses.
- Deliver maximum information density in the fewest words possible.
- Retain every single fact, detail, and placeholder token.
""",

    "formal": """STYLE: Formal & Polished
- Optimize for dignified, traditional, authoritative prose suitable for official publications, legal contexts, or formal correspondence.
- Maintain syntactic dignity and elevated grammatical structure without becoming archaic or verbose.
- Keep all factual anchors and placeholders strictly intact.
"""
}


def get_prompt_for_mode(mode: ImproverMode, text: str, context: str = None) -> Tuple[str, str]:
    """
    Returns (prompt, system_prompt) for the given mode and paragraph text.
    """
    mode_instructions = MODE_TEMPLATES.get(mode, MODE_TEMPLATES["academic_clarity"])
    system_prompt = f"{BASE_SYSTEM_INSTRUCTIONS}\n\n{mode_instructions}"

    prompt_parts = []
    if context:
        prompt_parts.append(f"Preceding context for smooth transition:\n\"{context}\"\n")
    prompt_parts.append(f"Paragraph to improve:\n{text}")

    prompt = "\n".join(prompt_parts)
    return prompt, system_prompt
