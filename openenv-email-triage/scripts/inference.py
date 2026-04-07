"""Baseline inference script using the OpenAI API client.
Reads API credentials from HF_TOKEN environment variable.
"""
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI
from email_triage import EmailTriageEnv
from email_triage.models import Action, ActionType, EmailCategory, Department


def get_client() -> OpenAI:
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN environment variable not set")
    return OpenAI(
        base_url="https://api-inference.huggingface.co/v1/",
        api_key=token,
    )


SYSTEM_PROMPT = """You are an email triage assistant. You will receive an inbox of emails and must process each one.

For each email, you can take these actions:
- classify: Assign a category (spam, important, newsletter, personal, urgent)
- prioritize: Assign priority 1-5 (5=most urgent)
- route: Route to department (sales, support, engineering, hr, management, general)
- respond: Draft a professional response
- flag: Flag with a reason
- skip: Skip the email
- done: Signal you're finished processing all emails

Respond with a JSON array of actions. Each action object has:
{
  "action_type": "classify|prioritize|route|respond|flag|skip|done",
  "email_id": "the email id",
  "category": "spam|important|newsletter|personal|urgent" (if classifying),
  "priority": 1-5 (if prioritizing),
  "department": "sales|support|engineering|hr|management|general" (if routing),
  "response_text": "your response" (if responding),
  "flag_reason": "reason" (if flagging)
}

Process ALL emails before sending a "done" action as the last item."""


def format_inbox(observation) -> str:
    lines = [f"Task: {observation.task_description}\n", "=== INBOX ===\n"]
    for email in observation.inbox:
        if email.id not in observation.processed:
            lines.append(f"[{email.id}] From: {email.sender}")
            lines.append(f"  Subject: {email.subject}")
            lines.append(f"  Body: {email.body}")
            if email.attachments:
                lines.append(f"  Attachments: {', '.join(email.attachments)}")
            lines.append(f"  Time: {email.timestamp}")
            lines.append("")
    lines.append(f"Time remaining: {observation.time_remaining}")
    return "\n".join(lines)


def parse_actions(response_text: str) -> list[Action]:
    """Parse LLM response into Action objects."""
    # Extract JSON from response
    text = response_text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON array in the text
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
        else:
            return [Action(action_type=ActionType.DONE)]

    if not isinstance(data, list):
        data = [data]

    actions = []
    for item in data:
        try:
            # Convert string enums
            if "action_type" in item:
                item["action_type"] = ActionType(item["action_type"])
            if "category" in item and item["category"]:
                item["category"] = EmailCategory(item["category"])
            if "department" in item and item["department"]:
                item["department"] = Department(item["department"])
            actions.append(Action(**item))
        except (ValueError, KeyError) as e:
            print(f"  Warning: Skipping malformed action: {e}")
            continue

    return actions if actions else [Action(action_type=ActionType.DONE)]


def run_task(client: OpenAI, task_id: str, model: str = "meta-llama/Llama-3.1-8B-Instruct") -> float:
    """Run a single task and return the final score."""
    print(f"\n{'='*60}")
    print(f"Running task: {task_id}")
    print(f"{'='*60}")

    env = EmailTriageEnv(task_id=task_id)
    obs = env.reset()

    inbox_text = format_inbox(obs)
    print(f"Inbox has {len(obs.inbox)} emails")

    # Single-turn: send full inbox, get all actions
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": inbox_text},
        ],
        max_tokens=2000,
        temperature=0.1,
    )

    reply = response.choices[0].message.content
    print(f"\nLLM Response (first 500 chars):\n{reply[:500]}")

    actions = parse_actions(reply)
    print(f"\nParsed {len(actions)} actions")

    # Execute all actions
    final_score = 0.0
    for action in actions:
        obs, reward, done, info = env.step(action)
        print(f"  Step {info.get('step', '?')}: {action.action_type.value} on {action.email_id} -> reward={reward.score:.3f} | {reward.message}")
        if done:
            final_score = info.get("final_score", reward.score)
            break

    # If agent didn't send DONE, force it
    if not done:
        _, reward, _, info = env.step(Action(action_type=ActionType.DONE))
        final_score = info.get("final_score", reward.score)

    print(f"\nFinal score for {task_id}: {final_score:.4f}")
    return final_score


def main():
    model = os.environ.get("MODEL_ID", "meta-llama/Llama-3.1-8B-Instruct")
    print(f"Using model: {model}")

    client = get_client()
    tasks = ["easy_classify", "medium_prioritize", "hard_respond"]
    scores = {}

    for task_id in tasks:
        try:
            scores[task_id] = run_task(client, task_id, model=model)
        except Exception as e:
            print(f"Error on {task_id}: {e}")
            scores[task_id] = 0.0

    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}")
    for task_id, score in scores.items():
        print(f"  {task_id}: {score:.4f}")
    avg = sum(scores.values()) / len(scores)
    print(f"  Average: {avg:.4f}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
