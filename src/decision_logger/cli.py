"""CLI interface for Decision Logger"""

import click
import json
import sys
from pathlib import Path
from datetime import datetime
from .config import DecisionLogConfig
from .collectors.git_collector import GitCollector
from .collectors.shell_collector import ShellCollector
from .collectors.claude_collector import ClaudeCollector
from .processing.timeline import TimelineBuilder
from .processing.redactor import SecretRedactor
from .inference.openai_client import DecisionLogInference, InferenceError
from .renderers.markdown import MarkdownRenderer
from .renderers.json_renderer import JSONRenderer
from .utils.shell_setup import enable_extended_history, check_extended_history_enabled
from .models.events import EventType


@click.group()
def cli():
    """Decision Logger - Track technical decisions across git, shell, and AI"""
    pass


@cli.command()
@click.option('--output-dir', default='.decision-log', help='Output directory')
@click.option('--base-branch', default='main', help='Base branch for comparison')
def init(output_dir, base_branch):
    """Initialize decision logger configuration"""
    output_path = Path(output_dir)
    config_path = output_path / 'config.json'

    if config_path.exists():
        click.echo(f"Config already exists at {config_path}")
        return

    config = DecisionLogConfig(
        output_dir=output_path,
        base_branch=base_branch
    )
    config.save(config_path)

    click.echo(f"✓ Initialized config at {config_path}")

    # Check and enable extended history if needed
    if not check_extended_history_enabled():
        enabled = enable_extended_history()
        if enabled:
            click.echo("✓ Enabled zsh extended history")
            click.echo("  Note: Restart your shell for changes to take effect")
        else:
            click.echo("⚠ Could not enable extended history - timestamps may be missing")
    else:
        click.echo("✓ Extended history already enabled")


@cli.command()
@click.option('--config', default='.decision-log/config.json', help='Config file path')
@click.option('--branch', help='Branch to analyze (default: current branch)')
def generate(config, branch):
    """Generate decision log for current branch"""
    config_path = Path(config)
    config_obj = DecisionLogConfig.load(config_path)

    if branch:
        config_obj.current_branch = branch

    # 1. Collect signals
    click.echo("Collecting signals...")

    git_collector = GitCollector(config_obj)
    shell_collector = ShellCollector(config_obj)
    claude_collector = ClaudeCollector(config_obj)

    # Check availability
    if not git_collector.is_available():
        click.echo("Error: Not a git repository", err=True)
        sys.exit(1)

    # Collect events
    git_events = git_collector.collect() if git_collector.is_available() else []
    shell_events = shell_collector.collect() if shell_collector.is_available() else []
    claude_events = claude_collector.collect() if claude_collector.is_available() else []

    click.echo(f"  Git commits: {len(git_events)}")
    click.echo(f"  Shell commands: {len(shell_events)}")
    click.echo(f"  AI conversations: {len(claude_events)}")

    if len(git_events) == 0:
        click.echo("Error: No commits found on this branch", err=True)
        sys.exit(1)

    # 2. Build timeline
    click.echo("Building timeline...")
    timeline_builder = TimelineBuilder(config_obj)
    timeline = timeline_builder.merge_events(git_events, shell_events, claude_events)
    click.echo(f"  Total events: {len(timeline)}")

    # 3. Redact secrets
    if config_obj.redact_secrets:
        click.echo("Redacting secrets...")
        redactor = SecretRedactor()
        redactor.redact_timeline(timeline)

    # 4. Prepare context for inference
    timeline_context = _format_timeline_for_inference(timeline)

    # Truncate if too long (keep first and last events)
    max_events = 1000
    if len(timeline) > max_events:
        click.echo(f"⚠ Timeline large ({len(timeline)} events), truncating to {max_events}")
        # Keep first half and last half
        half = max_events // 2
        truncated = timeline[:half] + timeline[-half:]
        timeline_context = _format_timeline_for_inference(truncated)

    # 5. Run inference
    click.echo("Inferring decisions with OpenAI...")
    try:
        inference = DecisionLogInference(config_obj)
        decision_log = inference.infer_decision_log(
            timeline_context,
            config_obj.current_branch or git_collector.get_current_branch() or "current"
        )
    except InferenceError as e:
        click.echo(f"Error during inference: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)

    # 6. Render outputs
    click.echo("Generating outputs...")

    branch_name = config_obj.current_branch or git_collector.get_current_branch() or "current"
    generated_at = datetime.now()

    if config_obj.generate_markdown:
        md_renderer = MarkdownRenderer()
        markdown = md_renderer.render_decision_log(
            decision_log,
            timeline,
            branch_name,
            generated_at
        )

        md_path = config_obj.output_dir / f"{branch_name}.md"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown)
        click.echo(f"  Markdown: {md_path}")

    if config_obj.generate_json:
        json_renderer = JSONRenderer()
        json_output = json_renderer.render(decision_log, timeline, branch_name, generated_at)

        json_path = config_obj.output_dir / f"{branch_name}.json"
        json_path.write_text(json_output)
        click.echo(f"  JSON: {json_path}")

    click.echo("✓ Decision log generated successfully")


@cli.command()
@click.option('--config', default='.decision-log/config.json', help='Config file path')
@click.option('--branch', help='Branch to analyze (default: current branch)')
def stats(config, branch):
    """Show timeline statistics without calling OpenAI"""
    config_path = Path(config)
    config_obj = DecisionLogConfig.load(config_path)

    if branch:
        config_obj.current_branch = branch

    git_collector = GitCollector(config_obj)
    shell_collector = ShellCollector(config_obj)
    claude_collector = ClaudeCollector(config_obj)

    if not git_collector.is_available():
        click.echo("Error: Not a git repository", err=True)
        sys.exit(1)

    git_events = git_collector.collect() if git_collector.is_available() else []
    shell_events = shell_collector.collect() if shell_collector.is_available() else []
    claude_events = claude_collector.collect() if claude_collector.is_available() else []

    timeline_builder = TimelineBuilder(config_obj)
    timeline = timeline_builder.merge_events(git_events, shell_events, claude_events)

    branch_name = config_obj.current_branch or git_collector.get_current_branch() or "current"

    click.echo(f"\nDecision Logger Stats — {branch_name}")
    click.echo("=" * 50)

    # Totals
    click.echo(f"\nSignal sources:")
    click.echo(f"  Git commits   : {len(git_events)}")
    click.echo(f"  Shell commands: {len(shell_events)}")
    click.echo(f"  AI messages   : {len(claude_events)}")
    click.echo(f"  Total events  : {len(timeline)}")

    # Time range
    timestamped = [e for e in timeline if e.timestamp]
    if timestamped:
        earliest = min(e.timestamp for e in timestamped)
        latest = max(e.timestamp for e in timestamped)
        click.echo(f"\nTime range:")
        click.echo(f"  From : {earliest.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"  To   : {latest.strftime('%Y-%m-%d %H:%M:%S')}")
        delta = latest - earliest
        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)
        click.echo(f"  Span : {hours}h {minutes}m")

    # Git commits
    if git_events:
        click.echo(f"\nCommits ({len(git_events)}):")
        for e in git_events:
            short_hash = e.commit_hash[:7] if e.commit_hash else "?"
            click.echo(f"  {short_hash}  {e.commit_message}")

        all_files = []
        for e in git_events:
            all_files.extend(e.files_changed)
        if all_files:
            from collections import Counter
            top_files = Counter(all_files).most_common(5)
            click.echo(f"\nMost changed files:")
            for f, count in top_files:
                click.echo(f"  {count}x  {f}")

    # Shell commands
    if shell_events:
        from collections import Counter
        prefixes = [e.command.split()[0] for e in shell_events if e.command.strip()]
        top_cmds = Counter(prefixes).most_common(8)
        click.echo(f"\nTop shell commands:")
        for cmd, count in top_cmds:
            click.echo(f"  {count:3}x  {cmd}")

    # Claude sessions
    if claude_events:
        sessions = {e.session_id for e in claude_events if hasattr(e, 'session_id') and e.session_id}
        user_msgs = sum(1 for e in claude_events if hasattr(e, 'role') and e.role == 'user')
        asst_msgs = sum(1 for e in claude_events if hasattr(e, 'role') and e.role == 'assistant')
        click.echo(f"\nClaude activity:")
        click.echo(f"  Sessions  : {len(sessions)}")
        click.echo(f"  User msgs : {user_msgs}")
        click.echo(f"  Asst msgs : {asst_msgs}")

    click.echo()


@cli.command()
@click.option('--config', default='.decision-log/config.json', help='Config file path')
@click.argument('branch')
def summary(config, branch):
    """Print short PR summary to stdout"""
    config_path = Path(config)
    config_obj = DecisionLogConfig.load(config_path)

    # Read existing decision log JSON
    json_path = config_obj.output_dir / f"{branch}.json"
    if not json_path.exists():
        click.echo(f"Error: No decision log found for branch {branch}", err=True)
        click.echo(f"Run 'decision-logger generate --branch {branch}' first", err=True)
        sys.exit(1)

    with open(json_path) as f:
        data = json.load(f)
        decision_log = data.get('decision_log', {})

    # Generate summary using OpenAI
    try:
        inference = DecisionLogInference(config_obj)
        summary_text = inference.generate_summary(decision_log)
        click.echo(summary_text)
    except InferenceError as e:
        click.echo(f"Error generating summary: {e}", err=True)
        sys.exit(1)


def _format_timeline_for_inference(timeline) -> str:
    """Format timeline events as text for OpenAI prompt"""
    lines = []

    for event in timeline:
        if not event.timestamp:
            continue

        timestamp = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        if event.event_type == EventType.GIT_COMMIT:
            commit_hash = event.commit_hash[:7] if hasattr(event, 'commit_hash') else 'unknown'
            commit_msg = event.commit_message if hasattr(event, 'commit_message') else ''
            lines.append(f"[{timestamp}] COMMIT {commit_hash}: {commit_msg}")

            if hasattr(event, 'files_changed'):
                files = event.files_changed[:5]  # Only first 5 files
                if files:
                    lines.append(f"  Files: {', '.join(files)}")
                if len(event.files_changed) > 5:
                    lines.append(f"  ... and {len(event.files_changed) - 5} more files")

        elif event.event_type == EventType.SHELL_COMMAND:
            cmd = event.command if hasattr(event, 'command') else ''
            # Truncate long commands
            if len(cmd) > 200:
                cmd = cmd[:200] + "..."
            lines.append(f"[{timestamp}] SHELL: {cmd}")

        elif event.event_type == EventType.AI_CONVERSATION:
            role = event.role if hasattr(event, 'role') else 'unknown'
            content = event.content if hasattr(event, 'content') else ''
            # Truncate and clean content
            content = content[:300].replace('\n', ' ')
            if len(content) >= 300:
                content += "..."
            lines.append(f"[{timestamp}] AI_{role.upper()}: {content}")

    return "\n".join(lines)


if __name__ == '__main__':
    cli()
