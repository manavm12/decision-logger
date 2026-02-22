"""Configuration management for Decision Logger"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List
import json
import os


@dataclass
class DecisionLogConfig:
    """Configuration for decision logger"""
    # Paths
    output_dir: Path = field(default_factory=lambda: Path(".decision-log"))
    claude_logs_dir: Optional[Path] = None  # Auto-detect if None
    shell_history_path: Optional[Path] = None  # Auto-detect if None

    # Git settings
    base_branch: str = "main"
    current_branch: Optional[str] = None  # Auto-detect if None

    # OpenAI settings
    openai_api_key: Optional[str] = None  # Read from env if None
    openai_model: str = "gpt-4o-mini"
    temperature: float = 0.0

    # Redaction settings
    redact_secrets: bool = True
    redaction_patterns: List[str] = field(default_factory=list)

    # Output settings
    generate_markdown: bool = True
    generate_json: bool = True
    include_full_diffs: bool = False  # Only summaries by default

    def __post_init__(self):
        """Convert string paths to Path objects"""
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        if self.claude_logs_dir and isinstance(self.claude_logs_dir, str):
            self.claude_logs_dir = Path(self.claude_logs_dir)
        if self.shell_history_path and isinstance(self.shell_history_path, str):
            self.shell_history_path = Path(self.shell_history_path)

    @classmethod
    def load(cls, config_path: Path) -> 'DecisionLogConfig':
        """Load config from JSON file"""
        if not config_path.exists():
            return cls()

        with open(config_path) as f:
            data = json.load(f)

        # Convert path strings to Path objects
        if 'output_dir' in data:
            data['output_dir'] = Path(data['output_dir'])
        if 'claude_logs_dir' in data and data['claude_logs_dir']:
            data['claude_logs_dir'] = Path(data['claude_logs_dir'])
        if 'shell_history_path' in data and data['shell_history_path']:
            data['shell_history_path'] = Path(data['shell_history_path'])

        return cls(**data)

    def save(self, config_path: Path):
        """Save config to JSON file"""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and handle Path objects
        data = {}
        for key, value in asdict(self).items():
            if isinstance(value, Path):
                data[key] = str(value)
            else:
                data[key] = value

        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from config or environment"""
        return self.openai_api_key or os.getenv('OPENAI_API_KEY')

    def get_claude_logs_dir(self) -> Optional[Path]:
        """Auto-detect Claude logs directory if not set"""
        if self.claude_logs_dir:
            return self.claude_logs_dir

        # Auto-detect: ~/.claude/projects/[project-path]/
        home = Path.home()
        claude_projects = home / '.claude' / 'projects'

        if not claude_projects.exists():
            return None

        # Convert current working directory to Claude's format
        # /Users/foo/bar -> -Users-foo-bar
        cwd = Path.cwd()
        project_dir_name = str(cwd).replace('/', '-')
        project_dir = claude_projects / project_dir_name

        if project_dir.exists():
            return project_dir

        return None

    def get_shell_history_path(self) -> Optional[Path]:
        """Auto-detect shell history path if not set"""
        if self.shell_history_path:
            return self.shell_history_path

        # Auto-detect zsh history
        home = Path.home()
        candidates = [
            home / '.zsh_history',
            home / '.zhistory',
            home / '.bash_history',
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate

        return None
