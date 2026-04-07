import gradio as gr
from email_triage.env import OpenEnv
from email_triage.models import Action

env = OpenEnv()

def run(level, user_input):
    obs = env.reset(level)
    action = Action(response=user_input)

    _, reward, _, _ = env.step(action)

    return f"Task: {obs.text}\nScore: {reward.score}"

gr.Interface(
    fn=run,
    inputs=[
        gr.Dropdown(["easy", "medium", "hard"], label="Select Task"),
        gr.Textbox(label="Your Answer")
    ],
    outputs="text",
    title="OpenEnv Email Triage"
).launch()