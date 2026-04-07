# OpenEnv Email Triage Environment

An OpenEnv-compliant environment simulating real-world **email triage** tasks. Agents must classify, prioritize, route, and respond to emails across three difficulty levels.

## Motivation

Email triage is a universal real-world task. Knowledge workers spend ~28% of their workday managing email. This environment tests an AI agent's ability to:
- **Understand context** — distinguish spam from urgent requests
- **Make decisions** — prioritize and route appropriately
- **Communicate** — draft professional responses
- **Manage resources** — work within a time budget

## Tasks

| Task ID | Difficulty | Description | Emails |
|---------|-----------|-------------|--------|
| `easy_classify` | Easy | Classify emails into categories (spam, important, newsletter, personal) | 6 |
| `medium_prioritize` | Medium | Classify + assign priority (1-5) + route to correct department | 8 |
| `hard_respond` | Hard | Full triage: classify, prioritize, route, draft responses, flag urgent | 8 |

## Observation Space

| Field | Type | Description |
|-------|------|-------------|
| `inbox` | `list[EmailMessage]` | Emails with sender, subject, body, timestamp, attachments |
| `current_email_index` | `int` | Index of current email |
| `processed` | `list[str]` | IDs of already-processed emails |
| `time_remaining` | `float` | Simulated time budget |
| `task_id` | `str` | Current task identifier |
| `task_description` | `str` | Human-readable task instructions |

## Action Space

| Field | Type | Description |
|-------|------|-------------|
| `action_type` | `enum` | `classify`, `prioritize`, `route`, `respond`, `flag`, `skip`, `done` |
| `email_id` | `str` | Target email ID |
| `category` | `enum?` | `spam`, `important`, `newsletter`, `personal`, `urgent` |
| `priority` | `int?` | 1-5 (5 = most urgent) |
| `department` | `enum?` | `sales`, `support`, `engineering`, `hr`, `management`, `general` |
| `response_text` | `str?` | Draft response content |
| `flag_reason` | `str?` | Reason for flagging |

## Reward Function

Rewards are provided **incrementally** at each step:
- ✅ Correct classification: +0.10
- ✅ Accurate priority: +0.08 (partial credit for close answers)
- ✅ Correct routing: +0.08
- ✅ Quality response: +0.05
- ✅ Correctly flagging urgent: +0.06
- ❌ Wrong classification: +0.02 (attempt credit)
- ❌ Unnecessary flagging: -0.02
- ❌ Nonexistent email: -0.05
- ❌ Time expired: -0.10
- ❌ Too many steps (loop detection): -0.20

Final score (0.0–1.0) is computed by the task-specific grader upon `done`.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

## Usage

### Python API

```python
from email_triage import EmailTriageEnv
from email_triage.models import Action, ActionType, EmailCategory

env = EmailTriageEnv(task_id="easy_classify")
obs = env.reset()

# Classify an email
action = Action(
    action_type=ActionType.CLASSIFY,
    email_id="e1",
    category=EmailCategory.SPAM,
)
obs, reward, done, info = env.step(action)
print(f"Reward: {reward.score}, Message: {reward.message}")

# Finish
obs, reward, done, info = env.step(Action(action_type=ActionType.DONE))
print(f"Final score: {info['final_score']}")
```

### Inference Script

```bash
export HF_TOKEN="your_huggingface_token"
export MODEL_ID="meta-llama/Llama-3.1-8B-Instruct"  # optional, this is default
python scripts/inference.py
```

### Docker

```bash
docker build -t email-triage-env .
docker run -e HF_TOKEN=$HF_TOKEN email-triage-env
```

### OpenEnv Validation

```bash
openenv validate
```

## Baseline Performance

| Task | Llama-3.1-8B | Expected Range |
|------|-------------|---------------|
| `easy_classify` | ~0.75 | 0.6–0.9 |
| `medium_prioritize` | ~0.55 | 0.4–0.7 |
| `hard_respond` | ~0.40 | 0.3–0.6 |

*Scores may vary based on model and API conditions.*

## Project Structure

```
openenv-email-triage/
├── openenv.yaml          # OpenEnv metadata
├── Dockerfile            # Container config
├── requirements.txt      # Python dependencies
├── setup.py              # Package setup
├── README.md             # This file
├── email_triage/
│   ├── __init__.py       # Package exports
│   ├── models.py         # Pydantic models (Observation, Action, Reward)
│   ├── data.py           # Email datasets for each difficulty
│   ├── graders.py        # Programmatic graders (0.0–1.0)
│   └── env.py            # Main environment (step/reset/state)
└── scripts/
    └── inference.py      # Baseline inference with OpenAI API
```

## License

MIT
