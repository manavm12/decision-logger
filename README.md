# Decision Logger

Automatically generate engineering decision logs by correlating Git commits, shell commands, and AI conversations.

Decision Logger helps you document the "why" behind your code changes by analyzing your development timeline and using AI to infer:
- What problem you were solving
- What approaches you tried
- What failed and why
- What you ultimately decided and the tradeoffs

## Features

- **Multi-Source Timeline**: Correlates Git commits, shell history, and Claude Code conversations
- **AI-Powered Inference**: Uses OpenAI to extract decision rationale from your development activity
- **Privacy-First**: Redacts API keys, tokens, and secrets before sending to OpenAI
- **Professional Output**: Generates markdown (human-readable) and JSON (machine-readable) decision logs
- **Evidence-Based**: AI cites specific commits, commands, and conversations to support claims

## Installation

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
cd decision-logger

# Create virtual environment and install dependencies
uv sync

# Activate the virtual environment
source .venv/bin/activate

# Or install in development mode with all dependencies
uv sync --all-extras
```

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (for dependency management)
- Git repository
- OpenAI API key
- Zsh shell with extended history (auto-enabled by `init` command)

## Quick Start

### 1. Initialize in your project

```bash
cd your-project
decision-logger init
```

This will:
- Create `.decision-log/config.json`
- Enable zsh extended history (for shell command timestamps)

### 2. Set your OpenAI API key

```bash
export OPENAI_API_KEY="sk-..."
```

Or add it to `.decision-log/config.json`:
```json
{
  "openai_api_key": "sk-..."
}
```

### 3. Generate a decision log for your current branch

```bash
decision-logger generate
```

This will:
1. Collect Git commits since branching from `main`
2. Collect shell commands (with timestamps)
3. Collect Claude Code conversations
4. Build a chronological timeline
5. Redact any secrets
6. Use OpenAI to infer decision rationale
7. Generate markdown and JSON outputs

### 4. View the decision log

```bash
cat .decision-log/your-branch-name.md
```

### 5. Generate a short PR summary

```bash
decision-logger summary your-branch-name
```

## Commands

### `init`

Initialize decision logger configuration.

```bash
decision-logger init [--output-dir DIR] [--base-branch BRANCH]
```

Options:
- `--output-dir`: Output directory (default: `.decision-log`)
- `--base-branch`: Base branch for comparison (default: `main`)

### `generate`

Generate decision log for current branch.

```bash
decision-logger generate [--config CONFIG] [--branch BRANCH]
```

Options:
- `--config`: Path to config file (default: `.decision-log/config.json`)
- `--branch`: Branch to analyze (default: current branch)

### `summary`

Print short PR summary to stdout.

```bash
decision-logger summary [--config CONFIG] BRANCH
```

Arguments:
- `BRANCH`: Branch name to generate summary for

## Configuration

Configuration is stored in `.decision-log/config.json`:

```json
{
  "output_dir": ".decision-log",
  "base_branch": "main",
  "openai_model": "gpt-4o-mini",
  "temperature": 0.0,
  "redact_secrets": true,
  "generate_markdown": true,
  "generate_json": true,
  "include_full_diffs": false
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `output_dir` | string | `.decision-log` | Where to write decision logs |
| `base_branch` | string | `main` | Base branch for comparison |
| `openai_api_key` | string | `null` | OpenAI API key (or use env var) |
| `openai_model` | string | `gpt-4o-mini` | OpenAI model to use |
| `temperature` | float | `0.0` | Temperature for inference (0 = deterministic) |
| `redact_secrets` | boolean | `true` | Whether to redact secrets |
| `generate_markdown` | boolean | `true` | Generate markdown output |
| `generate_json` | boolean | `true` | Generate JSON output |
| `include_full_diffs` | boolean | `false` | Include full diffs (vs summaries) |

## How It Works

### 1. Signal Collection

Decision Logger collects development signals from three sources:

**Git Commits**
- Uses `git log base_branch..current_branch` to find commits since divergence
- Extracts commit hash, message, author, timestamp, files changed, and diff summary

**Shell History**
- Parses `~/.zsh_history` with extended history format
- Extracts command, timestamp, and duration
- Requires zsh extended history (auto-enabled by `init`)

**Claude Code Conversations**
- Reads `~/.claude/projects/[project]/[sessionId].jsonl` files
- Extracts user prompts, assistant responses, timestamps, and tool calls

### 2. Timeline Correlation

All events are merged into a single chronological timeline sorted by timestamp.

### 3. Secret Redaction

Before sending to OpenAI, the timeline is scanned for:
- API keys (32+ char alphanumeric strings)
- Bearer tokens
- AWS credentials
- GitHub tokens
- Private keys (PEM format)
- JWTs
- Long base64 strings
- URLs with embedded credentials

### 4. AI Inference

The redacted timeline is sent to OpenAI (gpt-4o-mini by default) with a structured output schema that enforces:
- Problem statement
- Attempts and iterations (with evidence citations)
- Final solution (with evidence)
- Rationale and tradeoffs
- Risks and follow-ups

### 5. Output Rendering

The inferred decision log is rendered as:
- **Markdown**: Human-readable with sections and timeline appendix
- **JSON**: Machine-readable with metadata and raw timeline

## Example Output

### Markdown

```markdown
# Decision Log: feature/add-authentication

**Generated:** 2024-01-15T10:30:00
**Branch:** `feature/add-authentication`

---

## Problem Statement

Implement user authentication with JWT tokens for the API.

### Initial Context

Users need to log in to access protected endpoints. Requirements: JWT-based auth, bcrypt for password hashing.

## Attempts and Iterations

### Attempt 1: Session-based authentication

**Outcome:** rejected

**Learnings:** Session storage doesn't work well with distributed API architecture.

**Evidence:**
- [commit a7b3c2d] "Add express-session"
- [conversation: discussed session vs JWT tradeoffs]
- [commit c2f1a3e] "Revert session implementation"

### Attempt 2: JWT with HS256

**Outcome:** successful

**Learnings:** HS256 sufficient for single-server setup.

**Evidence:**
- [commit e4f2b1d] "Implement JWT with jsonwebtoken"
- [shell: npm install jsonwebtoken bcrypt]

## Final Solution

JWT-based authentication with HS256 signing, bcrypt for password hashing, tokens stored in HTTP-only cookies.

**Evidence:**
- [commit f3a1c4e] "Add JWT auth middleware"
- [commit g2b4d5e] "Add login endpoint"

## Rationale and Tradeoffs

JWT chosen over sessions for stateless architecture. HS256 chosen over RS256 for simplicity.

### Tradeoffs
- **Security vs Simplicity:** HS256 instead of RS256 - simpler but less secure for multi-server

## Risks and Follow-ups

### Risks
- Secret key stored in .env - needs rotation strategy
- No refresh token mechanism - users must re-login daily

### Follow-up Work
- Implement refresh tokens
- Add rate limiting to login endpoint
```

## Privacy & Security

Decision Logger takes privacy seriously:

1. **Secret Redaction**: All common secret patterns are redacted before sending to OpenAI
2. **Local Processing**: Timeline building and redaction happen locally
3. **Data Minimization**: Only redacted timeline text is sent to OpenAI (not full diffs)
4. **No Storage**: Decision Logger doesn't store your data - outputs are local files
5. **Open Source**: Audit the code yourself

## Troubleshooting

### "No commits found on this branch"

Make sure you're on a branch that diverged from your base branch (default: `main`).

```bash
git log main..HEAD  # Should show commits
```

### "Shell commands: 0"

Extended history is not enabled. Run:

```bash
decision-logger init
# Restart your shell
```

### "No AI conversation logs found"

Claude Code logs are auto-detected from `~/.claude/projects/`. If you're not using Claude Code, this is expected and the tool will still work with Git and shell data.

### "OpenAI API key not found"

Set the `OPENAI_API_KEY` environment variable:

```bash
export OPENAI_API_KEY="sk-..."
```

Or add it to `.decision-log/config.json`.

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
uv sync --all-extras

# Activate virtual environment
source .venv/bin/activate
```

### Running Tests

```bash
# Run tests
uv run pytest tests/ -v --cov=src/decision_logger

# Or with activated venv
pytest tests/ -v --cov=src/decision_logger
```

### Adding Dependencies

```bash
# Add production dependency
uv add package-name

# Add dev dependency
uv add --dev package-name
```

### Project Structure

```
decision-logger/
├── src/decision_logger/
│   ├── collectors/       # Signal collection (git, shell, claude)
│   ├── models/          # Data models
│   ├── processing/      # Timeline building, redaction
│   ├── inference/       # OpenAI integration
│   ├── renderers/       # Markdown and JSON output
│   ├── utils/           # Shell setup, helpers
│   ├── cli.py           # CLI commands
│   └── config.py        # Configuration
└── tests/
    └── test_*           # Unit tests
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure tests pass: `pytest tests/`
5. Submit a pull request

## License

MIT

## Credits

Built with:
- [Click](https://click.palletsprojects.com/) - CLI framework
- [OpenAI](https://openai.com/) - AI inference
- Python standard library for everything else
