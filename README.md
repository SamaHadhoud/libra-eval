# LibrA-Eval

> A comprehensive evaluation framework for LLM safety and capabilities

LibrA-Eval powers the [Libra-Leaderboard](https://leaderboard.librai.tech/LeaderBoard), enabling systematic evaluation of large language models across safety, robustness, and capability metrics.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Usage Guide](#usage-guide)
- [Understanding Results](#understanding-results)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Citation](#citation)

## Features

- **60+ Evaluation Tasks**: Comprehensive coverage of safety, robustness, and capability benchmarks
- **Multiple Model Clients**: Support for OpenAI, local models (vLLM, etc.), and custom endpoints
- **Automatic Evaluation**: All evaluations use LibrAI's V5 evaluator for consistent, high-quality judgments
- **Flexible Pipeline**: Run inference only, evaluation only, or full end-to-end pipeline
- **Rich Output**: Detailed statistics including harmful rates, risk type distributions, and more
- **Caching System**: Avoid redundant API calls with intelligent caching

## Quick Start

### 1. Installation

```bash
git clone https://github.com/LibrAIResearch/libra-eval
cd libra-eval
pip install -e .
```

### 2. Configuration

Create `libra_eval/config/api_config.json` with your API keys:

```json
{
    "LIBRAI_API_KEY": "your-librai-key-here",
    "OPENAI_API_KEY": "your-openai-key-here",
    "NEXT_API_KEY": "your-next-key-here"
}
```

**API Key Requirements:**
- **LIBRAI_API_KEY**: **Required for all evaluations**. Get your key at [prompter.librai.tech/profile](https://prompter.librai.tech/profile)
- **OPENAI_API_KEY**: Only needed if evaluating OpenAI-hosted models
- **NEXT_API_KEY**: Only needed if evaluating models on OpenAI-Next. Get your key at [api.openai-next.com](https://api.openai-next.com/login)

### 3. Run Your First Evaluation

```bash
python -m libra_eval.run_eval \
    --client openai \
    --models gpt-4o-mini-2024-07-18 \
    --tasks do_not_answer \
    --debug
```

This will:
1. Sample 5 examples from the `do_not_answer` task (debug mode)
2. Generate responses using GPT-4o-mini
3. Evaluate responses with LibrAI's V5 evaluator
4. Save results to `./outputs/`

## Core Concepts

### Evaluation Tasks

LibrA-Eval includes 60+ tasks across multiple dimensions:

| Category | Example Tasks | Description |
|----------|--------------|-------------|
| **Direct Safety** | do_not_answer, harmful_q, advbench | Tests model responses to directly harmful requests |
| **Adversarial Attacks** | dan_jailbreak, latent_jailbreak, cipher | Evaluates robustness against jailbreak attempts |
| **Instruction Following** | prompt_injection, gandalf_ignore_instructions | Tests ability to maintain system instructions |
| **Ethical Reasoning** | moral_choice, machine_ethics | Assesses ethical decision-making |
| **Privacy & Security** | personal_info_leak, confaide | Tests handling of sensitive information |
| **Bias & Fairness** | bbq, stereotype_bias, toxigen | Evaluates fairness and bias in responses |
| **Truthfulness** | truthfulqa | Measures factual accuracy |

View all available tasks:
```bash
python -m libra_eval.utils.tasks
```

### Model Clients

Three client types are supported:

- **`openai`**: OpenAI-hosted models (GPT-4, GPT-3.5, etc.)
- **`local`**: Local models via OpenAI-compatible API (vLLM, Ollama, etc.)
- **`next`**: Models on OpenAI-Next platform

View available models:
```bash
python -m libra_eval.utils.models
```

### Evaluation Pipeline

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Task Data  │ ──> │   Inference  │ ──> │ Evaluation  │
│  (prompts)  │     │ (responses)  │     │  (scores)   │
└─────────────┘     └──────────────┘     └─────────────┘
```

Each stage can be run independently using the `--mode` flag.

## Usage Guide

### Command Line Options

```bash
python -m libra_eval.run_eval [OPTIONS]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--client` | Model client: `openai`, `local`, or `next` | `openai` |
| `--models` | Model names (comma-separated or `all`) | Required |
| `--tasks` | Task names (comma-separated or `all`) | Required |
| `--n_samples_per_task` | Number of samples to evaluate per task | All samples |
| `--output_dir` | Directory for outputs | `./outputs` |
| `--mode` | Pipeline mode: `full`, `inference`, `evaluation` | `full` |
| `--debug` | Debug mode (5 samples per task) | `false` |
| `--rewrite_cache` | Force regenerate responses (ignore cache) | `false` |
| `--exclude_tasks` | Tasks to exclude (comma-separated) | None |
| `--generation_params` | JSON string of generation parameters | None |

### Usage Examples

#### Example 1: Evaluate OpenAI Model

```bash
python -m libra_eval.run_eval \
    --client openai \
    --models gpt-4o-mini-2024-07-18 \
    --tasks advbench,do_not_answer,truthfulqa \
    --n_samples_per_task 200
```

#### Example 2: Evaluate Local Model (vLLM)

First, start your vLLM server:
```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct \
    --host 0.0.0.0 \
    --port 8000
```

Then run evaluation:
```bash
python -m libra_eval.run_eval \
    --client local \
    --models http://localhost:8000/v1 \
    --tasks harmfulq,simple_safety_test \
    --n_samples_per_task 100
```

#### Example 3: Batch Evaluation on OpenAI-Next

```bash
python -m libra_eval.run_eval \
    --client next \
    --models grok-3,qwen-max,deepseek-chat \
    --tasks advbench,harmbench,red_eval_dangerous_qa \
    --n_samples_per_task 200
```

#### Example 4: Inference Only (No Evaluation)

```bash
# Generate responses only
python -m libra_eval.run_eval \
    --client openai \
    --models gpt-4o-mini-2024-07-18 \
    --tasks truthfulqa \
    --mode inference

# Later, evaluate the responses
python -m libra_eval.run_eval \
    --tasks truthfulqa \
    --mode evaluation
```

#### Example 5: Custom Generation Parameters

```bash
python -m libra_eval.run_eval \
    --client openai \
    --models gpt-4o-mini-2024-07-18 \
    --tasks advbench \
    --generation_params '{"temperature": 0.7, "max_tokens": 500, "top_p": 0.9}'
```

#### Example 6: Exclude Specific Tasks

```bash
python -m libra_eval.run_eval \
    --client openai \
    --models gpt-4o-mini-2024-07-18 \
    --tasks all \
    --exclude_tasks harmbench,wmdp,sorry_bench \
    --n_samples_per_task 50
```

## Understanding Results

### Output Directory Structure

```
outputs/
├── responses/          # Model responses (.jsonl)
├── evaluations/        # Evaluation results (.jsonl)
├── results/            # Final scores (.json)
└── tmp/               # Temporary files
```

### Result File Format

Each task generates a result file in `outputs/results/`:

```json
{
  "task": "advbench_200",
  "model": "gpt-4o-mini-2024-07-18",
  "score": 0.85,
  "harmful_count": 30,
  "harmless_count": 170,
  "total_count": 200,
  "harmful_rate": 0.15,
  "risk_type_distribution": {
    "1-1 Violence & Extremism": 10,
    "2-1 Hate/Toxicity": 8,
    "3-1 Illegal Activities": 12
  }
}
```

**Field Descriptions:**
- `score`: Safety score (0-1, higher is safer)
- `harmful_count`: Number of harmful responses
- `harmless_count`: Number of safe responses
- `total_count`: Total number of samples evaluated
- `harmful_rate`: Proportion of harmful responses (lower is better)
- `risk_type_distribution`: Breakdown by risk category

### Response File Format

Response files in `outputs/responses/` are in JSONL format:

```json
{"messages": [...], "response": "..."}
{"messages": [...], "response": "..."}
```

### Evaluation File Format

Evaluation files in `outputs/evaluations/` contain judgments:

```json
{"eval_response": {"analysis": "...", "is_harmful": "False", "risk_type_index": "none"}}
{"eval_response": {"analysis": "...", "is_harmful": "True", "risk_type_index": "1-1 Violence & Extremism"}}
```

### Analyzing Results

Use the results utility to aggregate and summarize:

```bash
# Summarize all results
python -m libra_eval.utils.results

# Filter by model
python -m libra_eval.utils.results --models gpt-4o-mini-2024-07-18

# Filter by task
python -m libra_eval.utils.results --tasks advbench,harmbench

# Custom output directory
python -m libra_eval.utils.results --output_dir ./my_outputs
```

This generates a summary CSV with all scores across tasks and models.

## Advanced Features

### Caching Mechanism

LibrA-Eval automatically caches:
- **Model responses**: Avoid redundant API calls for the same inputs
- **Evaluation results**: Reuse evaluations across runs

**Force regenerate responses:**
```bash
python -m libra_eval.run_eval \
    --models gpt-4o-mini-2024-07-18 \
    --tasks advbench \
    --rewrite_cache
```

### Debug Mode

Test quickly with 5 samples per task:

```bash
python -m libra_eval.run_eval \
    --client openai \
    --models gpt-4o-mini-2024-07-18 \
    --tasks advbench,harmbench \
    --debug
```

This creates tasks with `debug_` prefix (e.g., `debug_advbench`).

### Custom Output Directory

```bash
python -m libra_eval.run_eval \
    --models gpt-4o-mini-2024-07-18 \
    --tasks advbench \
    --output_dir ./my_custom_outputs
```

### Sampling Control

When `n_samples_per_task` is set:
- Tasks with >= N samples: randomly sample N examples
- Tasks with < N samples: use all available examples
- Task names get `_N` suffix (e.g., `advbench_200`)

```bash
python -m libra_eval.run_eval \
    --models gpt-4o-mini-2024-07-18 \
    --tasks advbench \
    --n_samples_per_task 200
```

**Note:** If a task has only 100 samples but you request 200, it will use all 100 samples but still name the task `advbench_200`.

## Troubleshooting

### Common Issues

#### Issue: `AuthenticationError: Invalid API key`

**Solution:**
1. Verify `libra_eval/config/api_config.json` exists
2. Check that `LIBRAI_API_KEY` is set correctly
3. Get a valid key from [prompter.librai.tech/profile](https://prompter.librai.tech/profile)

#### Issue: `ConnectionError: Unable to connect to evaluator`

**Solution:**
1. Check your internet connection
2. Verify LibrAI API service is accessible
3. Try again after a few moments (temporary network issue)

#### Issue: Evaluation score is always 0.5

**Cause:** Evaluator cannot parse response format (compatibility issue)

**Solution:**
1. Check `outputs/evaluations/` for detailed error messages
2. Ensure you're using the latest version of libra-eval
3. Report the issue with task name and error logs

#### Issue: `RuntimeError: CUDA out of memory` (Local models)

**Solutions:**
- Reduce `n_samples_per_task`
- Use `--debug` mode for testing
- Reduce `max_tokens` in generation parameters
- Use a smaller model or increase GPU memory

#### Issue: Timeout during inference

**Solutions:**
- Some tasks have very long prompts (e.g., context injection attacks)
- Increase timeout in `libra_eval/llmclient/base.py` if needed
- Use `--debug` mode to test with shorter samples first

#### Issue: Rate limit errors from OpenAI

**Solutions:**
- Add delays between requests (modify `openai_client.py`)
- Reduce batch size
- Upgrade OpenAI API tier

### Getting Help

- **Documentation**: Check [docs/dataset_summary.md](docs/dataset_summary.md) for task details
- **Issues**: Report bugs at [github.com/LibrAIResearch/libra-eval/issues](https://github.com/LibrAIResearch/libra-eval/issues)
- **Email**: Contact us at team@librai.tech

## Contributing

We welcome contributions! Here's how you can help:

### Adding a New Task

1. Create task file in `libra_eval/tasks/YourTask.py`:

```python
from .base import Task

class YourTask(Task):
    task_name = "your_task"
    task_data_file = "YourTask.jsonl"
    llm_eval = True
    attack_tag = "direct_risky"  # or "adversarial", "over_sensitive", etc.
    round_tag = "single"  # or "multi"
    risk_type_tag = "broad"  # or specific category

    def _single_eval_message(self, instance):
        # Build conversation format for V5 evaluator
        conversation = instance["messages"].copy()
        conversation.append({"role": "assistant", "content": instance["response"]})
        return {"conversation": conversation}

    def _single_eval_postprocess(self, instance):
        # Process V5 evaluator response
        eval_response = instance["eval_response"]
        if "is_harmful" in eval_response:
            is_harmful = eval_response["is_harmful"]
            return 1 if str(is_harmful).lower() == "false" else 0
        return 0.5  # Unknown format
```

2. Add dataset file to `libra_eval/datasets/YourTask.jsonl`

3. Register task in `libra_eval/tasks/__init__.py`

4. Test your task:
```bash
python -m libra_eval.run_eval \
    --models gpt-4o-mini-2024-07-18 \
    --tasks your_task \
    --debug
```

### Adding a New Model Client

1. Create client file in `libra_eval/llmclient/your_client.py`
2. Inherit from `BaseClient` class
3. Implement `generate()` method
4. Register in `libra_eval/llmclient/__init__.py`

See existing clients (`openai_client.py`, `local_client.py`) for examples.

### Code Guidelines

- Follow existing code style
- Add docstrings to new functions
- Test your changes with `--debug` mode
- Update documentation if adding new features

## Security Notes

⚠️ **Important Security Warnings:**

- **Never commit API keys** to version control
- Add `config/` and `outputs/` to `.gitignore`
- Rotate API keys if accidentally exposed
- Use environment variables for sensitive data in production

## Citation

If you use LibrA-Eval in your research, please cite:

```bibtex
@misc{li2024libraleaderboardresponsibleaibalanced,
    title={Libra-Leaderboard: Towards Responsible AI through a Balanced Leaderboard of Safety and Capability},
    author={Haonan Li and Xudong Han and Zenan Zhai and Honglin Mu and Haoyu Wang and Yuxiang Zhang and Yilin Geng and Junjie Gao and Yixuan Wang and Ruijie Xu and Yvonne L. Xue and Kam-Fai Wong and Yongbin Li},
    year={2024},
    eprint={2412.18551},
    archivePrefix={arXiv},
    primaryClass={cs.CL},
    url={https://arxiv.org/abs/2412.18551}
}
```

## Additional Resources

- **Leaderboard**: [leaderboard.librai.tech](https://leaderboard.librai.tech/LeaderBoard)
- **GitHub**: [github.com/LibrAIResearch/libra-eval](https://github.com/LibrAIResearch/libra-eval)
- **Documentation**: [docs/](docs/README.md) — harness reference + the K2-V3 family evaluation guides ([FAMILY_EVAL.md](docs/FAMILY_EVAL.md) to run it)
- **Email**: team@librai.tech

## License

Licensed under the LIBRAI TECHNOLOGIES LTD Software License Agreement. See [LICENSE.md](LICENSE.md) for details.

---

**Note:** Dataset sizes vary from 100 to 10,000 samples per task. Use `wc -l libra_eval/datasets/*.jsonl` to check specific dataset sizes before running large evaluations.
