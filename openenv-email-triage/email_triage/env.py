"""OpenEnv-compliant Email Triage Environment."""
from __future__ import annotations
import copy
from typing import Any

from .models import Observation, Action, ActionType, Reward, EmailMessage
from .data import get_easy_emails, get_medium_emails, get_hard_emails
from .graders import grade_classification, grade_prioritization, grade_full_triage


TASK_CONFIGS = {
    "easy_classify": {
        "description": "Classify each email into: spam, important, newsletter, or personal.",
        "emails_fn": get_easy_emails,
        "grader_fn": grade_classification,
        "time_budget": 100.0,
    },
    "medium_prioritize": {
        "description": "Classify emails, assign priority (1-5), and route to the correct department.",
        "emails_fn": get_medium_emails,
        "grader_fn": grade_prioritization,
        "time_budget": 150.0,
    },
    "hard_respond": {
        "description": "Full triage: classify, prioritize, route, draft responses for emails that need them, and flag urgent items.",
        "emails_fn": get_hard_emails,
        "grader_fn": grade_full_triage,
        "time_budget": 200.0,
    },
}

# Cost per action type (deducted from time_remaining)
ACTION_COSTS = {
    ActionType.CLASSIFY: 2.0,
    ActionType.PRIORITIZE: 3.0,
    ActionType.ROUTE: 2.0,
    ActionType.RESPOND: 10.0,
    ActionType.FLAG: 1.0,
    ActionType.SKIP: 1.0,
    ActionType.DONE: 0.0,
}


class EmailTriageEnv:
    """OpenEnv-compliant environment for email triage tasks."""

    def __init__(self, task_id: str = "easy_classify"):
        if task_id not in TASK_CONFIGS:
            raise ValueError(f"Unknown task: {task_id}. Choose from {list(TASK_CONFIGS.keys())}")
        self.task_id = task_id
        self._config = TASK_CONFIGS[task_id]
        self._emails: list[EmailMessage] = []
        self._actions: list[Action] = []
        self._processed: list[str] = []
        self._current_index: int = 0
        self._time_remaining: float = self._config["time_budget"]
        self._done: bool = False
        self._step_count: int = 0
        self._cumulative_reward: float = 0.0

    def reset(self) -> Observation:
        """Reset the environment and return the initial observation."""
        self._emails = self._config["emails_fn"]()
        # Strip ground truth from observations
        self._actions = []
        self._processed = []
        self._current_index = 0
        self._time_remaining = self._config["time_budget"]
        self._done = False
        self._step_count = 0
        self._cumulative_reward = 0.0
        return self._get_observation()

    def step(self, action: Action) -> tuple[Observation, Reward, bool, dict[str, Any]]:
        """Execute an action and return (observation, reward, done, info)."""
        if self._done:
            return self._get_observation(), Reward(score=0.0, message="Episode already done."), True, {}

        self._step_count += 1
        self._actions.append(action)

        # Deduct time
        cost = ACTION_COSTS.get(action.action_type, 5.0)
        self._time_remaining -= cost

        # Process action
        step_reward = 0.0
        message = ""

        if action.action_type == ActionType.DONE:
            self._done = True
            final_score, breakdown = self._config["grader_fn"](self._emails, self._actions)
            return (
                self._get_observation(),
                Reward(score=final_score, breakdown=breakdown, message="Episode complete."),
                True,
                {"final_score": final_score, "breakdown": breakdown},
            )

        if action.action_type == ActionType.SKIP:
            if action.email_id not in self._processed:
                self._processed.append(action.email_id)
            message = f"Skipped email {action.email_id}."
        else:
            # Incremental reward for taking meaningful actions
            email = next((e for e in self._emails if e.id == action.email_id), None)
            if email:
                if action.email_id not in self._processed:
                    self._processed.append(action.email_id)

                if action.action_type == ActionType.CLASSIFY:
                    if action.category == email.ground_truth_category:
                        step_reward = 0.1
                        message = f"Correct classification for {email.id}!"
                    else:
                        step_reward = 0.02  # Small reward for attempting
                        message = f"Incorrect classification for {email.id}."

                elif action.action_type == ActionType.PRIORITIZE:
                    if email.ground_truth_priority is not None and action.priority is not None:
                        diff = abs(action.priority - email.ground_truth_priority)
                        step_reward = max(0, 0.08 - diff * 0.02)
                        message = f"Priority set for {email.id} (off by {diff})."

                elif action.action_type == ActionType.ROUTE:
                    if action.department == email.ground_truth_department:
                        step_reward = 0.08
                        message = f"Correct routing for {email.id}!"
                    else:
                        step_reward = 0.01
                        message = f"Incorrect routing for {email.id}."

                elif action.action_type == ActionType.RESPOND:
                    step_reward = 0.05 if action.response_text and len(action.response_text) > 20 else 0.01
                    message = f"Response drafted for {email.id}."

                elif action.action_type == ActionType.FLAG:
                    if email.ground_truth_priority and email.ground_truth_priority >= 4:
                        step_reward = 0.06
                        message = f"Correctly flagged urgent email {email.id}."
                    else:
                        step_reward = -0.02
                        message = f"Unnecessarily flagged {email.id}."
            else:
                message = f"Email {action.email_id} not found."
                step_reward = -0.05

        # Penalize running out of time
        if self._time_remaining <= 0:
            self._done = True
            step_reward -= 0.1
            message += " Time expired!"

        # Penalize infinite loops (too many steps)
        if self._step_count > len(self._emails) * 10:
            self._done = True
            step_reward -= 0.2
            message += " Too many steps - possible infinite loop."

        self._cumulative_reward += max(0, step_reward)
        reward = Reward(
            score=max(0.0, min(1.0, step_reward)),
            breakdown={"step_reward": step_reward, "cumulative": self._cumulative_reward},
            message=message,
        )

        info = {
            "step": self._step_count,
            "time_remaining": self._time_remaining,
            "processed_count": len(self._processed),
            "total_emails": len(self._emails),
        }

        return self._get_observation(), reward, self._done, info

    def state(self) -> dict[str, Any]:
        """Return the full internal state."""
        return {
            "task_id": self.task_id,
            "step_count": self._step_count,
            "done": self._done,
            "time_remaining": self._time_remaining,
            "processed": list(self._processed),
            "actions_taken": [a.model_dump() for a in self._actions],
            "cumulative_reward": self._cumulative_reward,
            "total_emails": len(self._emails),
        }

    def _get_observation(self) -> Observation:
        """Build observation with ground truth stripped."""
        safe_emails = []
        for e in self._emails:
            clean = EmailMessage(
                id=e.id, sender=e.sender, subject=e.subject, body=e.body,
                timestamp=e.timestamp, attachments=e.attachments,
            )
            safe_emails.append(clean)

        return Observation(
            inbox=safe_emails,
            current_email_index=min(self._current_index, len(safe_emails) - 1),
            processed=list(self._processed),
            time_remaining=self._time_remaining,
            task_id=self.task_id,
            task_description=self._config["description"],
        )
