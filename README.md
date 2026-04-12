
# 🔧 Field Tech Visual Assistant

**AI-powered assistance for field technicians** - OpenEnv environment

[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compliant-green)](https://github.com/meta/openenv)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 🎯 Overview

Field Tech Visual Assistant helps field technicians make critical decisions about:
- **Cable Identification**: Identify correct cables from visual descriptions
- **Port Selection**: Select proper network ports for different purposes  
- **Wiring Diagnosis**: Find all errors in complex wiring setups

**Real-world impact**: Reduces equipment damage, prevents network outages, ensures technician safety.

## 🏗️ Architecture

```
┌─────────────┐      HTTP      ┌──────────────┐
│             │ ────────────▶   │   FastAPI    │
│ inference.py│                 │   Server     │
│  (OpenAI)   │ ◀────────────   │  (app.py)    │
└─────────────┘     JSON        └──────────────┘
                                       │
                                       ▼
                                ┌──────────────┐
                                │  Environment │
                                │   (env.py)   │
                                └──────────────┘
```

## 📋 Tasks

| Task | Difficulty | Description | Max Score |
|------|-----------|-------------|-----------|
| `cable_id_basic` | Easy | Identify network cable (RJ45) | 1.0 |
| `cable_id_power` | Easy | Identify power cable for PDU | 1.0 |
| `port_select_basic` | Medium | Select management port | 1.0 |
| `port_select_uplink` | Medium | Select uplink port | 1.0 |
| `wiring_diag_server` | Hard | Find all server rack errors | 1.0 |
| `wiring_diag_patch` | Hard | Find all patch panel errors | 1.0 |

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- HuggingFace account (FREE)
- HuggingFace token

### 2. Get HuggingFace Token

1. Go to https://huggingface.co/settings/tokens
2. Click "New token" → Create token
3. Copy your token (starts with `hf_...`)

### 3. Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set your HF token
export HF_TOKEN="hf_your_token_here"

# Start the FastAPI server
python app.py
```

In another terminal:

```bash
# Run inference
export HF_TOKEN="hf_your_token_here"
python inference.py
```

### 4. Deploy to HuggingFace Spaces

```bash
# Clone Space repo
git clone https://huggingface.co/spaces/YOUR_USERNAME/field-tech-assistant
cd field-tech-assistant

# Copy files
cp -r /path/to/this/repo/* .

# Push to HuggingFace
git add .
git commit -m "Initial deployment"
git push
```

**Important**: Add your `HF_TOKEN` in Space Settings → Secrets!

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HF_TOKEN` | **YES** | *(none)* | HuggingFace API token |
| `API_BASE_URL` | No | `https://router.huggingface.co/v1` | HF Router API endpoint |
| `MODEL_NAME` | No | `Qwen/Qwen2.5-72B-Instruct` | LLM model to use |
| `FIELD_TECH_TASK` | No | `cable_id_basic` | Task to run |

**⚠️ CRITICAL**: Never commit `HF_TOKEN` to git! Use environment variables or Secrets.

## 📊 Expected Performance

| Difficulty | Target Score | Runtime |
|-----------|--------------|---------|
| Easy | 0.95+ | ~30s |
| Medium | 0.90+ | ~45s |
| Hard | 0.85+ | ~60s |

**Mean Score Target**: 0.90+

## 🧪 Testing

```bash
# Test environment
python -c "from env import FieldTechEnv; env = FieldTechEnv(); print(env.reset())"

# Test server
curl -X POST http://localhost:7860/reset
curl -X POST http://localhost:7860/step -H "Content-Type: application/json" -d '{"action":"Cable C"}'
```

## 📝 OpenEnv Compliance Checklist

- [x] FastAPI server with `/reset` and `/step` endpoints
- [x] Returns JSON with observation, reward, done, info
- [x] Uses OpenAI client with configurable API_BASE_URL and MODEL_NAME
- [x] HF_TOKEN from environment (no default)
- [x] Logs follow [START]/[STEP]/[END] format exactly
- [x] Dockerfile exposes port 7860
- [x] openenv.yaml configuration file
- [x] Proper error handling



## 💡 Key Features

**Prompt Engineering**:
- Task-specific system prompts (easy/medium/hard)
- Systematic error-checking protocols for diagnostics
- Retry logic with improved guidance

**Scoring**:
- Deterministic grading
- Partial credit for hard tasks (0.25 per error found)
- Clear feedback on incorrect answers

**Design**:
- Clean separation: server (app.py) + client (inference.py)
- OpenEnv-compliant API
- Comprehensive error handling

## 📚 File Structure

```

field-tech-assistant/
├── inference.py         # Inference script (OpenAI client)            
├── Dockerfile            # Docker file
├── server/
│   ├── env.py           # Environment logic
│   ├── app.py           # FastAPI server (OpenEnv endpoints)
│   └── models.py        # Pydantic models
├── openenv.yaml
├── pyproject.toml
├── requirements.txt     # Python dependencies
├── LICENSE              # MIT License
├── README.md            # Info file
└── .gitignore           # Git ignore rules  

```

## 🤝 Contributing

 Feel free to fork and improve!

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🔗 Links

- **HuggingFace Model**: [Qwen/Qwen2.5-72B-Instruct](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct)
- **OpenEnv Spec**: [meta/openenv](https://github.com/meta/openenv)
- **Meta AI Hackathon**: [Event Info](https://www.scaler.com/event/meta-ai-hackathon/)

---

**Built with 💙 for field technicians everywhere**

