#!/usr/bin/env python3
"""
Round 2 Agent Training - Deep Specialization

Provides deep, project-specific training to agents after they've gained
experience with the codebase. This implements the second round of specialization
as described in resources/specialization-guidelines.md.

Triggered by:
- 24+ hours of project work
- 50+ tasks completed
- Manual trigger by human
- Agent-manager determination

Author: Onboard Agent Ecosystem v2.0
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class Round2Trainer:
    """
    Deep training system for agent specialization.

    Analyzes project patterns and injects specialized knowledge into agents.
    """

    def __init__(self, project_root: str = "."):
        """
        Initialize trainer.

        Args:
            project_root: Path to project root
        """
        self.project_root = Path(project_root).resolve()
        self.agents_dir = self.project_root / ".claude" / "agents"
        self.audit_path = self.project_root / ".claude" / "audit-trail.jsonl"

    def analyze_project_patterns(self) -> Dict[str, Any]:
        """
        Analyze codebase to extract patterns and conventions.

        Returns:
            Dict with detected patterns
        """
        patterns = {
            "coding_standards": self._detect_coding_standards(),
            "api_patterns": self._detect_api_patterns(),
            "testing_patterns": self._detect_testing_patterns(),
            "data_sources": self._map_data_sources(),
            "integration_points": self._find_integrations(),
            "common_libraries": self._identify_libraries()
        }

        return patterns

    def train_agent(
        self,
        agent_name: str,
        patterns: Dict[str, Any],
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Apply Round 2 deep training to specific agent.

        Args:
            agent_name: Agent file name (without .md extension)
            patterns: Project patterns from analyze_project_patterns()
            force: Force training even if already trained

        Returns:
            Dict with training status
        """
        agent_file = self.agents_dir / f"{agent_name}.md"

        if not agent_file.exists():
            return {"error": f"Agent not found: {agent_name}"}

        # Read agent file
        with open(agent_file) as f:
            content = f.read()

        # Check if already trained
        if "## Round 2 Deep Training" in content and not force:
            return {
                "status": "already_trained",
                "agent": agent_name,
                "message": "Use force=True to retrain"
            }

        # Generate training section based on agent role
        training_section = self._generate_training_section(agent_name, patterns)

        # Inject training into agent
        updated_content = self._inject_training(content, training_section)

        # Save updated agent
        with open(agent_file, 'w') as f:
            f.write(updated_content)

        # Log to audit trail
        self._log_training(agent_name, patterns)

        return {
            "status": "trained",
            "agent": agent_name,
            "training_tokens": len(training_section.split()),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def train_all_agents(self, patterns: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        Train all agents in the project.

        Args:
            patterns: Pre-analyzed patterns (or None to analyze first)

        Returns:
            List of training results
        """
        if not patterns:
            print("Analyzing project patterns...")
            patterns = self.analyze_project_patterns()

        results = []

        for agent_file in self.agents_dir.glob("*.md"):
            agent_name = agent_file.stem
            print(f"Training {agent_name}...")

            result = self.train_agent(agent_name, patterns)
            results.append(result)

        return results

    # Pattern Detection Methods

    def _detect_coding_standards(self) -> Dict[str, Any]:
        """Detect coding standards from config files."""
        standards = {}

        # Check for linter configs
        configs = {
            ".eslintrc": "ESLint",
            ".eslintrc.json": "ESLint",
            ".prettierrc": "Prettier",
            "pyproject.toml": "Python (Black/Ruff)",
            ".flake8": "Flake8",
            "tslint.json": "TSLint"
        }

        for config_file, tool in configs.items():
            if (self.project_root / config_file).exists():
                standards[tool] = str(self.project_root / config_file)

        return standards

    def _detect_api_patterns(self) -> Dict[str, Any]:
        """Detect API patterns and endpoints."""
        api_patterns = {
            "base_url": "http://localhost:3000/api",  # Default
            "auth_type": "unknown",
            "endpoints": []
        }

        # Look for common API files
        api_files = []
        for pattern in ["**/api/**/*.ts", "**/routes/**/*.py", "**/controllers/**/*.js"]:
            api_files.extend(self.project_root.glob(pattern))

        if api_files:
            api_patterns["endpoints_count"] = len(api_files)
            api_patterns["api_files"] = [str(f.relative_to(self.project_root)) for f in api_files[:5]]

        return api_patterns

    def _detect_testing_patterns(self) -> Dict[str, Any]:
        """Detect testing framework and patterns."""
        testing = {}

        # Check for test frameworks
        frameworks = {
            "jest.config.js": "Jest",
            "pytest.ini": "Pytest",
            "phpunit.xml": "PHPUnit",
            "karma.conf.js": "Karma"
        }

        for config, framework in frameworks.items():
            if (self.project_root / config).exists():
                testing["framework"] = framework
                break

        # Count test files
        test_files = list(self.project_root.glob("**/*.test.*")) + \
                    list(self.project_root.glob("**/*.spec.*"))

        testing["test_files_count"] = len(test_files)

        return testing

    def _map_data_sources(self) -> Dict[str, Any]:
        """Map data sources and databases."""
        data_sources = {}

        # Check for database configs
        db_indicators = {
            "DATABASE_URL": "PostgreSQL/MySQL",
            "MONGO_URI": "MongoDB",
            "REDIS_URL": "Redis"
        }

        # Check .env file
        env_file = self.project_root / ".env"
        if env_file.exists():
            with open(env_file) as f:
                env_content = f.read()
                for indicator, db_type in db_indicators.items():
                    if indicator in env_content:
                        data_sources[db_type] = "configured"

        return data_sources

    def _find_integrations(self) -> List[str]:
        """Find external service integrations."""
        integrations = []

        # Common integration patterns
        integration_keywords = [
            "stripe", "aws", "gcp", "azure", "sendgrid",
            "twilio", "firebase", "auth0", "okta"
        ]

        # Search package.json or requirements.txt
        package_files = [
            self.project_root / "package.json",
            self.project_root / "requirements.txt",
            self.project_root / "Gemfile"
        ]

        for pkg_file in package_files:
            if pkg_file.exists():
                with open(pkg_file) as f:
                    content = f.read().lower()
                    for keyword in integration_keywords:
                        if keyword in content:
                            integrations.append(keyword)

        return list(set(integrations))

    def _identify_libraries(self) -> List[str]:
        """Identify major libraries and frameworks."""
        libraries = []

        # Check package.json
        package_json = self.project_root / "package.json"
        if package_json.exists():
            with open(package_json) as f:
                pkg_data = json.load(f)
                deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}

                # Major frameworks
                major_libs = ["react", "vue", "angular", "express", "next", "nuxt"]
                for lib in major_libs:
                    if lib in deps:
                        libraries.append(f"{lib}@{deps[lib]}")

        return libraries

    # Training Content Generation

    def _generate_training_section(self, agent_name: str, patterns: Dict[str, Any]) -> str:
        """
        Generate agent-specific training content.

        Args:
            agent_name: Agent identifier
            patterns: Detected project patterns

        Returns:
            Markdown training section
        """
        role = self._infer_role(agent_name)

        training = f"""
## Round 2 Deep Training

**Training Status:** Completed on {datetime.utcnow().strftime('%Y-%m-%d')}
**Training Level:** Deep Domain Specialization

### Project-Specific Knowledge

"""

        if "frontend" in role:
            training += self._generate_frontend_training(patterns)
        elif "backend" in role:
            training += self._generate_backend_training(patterns)
        elif "test" in role or "qa" in role:
            training += self._generate_testing_training(patterns)
        else:
            training += self._generate_generic_training(patterns)

        training += f"""

### Coding Standards

"""

        if patterns["coding_standards"]:
            for tool, config_path in patterns["coding_standards"].items():
                training += f"- **{tool}**: Configured at `{config_path}`\n"
        else:
            training += "- Follow general best practices for the tech stack\n"

        training += f"""

### Integration Points

"""

        if patterns["integration_points"]:
            for integration in patterns["integration_points"]:
                training += f"- **{integration.capitalize()}**: Integrated in project\n"
        else:
            training += "- No major third-party integrations detected\n"

        training += f"""

### Data Sources

"""

        if patterns["data_sources"]:
            for db, status in patterns["data_sources"].items():
                training += f"- **{db}**: {status}\n"
        else:
            training += "- Data sources not yet configured\n"

        training += "\n---\n"

        return training

    def _generate_frontend_training(self, patterns: Dict) -> str:
        """Generate frontend-specific training."""
        training = "**Frontend Development Context:**\n\n"

        libs = patterns.get("common_libraries", [])
        react_version = next((lib for lib in libs if "react" in lib.lower()), "React (version unknown)")

        training += f"- **Framework:** {react_version}\n"
        training += "- **Component Pattern:** Functional components with hooks (modern standard)\n"
        training += "- **State Management:** Context API / Zustand / Redux (check codebase)\n"
        training += "- **Styling:** Check for Tailwind, CSS Modules, or styled-components in package.json\n\n"

        return training

    def _generate_backend_training(self, patterns: Dict) -> str:
        """Generate backend-specific training."""
        training = "**Backend Development Context:**\n\n"

        api_patterns = patterns.get("api_patterns", {})
        training += f"- **API Base:** {api_patterns.get('base_url', 'Not configured')}\n"
        training += f"- **Endpoints:** {api_patterns.get('endpoints_count', 0)} API files found\n\n"

        data_sources = patterns.get("data_sources", {})
        if data_sources:
            training += "- **Databases:** " + ", ".join(data_sources.keys()) + "\n\n"

        return training

    def _generate_testing_training(self, patterns: Dict) -> str:
        """Generate testing-specific training."""
        training = "**Testing Context:**\n\n"

        testing = patterns.get("testing_patterns", {})
        framework = testing.get("framework", "Unknown")
        test_count = testing.get("test_files_count", 0)

        training += f"- **Framework:** {framework}\n"
        training += f"- **Test Files:** {test_count} existing test files\n"
        training += "- **Coverage Target:** 80%+ (standard best practice)\n\n"

        return training

    def _generate_generic_training(self, patterns: Dict) -> str:
        """Generate generic training for non-specialized agents."""
        training = "**Project Context:**\n\n"

        training += f"- **Libraries:** {len(patterns.get('common_libraries', []))} major dependencies\n"
        training += f"- **Integrations:** {len(patterns.get('integration_points', []))} third-party services\n"
        training += f"- **Testing:** {patterns.get('testing_patterns', {}).get('framework', 'Not configured')}\n\n"

        return training

    def _inject_training(self, content: str, training_section: str) -> str:
        """
        Inject training section into agent content.

        Args:
            content: Current agent file content
            training_section: Training markdown to inject

        Returns:
            Updated content
        """
        # Look for injection marker
        marker = "## Development Workflow"

        if marker in content:
            # Inject before Development Workflow
            parts = content.split(marker, 1)
            return parts[0] + training_section + "\n" + marker + parts[1]
        else:
            # Append to end
            return content + "\n\n" + training_section

    def _infer_role(self, agent_name: str) -> str:
        """Infer agent role from name."""
        name_lower = agent_name.lower()

        if "frontend" in name_lower or "ui" in name_lower or "react" in name_lower:
            return "frontend"
        elif "backend" in name_lower or "api" in name_lower or "server" in name_lower:
            return "backend"
        elif "test" in name_lower or "qa" in name_lower:
            return "testing"
        elif "database" in name_lower or "db" in name_lower:
            return "database"
        else:
            return "generic"

    def _log_training(self, agent_name: str, patterns: Dict) -> None:
        """Log training event to audit trail."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event": "agent_training_round2",
            "agent": agent_name,
            "patterns_applied": list(patterns.keys())
        }

        with open(self.audit_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')


def main():
    """CLI interface for Round 2 training."""
    if len(sys.argv) < 2:
        print("Usage: python train_agents_round2.py <command> [options]")
        print()
        print("Commands:")
        print("  analyze              Analyze project patterns")
        print("  train <agent-name>   Train specific agent")
        print("  train-all            Train all agents")
        print()
        sys.exit(1)

    command = sys.argv[1]
    trainer = Round2Trainer()

    if command == "analyze":
        print("Analyzing project patterns...")
        patterns = trainer.analyze_project_patterns()
        print(json.dumps(patterns, indent=2))

    elif command == "train" and len(sys.argv) >= 3:
        agent_name = sys.argv[2]
        print(f"Training {agent_name}...")

        patterns = trainer.analyze_project_patterns()
        result = trainer.train_agent(agent_name, patterns)

        if "error" in result:
            print(f"Error: {result['error']}")
            sys.exit(1)
        else:
            print(f"✓ Training completed")
            print(f"  Agent: {result['agent']}")
            print(f"  Tokens added: ~{result['training_tokens']}")

    elif command == "train-all":
        print("Training all agents...")
        results = trainer.train_all_agents()

        success_count = sum(1 for r in results if r.get("status") == "trained")
        print(f"\n✓ Training completed: {success_count}/{len(results)} agents trained")

        for result in results:
            if result.get("status") == "trained":
                print(f"  ✓ {result['agent']}")
            else:
                print(f"  ○ {result['agent']} - {result.get('status', 'skipped')}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
