"""
Field Tech Visual Assistant Environment.

An OpenEnv-compliant RL environment for training AI agents to assist field technicians
with visual technical tasks like cable identification, port selection, and wiring diagnosis.
"""

import json
from typing import Optional, Dict, Any, List
from models import FieldTechAction, FieldTechObservation, FieldTechReward


class FieldTechEnv:
    """
    OpenEnv environment simulating field technician visual assistance tasks.
    
    Tasks:
    - Task 1 (Easy): Cable Identification - Identify correct cable type
    - Task 2 (Medium): Port Selection - Select correct port from rack
    - Task 3 (Hard): Wiring Diagnosis - Diagnose multiple wiring errors
    """
    
    # Task definitions
    TASKS = {
        "cable_id_basic": {
            "id": "cable_id_basic",
            "difficulty": "easy",
            "name": "Cable Identification - Basic",
            "scenario": "Data center cable installation",
            "visual_context": "You see three cables on the workbench: Cable A (black, rectangular connector with 19 pins), Cable B (white, oval connector with USB-C shape), Cable C (blue, RJ45 connector with 8 pins)",
            "question": "Which cable should I use to connect the server to the network switch?",
            "correct_answer": "cable c",
            "correct_variations": ["c", "cable c", "rj45", "blue cable", "the blue one", "cable with rj45"],
            "explanation": "Cable C (RJ45/Ethernet cable) is correct for network connections"
        },
        "cable_id_power": {
            "id": "cable_id_power",
            "difficulty": "easy",
            "name": "Cable Identification - Power",
            "scenario": "Server rack power setup",
            "visual_context": "You see four cables: Cable A (standard AC power cord with 3 prongs), Cable B (thin cable with USB connector), Cable C (thick cable with C13 connector), Cable D (fiber optic cable, orange)",
            "question": "Which cable should I use to power the PDU (Power Distribution Unit)?",
            "correct_answer": "cable a",
            "correct_variations": ["a", "cable a", "ac power", "3 prong", "power cord", "standard power"],
            "explanation": "Cable A (standard AC power cord) is correct for PDU power"
        },
        "port_select_basic": {
            "id": "port_select_basic",
            "difficulty": "medium",
            "name": "Port Selection - Management Interface",
            "scenario": "Network switch initial configuration",
            "visual_context": "You see a 24-port network switch. Ports 1-20 are green (labeled 'DATA'), ports 21-23 are yellow (labeled 'UPLINK'), port 24 is blue (labeled 'MGMT'). You have a laptop and need to configure the switch for the first time.",
            "question": "Which port number should I connect my laptop to for initial configuration?",
            "correct_answer": "24",
            "correct_variations": ["24", "port 24", "mgmt", "management", "blue port", "the blue one"],
            "explanation": "Port 24 (MGMT - Management port) is correct for initial configuration"
        },
        "port_select_uplink": {
            "id": "port_select_uplink",
            "difficulty": "medium",
            "name": "Port Selection - Uplink Connection",
            "scenario": "Connecting switch to core router",
            "visual_context": "You see Switch A (access switch) with 48 ports: Ports 1-44 are labeled 'ACCESS', Ports 45-46 are labeled 'UPLINK 10G', Ports 47-48 are labeled 'STACK'. You need to connect this to the core router which requires 10Gbps connection.",
            "question": "Which port should I use to connect to the core router?",
            "correct_answer": "45 or 46",
            "correct_variations": ["45", "46", "port 45", "port 46", "uplink", "10g", "45 or 46"],
            "explanation": "Ports 45 or 46 (10G UPLINK ports) are correct for high-speed core router connection"
        },
        "wiring_diag_server": {
            "id": "wiring_diag_server",
            "difficulty": "hard",
            "name": "Wiring Diagnosis - Server Rack",
            "scenario": "Troubleshooting non-functional server rack",
            "visual_context": "You see Server Rack B with 4 servers. Server 1: Power connected to Port A1 (correct), Network connected to Port 24 (should be Port 12). Server 2: Power connected to Port B3 (correct), Network connected to Port 15 (correct). Server 3: Power connected to Port A2 (should be Port C1), Network connected to Port 18 (correct). Server 4: No power connected (should be Port C2), Network connected to Port 22 (should be Port 20).",
            "question": "List all wiring errors you can identify in this rack.",
            "correct_answer": "server 1 network wrong, server 3 power wrong, server 4 missing power, server 4 network wrong",
            "errors": [
                "server 1 network",
                "server 3 power", 
                "server 4 power",
                "server 4 network"
            ],
            "explanation": "4 errors: Server 1 network on wrong port, Server 3 power on wrong PDU, Server 4 missing power, Server 4 network on wrong port"
        },
        "wiring_diag_patch": {
            "id": "wiring_diag_patch",
            "difficulty": "hard",
            "name": "Wiring Diagnosis - Patch Panel",
            "scenario": "Troubleshooting office network connectivity issues",
            "visual_context": "You see Patch Panel A (Top) and Switch B (Bottom). Connections: Panel Port 1 → Switch Port 5 (should be Port 1), Panel Port 2 → Switch Port 2 (correct), Panel Port 3 → not connected (should be Port 3), Panel Port 4 → Switch Port 7 (should be Port 4), Panel Port 5 → Switch Port 5 (should be Port 5, but Port 5 already used by Panel Port 1).",
            "question": "Identify all misconnections in this patch panel setup.",
            "correct_answer": "port 1 wrong, port 3 missing, port 4 wrong, port 5 conflict",
            "errors": [
                "port 1",
                "port 3",
                "port 4",
                "port 5"
            ],
            "explanation": "4 errors: Port 1 connected to wrong switch port, Port 3 not connected, Port 4 on wrong switch port, Port 5 conflict"
        }
    }
    
    def __init__(self, task_id: Optional[str] = None):
        """Initialize the environment with a specific task.
        
        Args:
            task_id: ID of the task to run. If None, uses first task.
        """
        self.task_id = task_id or "cable_id_basic"
        self.task_config = self.TASKS.get(self.task_id)
        if not self.task_config:
            raise ValueError(f"Unknown task_id: {task_id}")
            
        self.current_step = 0
        self.done = False
        self.last_action = None
        self.last_reward = 0.0
        self.total_reward = 0.0
        self.max_steps = 3  # Allow up to 3 attempts
        
    def reset(self) -> Dict[str, Any]:
        """Reset the environment to initial state.
        
        Returns:
            Dict with 'observation' key containing FieldTechObservation
        """
        self.current_step = 0
        self.done = False
        self.last_action = None
        self.last_reward = 0.0
        self.total_reward = 0.0
        
        observation = FieldTechObservation(
            task_id=self.task_config["id"],
            scenario=self.task_config["scenario"],
            visual_context=self.task_config["visual_context"],
            question=self.task_config["question"],
            step=self.current_step
        )
        
        return {
            "observation": observation.model_dump(),
            "info": {
                "difficulty": self.task_config["difficulty"],
                "task_id": self.task_id,
                "max_steps": self.max_steps
            }
        }
    
    def _grade_response(self, response: str) -> tuple[float, bool, str]:
        """Grade the agent's response based on task type.
        
        Args:
            response: Agent's response string
            
        Returns:
            Tuple of (score, is_correct, feedback)
        """
        response_lower = response.lower().strip()
        task_id = self.task_config["id"]
        
        # Easy tasks: Cable identification
        if task_id.startswith("cable_id"):
            correct_variations = self.task_config["correct_variations"]
            
            # Check for exact match or variation match
            # Use word boundaries to avoid false positives (e.g., "c" in "cable")
            is_correct = False
            for variation in correct_variations:
                # For single-letter variations, check as standalone word
                if len(variation) == 1:
                    import re
                    if re.search(r'\b' + re.escape(variation) + r'\b', response_lower):
                        is_correct = True
                        break
                # For longer variations, use substring match
                elif variation in response_lower:
                    is_correct = True   
                    break
            
            if is_correct:
                return 0.99, True, f"Correct! {self.task_config['explanation']}"
            
            # Partial credit for mentioning correct category but wrong specific
            if "cable" in response_lower:
                return 0.3, False, "You identified it as a cable, but selected the wrong type"
            
            return 0.01, False, f"Incorrect. {self.task_config['explanation']}"
        
        # Medium tasks: Port selection
        elif task_id.startswith("port_select"):
            correct_variations = self.task_config["correct_variations"]
            
            # Check if any correct variation is in response
            if any(variation in response_lower for variation in correct_variations):
                return 0.99, True, f"Correct! {self.task_config['explanation']}"
            
            # Partial credit for mentioning port but wrong number
            if "port" in response_lower or any(char.isdigit() for char in response_lower):
                # Extract any numbers from response
                numbers = [int(s) for s in response_lower.split() if s.isdigit()]
                if numbers:
                    # Give partial credit if close to correct port
                    correct_port = int(self.task_config["correct_answer"].split()[0])
                    if any(abs(num - correct_port) <= 2 for num in numbers):
                        return 0.5, False, "You're close, but that's not the correct port"
                return 0.2, False, "You mentioned a port number, but it's not correct"
            
            return 0.01, False, f"Incorrect. {self.task_config['explanation']}"
        
        # Hard tasks: Wiring diagnosis
        elif task_id.startswith("wiring_diag"):
            errors = self.task_config["errors"]
            errors_found = []
            
            # Check which errors were mentioned
            for error in errors:
                if error.lower() in response_lower:
                    errors_found.append(error)
            
            # Score based on how many errors identified
            raw_score = len(errors_found) / len(errors)
            score = max(0.01, min(0.99, raw_score))
            
            if score >= 0.75:  # Found 3+ out of 4 errors
                return score, True, f"Excellent diagnosis! You found {len(errors_found)}/{len(errors)} errors. {self.task_config['explanation']}"
            elif score >= 0.5:  # Found 2+ out of 4 errors
                return score, False, f"Good start. You found {len(errors_found)}/{len(errors)} errors, but there are more."
            elif score > 0:  # Found at least 1 error
                return score, False, f"You identified some issues ({len(errors_found)}/{len(errors)}), but missed several critical errors."
            else:
                return 0.01, False, f"Incorrect. {self.task_config['explanation']}"
        
        return 0.01, False, "Unable to evaluate response"
    
        
    
    def step(self, action: FieldTechAction) -> Dict[str, Any]:
        """Execute one step in the environment.
        
        Args:
            action: FieldTechAction containing agent's response
            
        Returns:
            Dict with 'observation', 'reward', 'done', 'info' keys
        """
        if self.done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")
        
        self.current_step += 1
        self.last_action = action.response
        
        # Grade the response
        score, is_correct, feedback = self._grade_response(action.response)
        
        # Create reward
        reward = FieldTechReward(
            score=score,
            correct=is_correct,
            feedback=feedback
        )
        
        self.last_reward = score
        self.total_reward += score
        
        # Episode ends if correct or max steps reached
        self.done = is_correct or self.current_step >= self.max_steps
        
        # Create observation
        observation = FieldTechObservation(
            task_id=self.task_config["id"],
            scenario=self.task_config["scenario"],
            visual_context=self.task_config["visual_context"],
            question=self.task_config["question"],
            step_number=self.current_step
        )
        
        return {
            "observation": observation.model_dump(),
            "reward": reward.model_dump(),
            "done": self.done,
            "info": {
                "step": self.current_step,
                "is_correct": is_correct,
                "total_reward": self.total_reward,
                "last_action": self.last_action
            }
        }
    
    def state(self) -> Dict[str, Any]:
        """Get current environment state.
        
        Returns:
            Dict containing current state information
        """
        return {
            "task_id": self.task_id,
            "current_step": self.current_step,
            "done": self.done,
            "total_reward": self.total_reward,
            "last_action": self.last_action,
            "last_reward": self.last_reward
        }
    
    @classmethod
    def get_all_tasks(cls) -> List[Dict[str, str]]:
        """Get list of all available tasks.
        
        Returns:
            List of task metadata dictionaries
        """
        return [
            {
                "id": task_id,
                "name": task_config["name"],
                "difficulty": task_config["difficulty"]
            }
            for task_id, task_config in cls.TASKS.items()
        ]


# Task grader functions (can be called independently for evaluation)

def grade_cable_identification(response: str, task_id: str) -> float:
    """Grade cable identification task.
    
    Args:
        response: Agent's response
        task_id: Task identifier
        
    Returns:
        Score between 0.0 and 1.0
    """
    env = FieldTechEnv(task_id=task_id)
    score, _, _ = env._grade_response(response)
    return score


def grade_port_selection(response: str, task_id: str) -> float:
    """Grade port selection task.
    
    Args:
        response: Agent's response
        task_id: Task identifier
        
    Returns:
        Score between 0.0 and 1.0
    """
    env = FieldTechEnv(task_id=task_id)
    score, _, _ = env._grade_response(response)
    return score


def grade_wiring_diagnosis(response: str, task_id: str) -> float:
    """Grade wiring diagnosis task.
    
    Args:
        response: Agent's response
        task_id: Task identifier
        
    Returns:
        Score between 0.0 and 1.0
    """
    env = FieldTechEnv(task_id=task_id)
    score, _, _ = env._grade_response(response)
    return score
