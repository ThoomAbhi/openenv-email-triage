"""Programmatic graders for each task. Each returns a score between 0.0 and 1.0."""
from __future__ import annotations
from .models import EmailMessage, Action, ActionType


def grade_classification(emails: list[EmailMessage], actions: list[Action]) -> tuple[float, dict]:
    """Grade Task 1 (Easy): Email classification accuracy."""
    classify_actions = {a.email_id: a for a in actions if a.action_type == ActionType.CLASSIFY}
    
    correct = 0
    total = len(emails)
    details = {}
    
    for email in emails:
        action = classify_actions.get(email.id)
        if action and action.category == email.ground_truth_category:
            correct += 1
            details[email.id] = {"correct": True, "expected": email.ground_truth_category, "got": action.category}
        else:
            got = action.category if action else "not_classified"
            details[email.id] = {"correct": False, "expected": email.ground_truth_category, "got": got}
    
    # Penalize unprocessed emails
    processed = len(classify_actions)
    completeness = processed / total if total > 0 else 0
    accuracy = correct / total if total > 0 else 0
    
    score = 0.7 * accuracy + 0.3 * completeness
    return score, {"accuracy": accuracy, "completeness": completeness, "details": details}


def grade_prioritization(emails: list[EmailMessage], actions: list[Action]) -> tuple[float, dict]:
    """Grade Task 2 (Medium): Priority + routing accuracy."""
    prioritize_actions = {a.email_id: a for a in actions if a.action_type == ActionType.PRIORITIZE}
    route_actions = {a.email_id: a for a in actions if a.action_type == ActionType.ROUTE}
    classify_actions = {a.email_id: a for a in actions if a.action_type == ActionType.CLASSIFY}
    
    total = len([e for e in emails if e.ground_truth_priority is not None])
    priority_score = 0
    route_score = 0
    classify_score = 0
    
    for email in emails:
        # Classification (same as easy)
        ca = classify_actions.get(email.id)
        if ca and ca.category == email.ground_truth_category:
            classify_score += 1
        
        # Priority scoring (partial credit for close answers)
        pa = prioritize_actions.get(email.id)
        if pa and pa.priority is not None and email.ground_truth_priority is not None:
            diff = abs(pa.priority - email.ground_truth_priority)
            priority_score += max(0, 1.0 - diff * 0.25)
        
        # Routing
        ra = route_actions.get(email.id)
        if ra and ra.department == email.ground_truth_department:
            route_score += 1
    
    n = max(total, 1)
    breakdown = {
        "classification": classify_score / len(emails),
        "priority": priority_score / n,
        "routing": route_score / n,
    }
    score = 0.3 * breakdown["classification"] + 0.4 * breakdown["priority"] + 0.3 * breakdown["routing"]
    return score, breakdown


def grade_response_quality(text: str, key_points: list[str]) -> float:
    """Simple keyword-based response quality check."""
    if not text or len(text.strip()) < 10:
        return 0.0
    text_lower = text.lower()
    
    # Check key points coverage
    covered = sum(1 for kp in key_points if any(word in text_lower for word in kp.split()))
    coverage = covered / len(key_points) if key_points else 0.5
    
    # Check response isn't too short or too long
    words = len(text.split())
    length_score = 1.0 if 20 <= words <= 200 else 0.5 if 10 <= words <= 300 else 0.2
    
    # Check professionalism (basic heuristics)
    prof_markers = ["thank", "please", "regards", "sincerely", "appreciate", "apolog"]
    prof_score = min(1.0, sum(0.3 for m in prof_markers if m in text_lower))
    
    return 0.5 * coverage + 0.3 * length_score + 0.2 * prof_score


def grade_full_triage(emails: list[EmailMessage], actions: list[Action]) -> tuple[float, dict]:
    """Grade Task 3 (Hard): Full triage including responses."""
    # Get medium scores first
    medium_score, medium_breakdown = grade_prioritization(emails, actions)
    
    # Grade responses
    respond_actions = {a.email_id: a for a in actions if a.action_type == ActionType.RESPOND}
    response_emails = [e for e in emails if e.requires_response]
    
    response_score = 0
    response_details = {}
    for email in response_emails:
        ra = respond_actions.get(email.id)
        if ra and ra.response_text:
            q = grade_response_quality(ra.response_text, email.key_points)
            response_score += q
            response_details[email.id] = {"quality": q, "responded": True}
        else:
            response_details[email.id] = {"quality": 0.0, "responded": False}
    
    n_resp = max(len(response_emails), 1)
    avg_response = response_score / n_resp
    
    # Flag scoring - penalize flagging spam as important or missing urgent items
    flag_actions = {a.email_id: a for a in actions if a.action_type == ActionType.FLAG}
    urgent_emails = [e for e in emails if e.ground_truth_priority and e.ground_truth_priority >= 4]
    flagged_urgent = sum(1 for e in urgent_emails if e.id in flag_actions)
    flag_score = flagged_urgent / max(len(urgent_emails), 1)
    
    breakdown = {
        **medium_breakdown,
        "response_quality": avg_response,
        "flag_accuracy": flag_score,
        "response_details": response_details,
    }
    score = 0.4 * medium_score + 0.4 * avg_response + 0.2 * flag_score
    return score, breakdown
