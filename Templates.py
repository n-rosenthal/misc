"""
    experiments with Python 3.14's template strings (t-strings)
"""

from string.templatelib import Template, Interpolation, convert

def render_md(template: Template) -> str:
    """
    Render a template string as Markdown.

    The template string is iterated and each part is processed.
    Strings are appended as is, while Interpolations are converted
    and formatted according to their conversion and format specification.
    Any other part type raises a TypeError.

    :param template: The template string to render.
    :return: The rendered Markdown string.
    """
    parts = []
    # The template can be iterated – it yields strings and Interpolations in order.
    # Empty strings are skipped, which is usually what we want.
    for part in template:
        if isinstance(part, str):
            parts.append(part)
        elif isinstance(part, Interpolation):
            # Apply conversion (if any)
            value = convert(part.value, part.conversion)
            # Apply format specification (if any)
            if part.format_spec:
                value = format(value, part.format_spec)
            parts.append(str(value))
        else:
            raise TypeError(f"Unexpected part type: {type(part)}")
    return ''.join(parts)

from datetime import date

def journal_entry(entry_date: date, mood: str, content: str) -> str:
    template = """
# Journal: {entry_date}

**Mood:** {mood}

{content}
"""
    return render_md(template)

# Usage
entry = journal_entry(date.today(), "😊 productive", "Worked on the Markdown generator.")
print(entry)

def daily_log(day: date, activities: list[tuple[str, str]]) -> str:
    # activities: list of (description, duration)
    template = """
## {day}

### Completed
{activities}
"""
    return render_md(template)

# But we need to format the activities as a bullet list. 
# We could pre‑format them before interpolation:
def format_activities(activities):
    return '\n'.join(f"- {desc} ({dur})" for desc, dur in activities)

log = daily_log(
    date.today(),
    format_activities([("Morning run", "30 min"), ("Read", "1h")])
)

def workout_log(exercises: list[dict]) -> str:
    # Each exercise: {"name": str, "sets": int, "reps": int, "weight": str}
    template = """
## Workout – {date.today()}

{exercises}
"""
    # Pre‑format exercises as a Markdown table
    rows = ["| Exercise | Sets | Reps | Weight |",
            "|----------|------|------|--------|"]
    for ex in exercises:
        rows.append(f"| {ex['name']} | {ex['sets']} | {ex['reps']} | {ex['weight']} |")
    exercises_md = "\n".join(rows)
    return render_md(template)  # exercises is now a string









# --- advanced

import re

def escape_markdown(text: str) -> str:
    # Escape characters that have special meaning in Markdown
    return re.sub(r'([\\`*_{}[\]()#+\-.!])', r'\\\1', text)

def render_md_ext(template: Template) -> str:
    parts = []
    for part in template:
        if isinstance(part, str):
            parts.append(part)
        elif isinstance(part, Interpolation):
            # Handle built‑in conversions
            if part.conversion in ('a', 'r', 's'):
                value = convert(part.value, part.conversion)
            elif part.conversion == 'm':
                value = escape_markdown(str(part.value))
            elif part.conversion is None:
                value = part.value
            else:
                raise ValueError(f"Unsupported conversion: {part.conversion}")

            if part.format_spec:
                value = format(value, part.format_spec)
            parts.append(str(value))
    return ''.join(parts)

user_input = "**important** *text*"
safe = "User wrote: {user_input!m}"
print(render_md_ext(safe))  # User wrote: \*\*important\*\* \*text\*