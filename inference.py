"""
Inference script for Field Tech Visual Assistant.
"""

import os
import sys
import json
import textwrap
from openai import OpenAI

# ============================================================================
# GLOBAL CLIENT
# ============================================================================
client = None

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================
API_KEY = os.getenv("API_KEY") 
API_BASE_URL = os.getenv("API_BASE_URL") 
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

FIELD_TECH_TASK = os.getenv("FIELD_TECH_TASK", "cable_id_basic")
MAX_STEPS = 3
TEMPERATURE = 0.2
MAX_TOKENS = 1000

# ============================================================================
# INITIALIZE CLIENT
# ============================================================================
def init_client():
    global client
    try:
        client = OpenAI(
            api_key=API_KEY,
            base_url=API_BASE_URL
        )
    except Exception as e:
        print(f"[ERROR] Failed to initialize: {e}", file=sys.stderr)
        client = None

# ============================================================================
# PROMPT ENGINEERING
# ============================================================================
def build_system_prompt(task_difficulty: str) -> str:
    base_prompt = textwrap.dedent("""
        You are an expert field technician AI with 20+ years of experience in data centers, 
        network infrastructure, and electrical systems. You provide precise technical guidance.

        CRITICAL RULES:
        1. Read visual context carefully
        2. Answer with EXACT identifiers
        3. List ALL errors for diagnostics
        4. Never guess
    """).strip()

    if task_difficulty == "easy":
        base_prompt += "\n\nFocus on identifying correct cable."
    elif task_difficulty == "medium":
        base_prompt += "\n\nFocus on selecting correct port."
    elif task_difficulty == "hard":
        base_prompt += "\n\nList ALL wiring errors carefully."

    return base_prompt


def build_user_prompt(observation: dict, step: int, history: list = None) -> str:
    prompt = f"""
SCENARIO: {observation['scenario']}

VISUAL:
{observation['visual_context']}

QUESTION:
{observation['question']}

ATTEMPT {step}/{MAX_STEPS}

ANSWER:
""".strip()

    if history:
        prompt += "\n\nPrevious attempts:\n" + "\n".join(history[-2:])

    return prompt

# ============================================================================
# LLM CALL
# ============================================================================
def get_llm_response(system_prompt: str, user_prompt: str) -> str:
    if client is None:
        return "error"

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[DEBUG] LLM request failed: {e}", file=sys.stderr)
        return "error"

# ============================================================================
# MAIN INFERENCE
# ============================================================================
def run_inference(env_url: str = "http://localhost:7860"):
    import requests

    print(f"[START] task={FIELD_TECH_TASK} env=field_tech_assistant model={MODEL_NAME}")
    sys.stdout.flush()

    try:
        reset = requests.post(f"{env_url}/reset", json={"task_id": FIELD_TECH_TASK}, timeout=30)

        if reset.status_code != 200:
            print("[END] success=false steps=0 score=0.01 rewards=")
            return

        data = reset.json()
        observation = data["observation"]
        task_info = data["info"]

        system_prompt = build_system_prompt(task_info.get("difficulty", "medium"))

        step = 0
        done = False
        rewards = []
        history = []

        while not done and step < MAX_STEPS:
            step += 1

            user_prompt = build_user_prompt(observation, step, history)
            action = get_llm_response(system_prompt, user_prompt)

            res = requests.post(f"{env_url}/step", json={"action": action}, timeout=30)
            step_data = res.json()

            observation = step_data["observation"]
            reward = step_data["reward"]["score"]
            if reward <= 0:
                reward = 0.01
            elif reward >= 1:
                reward = 0.99
                
            done = step_data["done"]

            rewards.append(reward)

            print(f"[STEP] step={step} action={action[:50]} reward={reward:.2f} done={str(done).lower()} error=null")
            sys.stdout.flush()

            history.append(f"{action} -> {reward:.2f}")

        final_score = rewards[-1] if rewards else 0.01
        if final_score <= 0:
            final_score = 0.01
        elif final_score >= 1:
            final_score = 0.99
            
        success = final_score >= 0.75

        print(f"[END] success={str(success).lower()} steps={step} score={final_score:.3f} rewards={','.join(map(str,rewards))}")
        sys.stdout.flush()

    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        print(f"[END] success=false steps=0 score=0.01 rewards=")

# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    init_client()

    if not API_KEY or not API_BASE_URL:
        print("[WARN] Missing API_KEY or API_BASE_URL", file=sys.stderr)

    env_url = os.getenv("ENV_URL", "http://localhost:7860")
    tasks = [
    "cable_id_basic",
    "cable_id_power",
    "port_select_basic"
    ]

    for task in tasks:
        os.environ["FIELD_TECH_TASK"] = task
        run_inference(env_url)