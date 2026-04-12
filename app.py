
"""
FastAPI server for Field Tech Visual Assistant OpenEnv environment.
Implements OpenEnv protocol endpoints + Interactive Web UI.
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from env import FieldTechEnv
from models import FieldTechAction, FieldTechObservation, FieldTechReward

# Initialize FastAPI app
app = FastAPI(
    title="Field Tech Visual Assistant",
    description="OpenEnv environment for AI-assisted field technician tasks",
    version="1.0.0"
)

# Global environment instance
env_instance: Optional[FieldTechEnv] = None
current_task_id: Optional[str] = None


class ResetRequest(BaseModel):
    """Request model for environment reset."""
    task_id: Optional[str] = None


class StepRequest(BaseModel):
    """Request model for environment step."""
    action: str


# ============================================================================
# WEB UI - BEAUTIFUL INTERACTIVE INTERFACE
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve interactive web UI."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔧 Field Tech Visual Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .task-selector {
            margin-bottom: 20px;
        }
        
        .task-selector label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        
        select, input, textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s;
        }
        
        select:focus, input:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            margin-top: 10px;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .task-info {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }
        
        .task-info h3 {
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .task-info p {
            margin: 5px 0;
            line-height: 1.6;
        }
        
        .difficulty-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            margin-top: 5px;
        }
        
        .difficulty-easy {
            background: #d4edda;
            color: #155724;
        }
        
        .difficulty-medium {
            background: #fff3cd;
            color: #856404;
        }
        
        .difficulty-hard {
            background: #f8d7da;
            color: #721c24;
        }
        
        .results {
            margin-top: 20px;
        }
        
        .result-item {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
        }
        
        .result-item h4 {
            color: #667eea;
            margin-bottom: 8px;
        }
        
        .result-item pre {
            background: #2d3748;
            color: #68d391;
            padding: 10px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 0.9em;
        }
        
        .score-display {
            font-size: 2em;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
        }
        
        .score-good {
            background: linear-gradient(135deg, #56ab2f 0%, #a8e063 100%);
        }
        
        .score-bad {
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #667eea;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .api-links {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .api-link {
            flex: 1;
            min-width: 150px;
            text-align: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
            text-decoration: none;
            color: #667eea;
            font-weight: 600;
            transition: background 0.3s;
        }
        
        .api-link:hover {
            background: #e9ecef;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-top: 20px;
        }
        
        .stat-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-card h3 {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }
        
        .stat-card .value {
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
        }
        
        footer {
            text-align: center;
            color: white;
            margin-top: 30px;
            padding: 20px;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔧 Field Tech Visual Assistant</h1>
            <p>AI-Powered Assistance for Field Technicians</p>
        </header>
        
        <div class="main-content">
            <!-- Control Panel -->
            <div class="card">
                <h2>🎮 Control Panel</h2>
                
                <div class="task-selector">
                    <label for="taskSelect">Select Task:</label>
                    <select id="taskSelect" onchange="updateTaskInfo()">
                        <option value="cable_id_basic">Cable ID - Basic (Easy)</option>
                        <option value="cable_id_power">Cable ID - Power (Easy)</option>
                        <option value="port_select_basic">Port Selection - MGMT (Medium)</option>
                        <option value="port_select_uplink">Port Selection - Uplink (Medium)</option>
                        <option value="wiring_diag_server">Wiring Diagnosis - Server (Hard)</option>
                        <option value="wiring_diag_patch">Wiring Diagnosis - Patch (Hard)</option>
                    </select>
                </div>
                
                <button onclick="resetEnvironment()">🔄 Reset Environment</button>
                
                <div id="taskInfo" class="task-info" style="display:none;">
                    <h3 id="taskTitle"></h3>
                    <p><strong>Scenario:</strong> <span id="taskScenario"></span></p>
                    <p><strong>Visual Context:</strong> <span id="taskVisual"></span></p>
                    <p><strong>Question:</strong> <span id="taskQuestion"></span></p>
                    <div id="taskDifficulty"></div>
                </div>
                
                <div style="margin-top: 20px;">
                    <label for="actionInput">Your Answer:</label>
                    <input type="text" id="actionInput" placeholder="e.g., Cable C, Port 24, Server 1 network wrong..." />
                    <button onclick="takeStep()" id="stepButton" disabled>🎯 Submit Answer</button>
                </div>
                
                <div class="stats" id="statsPanel" style="display:none;">
                    <div class="stat-card">
                        <h3>Steps</h3>
                        <div class="value" id="stepCount">0</div>
                    </div>
                    <div class="stat-card">
                        <h3>Score</h3>
                        <div class="value" id="currentScore">0.00</div>
                    </div>
                    <div class="stat-card">
                        <h3>Status</h3>
                        <div class="value" id="doneStatus" style="font-size:1.2em;">⏳</div>
                    </div>
                </div>
            </div>
            
            <!-- Results Panel -->
            <div class="card">
                <h2>📊 Results</h2>
                <div id="results">
                    <p style="text-align:center; color:#999; padding:40px;">
                        Select a task and click "Reset Environment" to begin
                    </p>
                </div>
            </div>
        </div>
        
        <!-- API Documentation Links -->
        <div class="card">
            <h2>🔗 API Endpoints</h2>
            <div class="api-links">
                <a href="/docs" class="api-link" target="_blank">📚 API Docs</a>
                <a href="/health" class="api-link" target="_blank">💚 Health Check</a>
                <a href="/state" class="api-link" target="_blank">📍 Current State</a>
            </div>
        </div>
        
        <footer>
            <p>AI | OpenEnv Compliant</p>
            <p> Field technician assistance</p>
        </footer>
    </div>
    
    <script>
        let currentObservation = null;
        let stepCounter = 0;
        let taskData = null;
        
        const taskDescriptions = {
            'cable_id_basic': {
                title: 'Cable Identification - Basic',
                difficulty: 'easy',
                description: 'Identify the correct network cable from visual description'
            },
            'cable_id_power': {
                title: 'Cable Identification - Power',
                difficulty: 'easy',
                description: 'Identify the correct power cable for PDU'
            },
            'port_select_basic': {
                title: 'Port Selection - Management',
                difficulty: 'medium',
                description: 'Select the correct management port on network switch'
            },
            'port_select_uplink': {
                title: 'Port Selection - Uplink',
                difficulty: 'medium',
                description: 'Select the correct uplink port for high-speed connection'
            },
            'wiring_diag_server': {
                title: 'Wiring Diagnosis - Server Rack',
                difficulty: 'hard',
                description: 'Diagnose multiple wiring errors in server rack setup'
            },
            'wiring_diag_patch': {
                title: 'Wiring Diagnosis - Patch Panel',
                difficulty: 'hard',
                description: 'Diagnose wiring errors in patch panel configuration'
            }
        };
        
        function updateTaskInfo() {
            const taskId = document.getElementById('taskSelect').value;
            const task = taskDescriptions[taskId];
            
            document.getElementById('taskTitle').textContent = task.title;
            
            const difficultyBadge = `<span class="difficulty-badge difficulty-${task.difficulty}">${task.difficulty.toUpperCase()}</span>`;
            document.getElementById('taskDifficulty').innerHTML = difficultyBadge;
        }
        
        async function resetEnvironment() {
            const taskId = document.getElementById('taskSelect').value;
            const resultsDiv = document.getElementById('results');
            
            resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div><p>Resetting environment...</p></div>';
            
            try {
                const response = await fetch('/reset', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ task_id: taskId })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    currentObservation = data.observation;
                    taskData = data.info;
                    stepCounter = 0;
                    
                    // Update task info display
                    document.getElementById('taskInfo').style.display = 'block';
                    document.getElementById('taskScenario').textContent = currentObservation.scenario;
                    document.getElementById('taskVisual').textContent = currentObservation.visual_context;
                    document.getElementById('taskQuestion').textContent = currentObservation.question;
                    
                    // Enable step button
                    document.getElementById('stepButton').disabled = false;
                    document.getElementById('actionInput').value = '';
                    document.getElementById('actionInput').focus();
                    
                    // Show stats
                    document.getElementById('statsPanel').style.display = 'grid';
                    document.getElementById('stepCount').textContent = '0';
                    document.getElementById('currentScore').textContent = '0.00';
                    document.getElementById('doneStatus').textContent = '⏳';
                    
                    // Display success
                    resultsDiv.innerHTML = `
                        <div class="result-item">
                            <h4>✅ Environment Reset Successfully</h4>
                            <p><strong>Task:</strong> ${taskData.task_id}</p>
                            <p><strong>Difficulty:</strong> ${taskData.difficulty}</p>
                            <p><strong>Max Steps:</strong> ${taskData.max_steps}</p>
                        </div>
                    `;
                } else {
                    resultsDiv.innerHTML = `
                        <div class="result-item">
                            <h4>❌ Reset Failed</h4>
                            <pre>${JSON.stringify(data, null, 2)}</pre>
                        </div>
                    `;
                }
            } catch (error) {
                resultsDiv.innerHTML = `
                    <div class="result-item">
                        <h4>❌ Error</h4>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }
        
        async function takeStep() {
            const action = document.getElementById('actionInput').value.trim();
            
            if (!action) {
                alert('Please enter your answer!');
                return;
            }
            
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML += '<div class="loading"><div class="spinner"></div><p>Processing your answer...</p></div>';
            
            try {
                const response = await fetch('/step', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: action })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    stepCounter++;
                    currentObservation = data.observation;
                    const reward = data.reward;
                    const done = data.done;
                    
                    // Update stats
                    document.getElementById('stepCount').textContent = stepCounter;
                    document.getElementById('currentScore').textContent = reward.score.toFixed(2);
                    document.getElementById('doneStatus').textContent = done ? '✅' : '⏳';
                    
                    // Remove loading spinner
                    const loadingDivs = resultsDiv.querySelectorAll('.loading');
                    loadingDivs.forEach(div => div.remove());
                    
                    // Display result
                    const scoreClass = reward.score >= 0.75 ? 'score-good' : reward.score >= 0.3 ? '' : 'score-bad';
                    
                    resultsDiv.innerHTML += `
                        <div class="result-item">
                            <h4>Step ${stepCounter} Result</h4>
                            <p><strong>Your Answer:</strong> ${action}</p>
                            <div class="score-display ${scoreClass}">
                                Score: ${reward.score.toFixed(2)}
                            </div>
                            <p><strong>Feedback:</strong> ${reward.feedback}</p>
                            <p><strong>Correct:</strong> ${reward.correct ? '✅ Yes' : '❌ No'}</p>
                            <p><strong>Episode Done:</strong> ${done ? '✅ Yes' : '❌ No'}</p>
                        </div>
                    `;
                    
                    // Scroll to bottom
                    resultsDiv.scrollTop = resultsDiv.scrollHeight;
                    
                    // Clear input
                    document.getElementById('actionInput').value = '';
                    
                    // Disable button if done
                    if (done) {
                        document.getElementById('stepButton').disabled = true;
                        document.getElementById('actionInput').disabled = true;
                        document.getElementById('doneStatus').textContent = reward.correct ? '✅' : '❌';
                    } else {
                        document.getElementById('actionInput').focus();
                    }
                    
                } else {
                    resultsDiv.innerHTML += `
                        <div class="result-item">
                            <h4>❌ Step Failed</h4>
                            <pre>${JSON.stringify(data, null, 2)}</pre>
                        </div>
                    `;
                }
            } catch (error) {
                resultsDiv.innerHTML += `
                    <div class="result-item">
                        <h4>❌ Error</h4>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        }
        
        // Allow Enter key to submit
        document.getElementById('actionInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !document.getElementById('stepButton').disabled) {
                takeStep();
            }
        });
        
        // Initialize on load
        updateTaskInfo();
    </script>
</body>
</html>
    """


# ============================================================================
# OPENENV API ENDPOINTS
# ============================================================================

@app.post("/reset")
async def reset(request: ResetRequest = None):
    """
    Reset the environment to initial state.
    
    Args:
        request: Optional request with task_id
        
    Returns:
        Initial observation and environment info
    """
    global env_instance, current_task_id
    
    try:
        # Get task_id from request or environment variable
        task_id = None
        if request and request.task_id:
            task_id = request.task_id
        else:
            task_id = os.getenv("FIELD_TECH_TASK", "cable_id_basic")
        
        current_task_id = task_id
        
        # Create new environment instance
        env_instance = FieldTechEnv(task_id=task_id)
        
        # Get initial observation
        result = env_instance.reset()
        
        # Return OpenEnv-compliant response
        return JSONResponse(content=result)
        # return JSONResponse(content={
        #     "observation": observation.model_dump(),
        #     "info": {
        #         "task_id": task_id,
        #         "max_steps": env_instance.max_steps,
        #         "difficulty": env_instance.task_config["difficulty"]
        #     }
        # })
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@app.post("/step")
async def step(request: StepRequest):
    """
    Take a step in the environment with given action.
    
    Args:
        request: StepRequest with action string
        
    Returns:
        observation, reward, done, info
    """
    global env_instance
    
    if env_instance is None:
        raise HTTPException(
            status_code=400, 
            detail="Environment not initialized. Call /reset first."
        )
    
    try:
        # Create action object
        action = FieldTechAction(response=request.action)
        
        # Take step in environment
        result = env_instance.step(action)
        # observation, reward, done, info = env_instance.step(action)
        
        # Return OpenEnv-compliant response
        return JSONResponse(content=result)
        # return JSONResponse(content={
        #     "observation": observation.model_dump(),
        #     "reward": reward.model_dump(),
        #     "done": done,
        #     "info": info
        # })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step failed: {str(e)}")


@app.get("/state")
async def get_state():
    """
    Get current environment state (optional endpoint).
    
    Returns:
        Current state information
    """
    global env_instance, current_task_id
    
    if env_instance is None:
        return JSONResponse(content={
            "initialized": False,
            "task_id": None,
            "step": 0,
            "done": False
        })
    
    return JSONResponse(content={
        "initialized": True,
        "task_id": current_task_id,
        "step": env_instance.step_count,
        "done": env_instance.done,
        "max_steps": env_instance.max_steps
    })


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

import os
import uvicorn

def main():
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == '__main__':
    main()


if __name__ == "__main__":
    # Get port from environment (HuggingFace Spaces uses 7860)
    port = int(os.getenv("PORT", 7860))
    
    # Run server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )
