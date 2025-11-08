# Agent Skills

> Create, manage, and share Skills to extend Claude's capabilities in Claude Code.

This guide shows you how to create, use, and manage Agent Skills in Claude Code. Skills are modular capabilities that extend Claude's functionality through organized folders containing instructions, scripts, and resources.

## Prerequisites

* Claude Code version 1.0 or later
* Basic familiarity with [Claude Code](/en/quickstart)

## What are Agent Skills?

Agent Skills package expertise into discoverable capabilities. Each Skill consists of a `SKILL.md` file with instructions that Claude reads when relevant, plus optional supporting files like scripts and templates.

**How Skills are invoked**: Skills are **model-invoked**—Claude autonomously decides when to use them based on your request and the Skill's description. This is different from slash commands, which are **user-invoked** (you explicitly type `/command` to trigger them).

**Benefits**:

* Extend Claude's capabilities for your specific workflows
* Share expertise across your team via git
* Reduce repetitive prompting
* Compose multiple Skills for complex tasks

Learn more in the [Agent Skills overview](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview).

<Note>
  For a deep dive into the architecture and real-world applications of Agent Skills, read our engineering blog: [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills).
</Note>

## Create a Skill

Skills are stored as directories containing a `SKILL.md` file.

### Personal Skills

Personal Skills are available across all your projects. Store them in `~/.claude/skills/`:

```bash  theme={null}
mkdir -p ~/.claude/skills/my-skill-name
```

**Use personal Skills for**:

* Your individual workflows and preferences
* Experimental Skills you're developing
* Personal productivity tools

### Project Skills

Project Skills are shared with your team. Store them in `.claude/skills/` within your project:

```bash  theme={null}
mkdir -p .claude/skills/my-skill-name
```

**Use project Skills for**:

* Team workflows and conventions
* Project-specific expertise
* Shared utilities and scripts

Project Skills are checked into git and automatically available to team members.

### Plugin Skills

Skills can also come from [Claude Code plugins](/en/plugins). Plugins may bundle Skills that are automatically available when the plugin is installed. These Skills work the same way as personal and project Skills.

## Write SKILL.md

Create a `SKILL.md` file with YAML frontmatter and Markdown content:

```yaml  theme={null}
---
name: your-skill-name
description: Brief description of what this Skill does and when to use it
---

# Your Skill Name

## Instructions
Provide clear, step-by-step guidance for Claude.

## Examples
Show concrete examples of using this Skill.
```

**Field requirements**:

* `name`: Must use lowercase letters, numbers, and hyphens only (max 64 characters)
* `description`: Brief description of what the Skill does and when to use it (max 1024 characters)

The `description` field is critical for Claude to discover when to use your Skill. It should include both what the Skill does and when Claude should use it.

See the [best practices guide](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices) for complete authoring guidance including validation rules.

## Add supporting files

Create additional files alongside SKILL.md:

```
my-skill/
├── SKILL.md (required)
├── reference.md (optional documentation)
├── examples.md (optional examples)
├── scripts/
│   └── helper.py (optional utility)
└── templates/
    └── template.txt (optional template)
```

Reference these files from SKILL.md:

````markdown  theme={null}
For advanced usage, see [reference.md](reference.md).

Run the helper script:
```bash
python scripts/helper.py input.txt
```
````

Claude reads these files only when needed, using progressive disclosure to manage context efficiently.

## Restrict tool access with allowed-tools

Use the `allowed-tools` frontmatter field to limit which tools Claude can use when a Skill is active:

```yaml  theme={null}
---
name: safe-file-reader
description: Read files without making changes. Use when you need read-only file access.
allowed-tools: Read, Grep, Glob
---

# Safe File Reader

This Skill provides read-only file access.

## Instructions
1. Use Read to view file contents
2. Use Grep to search within files
3. Use Glob to find files by pattern
```

When this Skill is active, Claude can only use the specified tools (Read, Grep, Glob) without needing to ask for permission. This is useful for:

* Read-only Skills that shouldn't modify files
* Skills with limited scope (e.g., only data analysis, no file writing)
* Security-sensitive workflows where you want to restrict capabilities

If `allowed-tools` is not specified, Claude will ask for permission to use tools as normal, following the standard permission model.

<Note>
  `allowed-tools` is only supported for Skills in Claude Code.
</Note>

## View available Skills

Skills are automatically discovered by Claude from three sources:

* Personal Skills: `~/.claude/skills/`
* Project Skills: `.claude/skills/`
* Plugin Skills: bundled with installed plugins

**To view all available Skills**, ask Claude directly:

```
What Skills are available?
```

or

```
List all available Skills
```

This will show all Skills from all sources, including plugin Skills.

**To inspect a specific Skill**, you can also check the filesystem:

```bash  theme={null}
# List personal Skills
ls ~/.claude/skills/

# List project Skills (if in a project directory)
ls .claude/skills/

# View a specific Skill's content
cat ~/.claude/skills/my-skill/SKILL.md
```

## Test a Skill

After creating a Skill, test it by asking questions that match your description.

**Example**: If your description mentions "PDF files":

```
Can you help me extract text from this PDF?
```

Claude autonomously decides to use your Skill if it matches the request—you don't need to explicitly invoke it. The Skill activates automatically based on the context of your question.

## Debug a Skill

If Claude doesn't use your Skill, check these common issues:

### Make description specific

**Too vague**:

```yaml  theme={null}
description: Helps with documents
```

**Specific**:

```yaml  theme={null}
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

Include both what the Skill does and when to use it in the description.

### Verify file path

**Personal Skills**: `~/.claude/skills/skill-name/SKILL.md`
**Project Skills**: `.claude/skills/skill-name/SKILL.md`

Check the file exists:

```bash  theme={null}
# Personal
ls ~/.claude/skills/my-skill/SKILL.md

# Project
ls .claude/skills/my-skill/SKILL.md
```

### Check YAML syntax

Invalid YAML prevents the Skill from loading. Verify the frontmatter:

```bash  theme={null}
cat SKILL.md | head -n 10
```

Ensure:

* Opening `---` on line 1
* Closing `---` before Markdown content
* Valid YAML syntax (no tabs, correct indentation)

### View errors

Run Claude Code with debug mode to see Skill loading errors:

```bash  theme={null}
claude --debug
```

## Share Skills with your team

**Recommended approach**: Distribute Skills through [plugins](/en/plugins).

To share Skills via plugin:

1. Create a plugin with Skills in the `skills/` directory
2. Add the plugin to a marketplace
3. Team members install the plugin

For complete instructions, see [Add Skills to your plugin](/en/plugins#add-skills-to-your-plugin).

You can also share Skills directly through project repositories:

### Step 1: Add Skill to your project

Create a project Skill:

```bash  theme={null}
mkdir -p .claude/skills/team-skill
# Create SKILL.md
```

### Step 2: Commit to git

```bash  theme={null}
git add .claude/skills/
git commit -m "Add team Skill for PDF processing"
git push
```

### Step 3: Team members get Skills automatically

When team members pull the latest changes, Skills are immediately available:

```bash  theme={null}
git pull
claude  # Skills are now available
```

## Update a Skill

Edit SKILL.md directly:

```bash  theme={null}
# Personal Skill
code ~/.claude/skills/my-skill/SKILL.md

# Project Skill
code .claude/skills/my-skill/SKILL.md
```

Changes take effect the next time you start Claude Code. If Claude Code is already running, restart it to load the updates.

## Remove a Skill

Delete the Skill directory:

```bash  theme={null}
# Personal
rm -rf ~/.claude/skills/my-skill

# Project
rm -rf .claude/skills/my-skill
git commit -m "Remove unused Skill"
```

## Best practices

### Keep Skills focused

One Skill should address one capability:

**Focused**:

* "PDF form filling"
* "Excel data analysis"
* "Git commit messages"

**Too broad**:

* "Document processing" (split into separate Skills)
* "Data tools" (split by data type or operation)

### Write clear descriptions

Help Claude discover when to use Skills by including specific triggers in your description:

**Clear**:

```yaml  theme={null}
description: Analyze Excel spreadsheets, create pivot tables, and generate charts. Use when working with Excel files, spreadsheets, or analyzing tabular data in .xlsx format.
```

**Vague**:

```yaml  theme={null}
description: For files
```

### Test with your team

Have teammates use Skills and provide feedback:

* Does the Skill activate when expected?
* Are the instructions clear?
* Are there missing examples or edge cases?

### Document Skill versions

You can document Skill versions in your SKILL.md content to track changes over time. Add a version history section:

```markdown  theme={null}
# My Skill

## Version History
- v2.0.0 (2025-10-01): Breaking changes to API
- v1.1.0 (2025-09-15): Added new features
- v1.0.0 (2025-09-01): Initial release
```

This helps team members understand what changed between versions.

## Troubleshooting

### Claude doesn't use my Skill

**Symptom**: You ask a relevant question but Claude doesn't use your Skill.

**Check**: Is the description specific enough?

Vague descriptions make discovery difficult. Include both what the Skill does and when to use it, with key terms users would mention.

**Too generic**:

```yaml  theme={null}
description: Helps with data
```

**Specific**:

```yaml  theme={null}
description: Analyze Excel spreadsheets, generate pivot tables, create charts. Use when working with Excel files, spreadsheets, or .xlsx files.
```

**Check**: Is the YAML valid?

Run validation to check for syntax errors:

```bash  theme={null}
# View frontmatter
cat .claude/skills/my-skill/SKILL.md | head -n 15

# Check for common issues
# - Missing opening or closing ---
# - Tabs instead of spaces
# - Unquoted strings with special characters
```

**Check**: Is the Skill in the correct location?

```bash  theme={null}
# Personal Skills
ls ~/.claude/skills/*/SKILL.md

# Project Skills
ls .claude/skills/*/SKILL.md
```

### Skill has errors

**Symptom**: The Skill loads but doesn't work correctly.

**Check**: Are dependencies available?

Claude will automatically install required dependencies (or ask for permission to install them) when it needs them.

**Check**: Do scripts have execute permissions?

```bash  theme={null}
chmod +x .claude/skills/my-skill/scripts/*.py
```

**Check**: Are file paths correct?

Use forward slashes (Unix style) in all paths:

**Correct**: `scripts/helper.py`
**Wrong**: `scripts\helper.py` (Windows style)

### Multiple Skills conflict

**Symptom**: Claude uses the wrong Skill or seems confused between similar Skills.

**Be specific in descriptions**: Help Claude choose the right Skill by using distinct trigger terms in your descriptions.

Instead of:

```yaml  theme={null}
# Skill 1
description: For data analysis

# Skill 2
description: For analyzing data
```

Use:

```yaml  theme={null}
# Skill 1
description: Analyze sales data in Excel files and CRM exports. Use for sales reports, pipeline analysis, and revenue tracking.

# Skill 2
description: Analyze log files and system metrics data. Use for performance monitoring, debugging, and system diagnostics.
```

## Examples

### Simple Skill (single file)

```
commit-helper/
└── SKILL.md
```

```yaml  theme={null}
---
name: generating-commit-messages
description: Generates clear commit messages from git diffs. Use when writing commit messages or reviewing staged changes.
---

# Generating Commit Messages

## Instructions

1. Run `git diff --staged` to see changes
2. I'll suggest a commit message with:
   - Summary under 50 characters
   - Detailed description
   - Affected components

## Best practices

- Use present tense
- Explain what and why, not how
```

### Skill with tool permissions

```
code-reviewer/
└── SKILL.md
```

```yaml  theme={null}
---
name: code-reviewer
description: Review code for best practices and potential issues. Use when reviewing code, checking PRs, or analyzing code quality.
allowed-tools: Read, Grep, Glob
---

# Code Reviewer

## Review checklist

1. Code organization and structure
2. Error handling
3. Performance considerations
4. Security concerns
5. Test coverage

## Instructions

1. Read the target files using Read tool
2. Search for patterns using Grep
3. Find related files using Glob
4. Provide detailed feedback on code quality
```

### Multi-file Skill

```
pdf-processing/
├── SKILL.md
├── FORMS.md
├── REFERENCE.md
└── scripts/
    ├── fill_form.py
    └── validate.py
```

**SKILL.md**:

````yaml  theme={null}
---
name: pdf-processing
description: Extract text, fill forms, merge PDFs. Use when working with PDF files, forms, or document extraction. Requires pypdf and pdfplumber packages.
---

# PDF Processing

## Quick start

Extract text:
```python
import pdfplumber
with pdfplumber.open("doc.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

For form filling, see [FORMS.md](FORMS.md).
For detailed API reference, see [REFERENCE.md](REFERENCE.md).

## Requirements

Packages must be installed in your environment:
```bash
pip install pypdf pdfplumber
```
````

<Note>
  List required packages in the description. Packages must be installed in your environment before Claude can use them.
</Note>

Claude loads additional files only when needed.

## Next steps

<CardGroup cols={2}>
  <Card title="Authoring best practices" icon="lightbulb" href="https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices">
    Write Skills that Claude can use effectively
  </Card>

  <Card title="Agent Skills overview" icon="book" href="https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview">
    Learn how Skills work across Claude products
  </Card>

  <Card title="Use Skills in the Agent SDK" icon="cube" href="https://docs.claude.com/en/docs/agent-sdk/skills">
    Use Skills programmatically with TypeScript and Python
  </Card>

  <Card title="Get started with Agent Skills" icon="rocket" href="https://docs.claude.com/en/docs/agents-and-tools/agent-skills/quickstart">
    Create your first Skill
  </Card>
</CardGroup>

# Agent Skills in the SDK

> Extend Claude with specialized capabilities using Agent Skills in the Claude Agent SDK

## Overview

Agent Skills extend Claude with specialized capabilities that Claude autonomously invokes when relevant. Skills are packaged as `SKILL.md` files containing instructions, descriptions, and optional supporting resources.

For comprehensive information about Skills, including benefits, architecture, and authoring guidelines, see the [Agent Skills overview](/en/docs/agents-and-tools/agent-skills/overview).

## How Skills Work with the SDK

When using the Claude Agent SDK, Skills are:

1. **Defined as filesystem artifacts**: Created as `SKILL.md` files in specific directories (`.claude/skills/`)
2. **Loaded from filesystem**: Skills are loaded from configured filesystem locations. You must specify `settingSources` (TypeScript) or `setting_sources` (Python) to load Skills from the filesystem
3. **Automatically discovered**: Once filesystem settings are loaded, Skill metadata is discovered at startup from user and project directories; full content loaded when triggered
4. **Model-invoked**: Claude autonomously chooses when to use them based on context
5. **Enabled via allowed\_tools**: Add `"Skill"` to your `allowed_tools` to enable Skills

Unlike subagents (which can be defined programmatically), Skills must be created as filesystem artifacts. The SDK does not provide a programmatic API for registering Skills.

<Note>
  **Default behavior**: By default, the SDK does not load any filesystem settings. To use Skills, you must explicitly configure `settingSources: ['user', 'project']` (TypeScript) or `setting_sources=["user", "project"]` (Python) in your options.
</Note>

## Using Skills with the SDK

To use Skills with the SDK, you need to:

1. Include `"Skill"` in your `allowed_tools` configuration
2. Configure `settingSources`/`setting_sources` to load Skills from the filesystem

Once configured, Claude automatically discovers Skills from the specified directories and invokes them when relevant to the user's request.

<CodeGroup>
  ```python Python theme={null}
  import asyncio
  from claude_agent_sdk import query, ClaudeAgentOptions

  async def main():
      options = ClaudeAgentOptions(
          cwd="/path/to/project",  # Project with .claude/skills/
          setting_sources=["user", "project"],  # Load Skills from filesystem
          allowed_tools=["Skill", "Read", "Write", "Bash"]  # Enable Skill tool
      )

      async for message in query(
          prompt="Help me process this PDF document",
          options=options
      ):
          print(message)

  asyncio.run(main())
  ```

  ```typescript TypeScript theme={null}
  import { query } from "@anthropic-ai/claude-agent-sdk";

  for await (const message of query({
    prompt: "Help me process this PDF document",
    options: {
      cwd: "/path/to/project",  // Project with .claude/skills/
      settingSources: ["user", "project"],  // Load Skills from filesystem
      allowedTools: ["Skill", "Read", "Write", "Bash"]  // Enable Skill tool
    }
  })) {
    console.log(message);
  }
  ```
</CodeGroup>

## Skill Locations

Skills are loaded from filesystem directories based on your `settingSources`/`setting_sources` configuration:

* **Project Skills** (`.claude/skills/`): Shared with your team via git - loaded when `setting_sources` includes `"project"`
* **User Skills** (`~/.claude/skills/`): Personal Skills across all projects - loaded when `setting_sources` includes `"user"`
* **Plugin Skills**: Bundled with installed Claude Code plugins

## Creating Skills

Skills are defined as directories containing a `SKILL.md` file with YAML frontmatter and Markdown content. The `description` field determines when Claude invokes your Skill.

**Example directory structure**:

```bash  theme={null}
.claude/skills/processing-pdfs/
└── SKILL.md
```

For complete guidance on creating Skills, including SKILL.md structure, multi-file Skills, and examples, see:

* [Agent Skills in Claude Code](https://code.claude.com/docs/skills): Complete guide with examples
* [Agent Skills Best Practices](/en/docs/agents-and-tools/agent-skills/best-practices): Authoring guidelines and naming conventions

## Tool Restrictions

<Note>
  The `allowed-tools` frontmatter field in SKILL.md is only supported when using Claude Code CLI directly. **It does not apply when using Skills through the SDK**.

  When using the SDK, control tool access through the main `allowedTools` option in your query configuration.
</Note>

To restrict tools for Skills in SDK applications, use the `allowedTools` option:

<Note>
  Import statements from the first example are assumed in the following code snippets.
</Note>

<CodeGroup>
  ```python Python theme={null}
  options = ClaudeAgentOptions(
      setting_sources=["user", "project"],  # Load Skills from filesystem
      allowed_tools=["Skill", "Read", "Grep", "Glob"]  # Restricted toolset
  )

  async for message in query(
      prompt="Analyze the codebase structure",
      options=options
  ):
      print(message)
  ```

  ```typescript TypeScript theme={null}
  // Skills can only use Read, Grep, and Glob tools
  for await (const message of query({
    prompt: "Analyze the codebase structure",
    options: {
      settingSources: ["user", "project"],  // Load Skills from filesystem
      allowedTools: ["Skill", "Read", "Grep", "Glob"]  // Restricted toolset
    }
  })) {
    console.log(message);
  }
  ```
</CodeGroup>

## Discovering Available Skills

To see which Skills are available in your SDK application, simply ask Claude:

<CodeGroup>
  ```python Python theme={null}
  options = ClaudeAgentOptions(
      setting_sources=["user", "project"],  # Load Skills from filesystem
      allowed_tools=["Skill"]
  )

  async for message in query(
      prompt="What Skills are available?",
      options=options
  ):
      print(message)
  ```

  ```typescript TypeScript theme={null}
  for await (const message of query({
    prompt: "What Skills are available?",
    options: {
      settingSources: ["user", "project"],  // Load Skills from filesystem
      allowedTools: ["Skill"]
    }
  })) {
    console.log(message);
  }
  ```
</CodeGroup>

Claude will list the available Skills based on your current working directory and installed plugins.

## Testing Skills

Test Skills by asking questions that match their descriptions:

<CodeGroup>
  ```python Python theme={null}
  options = ClaudeAgentOptions(
      cwd="/path/to/project",
      setting_sources=["user", "project"],  # Load Skills from filesystem
      allowed_tools=["Skill", "Read", "Bash"]
  )

  async for message in query(
      prompt="Extract text from invoice.pdf",
      options=options
  ):
      print(message)
  ```

  ```typescript TypeScript theme={null}
  for await (const message of query({
    prompt: "Extract text from invoice.pdf",
    options: {
      cwd: "/path/to/project",
      settingSources: ["user", "project"],  // Load Skills from filesystem
      allowedTools: ["Skill", "Read", "Bash"]
    }
  })) {
    console.log(message);
  }
  ```
</CodeGroup>

Claude automatically invokes the relevant Skill if the description matches your request.

## Troubleshooting

### Skills Not Found

**Check settingSources configuration**: Skills are only loaded when you explicitly configure `settingSources`/`setting_sources`. This is the most common issue:

<CodeGroup>
  ```python Python theme={null}
  # Wrong - Skills won't be loaded
  options = ClaudeAgentOptions(
      allowed_tools=["Skill"]
  )

  # Correct - Skills will be loaded
  options = ClaudeAgentOptions(
      setting_sources=["user", "project"],  # Required to load Skills
      allowed_tools=["Skill"]
  )
  ```

  ```typescript TypeScript theme={null}
  // Wrong - Skills won't be loaded
  const options = {
    allowedTools: ["Skill"]
  };

  // Correct - Skills will be loaded
  const options = {
    settingSources: ["user", "project"],  // Required to load Skills
    allowedTools: ["Skill"]
  };
  ```
</CodeGroup>

For more details on `settingSources`/`setting_sources`, see the [TypeScript SDK reference](/en/docs/agent-sdk/typescript#settingsource) or [Python SDK reference](/en/docs/agent-sdk/python#settingsource).

**Check working directory**: The SDK loads Skills relative to the `cwd` option. Ensure it points to a directory containing `.claude/skills/`:

<CodeGroup>
  ```python Python theme={null}
  # Ensure your cwd points to the directory containing .claude/skills/
  options = ClaudeAgentOptions(
      cwd="/path/to/project",  # Must contain .claude/skills/
      setting_sources=["user", "project"],  # Required to load Skills
      allowed_tools=["Skill"]
  )
  ```

  ```typescript TypeScript theme={null}
  // Ensure your cwd points to the directory containing .claude/skills/
  const options = {
    cwd: "/path/to/project",  // Must contain .claude/skills/
    settingSources: ["user", "project"],  // Required to load Skills
    allowedTools: ["Skill"]
  };
  ```
</CodeGroup>

See the "Using Skills with the SDK" section above for the complete pattern.

**Verify filesystem location**:

```bash  theme={null}
# Check project Skills
ls .claude/skills/*/SKILL.md

# Check personal Skills
ls ~/.claude/skills/*/SKILL.md
```

### Skill Not Being Used

**Check the Skill tool is enabled**: Confirm `"Skill"` is in your `allowedTools`.

**Check the description**: Ensure it's specific and includes relevant keywords. See [Agent Skills Best Practices](/en/docs/agents-and-tools/agent-skills/best-practices#writing-effective-descriptions) for guidance on writing effective descriptions.

### Additional Troubleshooting

For general Skills troubleshooting (YAML syntax, debugging, etc.), see the [Claude Code Skills troubleshooting section](https://code.claude.com/docs/skills#troubleshooting).

## Related Documentation

### Skills Guides

* [Agent Skills in Claude Code](https://code.claude.com/docs/skills): Complete Skills guide with creation, examples, and troubleshooting
* [Agent Skills Overview](/en/docs/agents-and-tools/agent-skills/overview): Conceptual overview, benefits, and architecture
* [Agent Skills Best Practices](/en/docs/agents-and-tools/agent-skills/best-practices): Authoring guidelines for effective Skills
* [Agent Skills Cookbook](https://github.com/anthropics/claude-cookbooks/tree/main/skills): Example Skills and templates

### SDK Resources

* [Subagents in the SDK](/en/docs/agent-sdk/subagents): Similar filesystem-based agents with programmatic options
* [Slash Commands in the SDK](/en/docs/agent-sdk/slash-commands): User-invoked commands
* [SDK Overview](/en/docs/agent-sdk/overview): General SDK concepts
* [TypeScript SDK Reference](/en/docs/agent-sdk/typescript): Complete API documentation
* [Python SDK Reference](/en/docs/agent-sdk/python): Complete API documentation
