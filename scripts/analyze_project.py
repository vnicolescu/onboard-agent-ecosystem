#!/usr/bin/env python3
"""
Project Analyzer - Reads or creates project specifications.

Supports:
- 5-document specification-architect pattern (blueprint, requirements, design, tasks, validation)
- Single master blueprint
- README.md files
- Creates initial spec if none exists
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ProjectAnalyzer:
    """Analyzes project structure and specifications."""
    
    SPEC_PATTERNS = {
        "specification-architect": [
            "blueprint.md",
            "requirements.md",
            "design.md",
            "tasks.md",
            "validation.md"
        ],
        "master-blueprint": ["BLUEPRINT.md", "blueprint.md"],
        "readme": ["README.md", "readme.md", "Readme.md"]
    }
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.claude_dir = self.project_root / ".claude"
        
    def detect_spec_type(self) -> Tuple[Optional[str], List[Path]]:
        """
        Detect which specification pattern exists in the project.
        
        Returns:
            (spec_type, found_files) tuple
        """
        # Check for 5-document system first (most comprehensive)
        spec_dir = self.project_root / "specs"
        if spec_dir.exists():
            found = []
            for fname in self.SPEC_PATTERNS["specification-architect"]:
                fpath = spec_dir / fname
                if fpath.exists():
                    found.append(fpath)
            if len(found) >= 3:  # At least 3 of 5 docs
                return ("specification-architect", found)
        
        # Check for master blueprint
        for fname in self.SPEC_PATTERNS["master-blueprint"]:
            fpath = self.project_root / fname
            if fpath.exists():
                return ("master-blueprint", [fpath])
        
        # Check for README
        for fname in self.SPEC_PATTERNS["readme"]:
            fpath = self.project_root / fname
            if fpath.exists():
                return ("readme", [fpath])
        
        return (None, [])
    
    def analyze(self) -> Dict:
        """
        Analyze project and return structured information.
        
        Returns:
            Dictionary with project metadata and analysis
        """
        spec_type, spec_files = self.detect_spec_type()
        
        # Gather project metadata
        project_name = self.project_root.name
        has_claude_dir = self.claude_dir.exists()
        has_agents = (self.claude_dir / "agents").exists() if has_claude_dir else False
        has_skills = (self.claude_dir / "skills").exists() if has_claude_dir else False
        
        # Technology detection
        tech_stack = self._detect_technologies()
        
        # Count files
        total_files = sum(1 for _ in self.project_root.rglob("*") if _.is_file())
        
        result = {
            "project_name": project_name,
            "project_root": str(self.project_root),
            "spec_type": spec_type,
            "spec_files": [str(f) for f in spec_files],
            "has_claude_dir": has_claude_dir,
            "has_agents": has_agents,
            "has_skills": has_skills,
            "tech_stack": tech_stack,
            "total_files": total_files,
            "needs_spec_creation": spec_type is None,
            "recommended_agents": self._recommend_agents(tech_stack)
        }
        
        return result
    
    def _detect_technologies(self) -> List[str]:
        """Detect technologies used in the project."""
        tech = []
        
        # Check for common indicators
        indicators = {
            "Python": ["requirements.txt", "setup.py", "pyproject.toml", "*.py"],
            "Node.js": ["package.json", "yarn.lock", "pnpm-lock.yaml"],
            "TypeScript": ["tsconfig.json", "*.ts", "*.tsx"],
            "React": ["package.json"],  # Will check contents
            "Vue": ["package.json"],
            "Next.js": ["next.config.js", "next.config.ts"],
            "Docker": ["Dockerfile", "docker-compose.yml"],
            "Database": ["*.sql", "prisma/", "migrations/"],
            "Frontend": ["public/", "src/components/", "styles/"],
            "Backend": ["api/", "server/", "backend/"]
        }
        
        for tech_name, patterns in indicators.items():
            for pattern in patterns:
                if "*" in pattern:
                    # Glob pattern
                    ext = pattern.split("*")[1]
                    if list(self.project_root.rglob(f"*{ext}")):
                        tech.append(tech_name)
                        break
                else:
                    # File/directory name
                    if (self.project_root / pattern).exists():
                        tech.append(tech_name)
                        break
        
        # Special checks
        pkg_json = self.project_root / "package.json"
        if pkg_json.exists():
            try:
                with open(pkg_json) as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    
                    if "react" in deps and "React" not in tech:
                        tech.append("React")
                    if "vue" in deps and "Vue" not in tech:
                        tech.append("Vue")
                    if "next" in deps and "Next.js" not in tech:
                        tech.append("Next.js")
            except:
                pass
        
        return list(set(tech))
    
    def _recommend_agents(self, tech_stack: List[str]) -> List[str]:
        """Recommend agents based on detected technologies."""
        # Core meta-orchestrators (always needed)
        agents = [
            "context-manager",
            "agent-manager",  # Handles recruitment and training
            "multi-agent-orchestrator"
        ]
        
        # Technology-specific agents
        tech_mapping = {
            "Python": ["python-pro", "backend-developer"],
            "Node.js": ["backend-developer", "nodejs-expert"],
            "TypeScript": ["typescript-pro", "frontend-developer"],
            "React": ["react-specialist", "frontend-developer"],
            "Vue": ["vue-specialist", "frontend-developer"],
            "Next.js": ["nextjs-developer", "frontend-developer"],
            "Frontend": ["frontend-developer", "ui-designer"],
            "Backend": ["backend-developer", "api-architect"],
            "Database": ["database-optimizer", "data-architect"],
            "Docker": ["devops-engineer", "build-engineer"]
        }
        
        for tech in tech_stack:
            if tech in tech_mapping:
                agents.extend(tech_mapping[tech])
        
        # Always useful
        agents.extend([
            "code-reviewer",
            "test-automator",
            "debugger",
            "task-distributor",
            "documentation-engineer"
        ])
        
        return list(dict.fromkeys(agents))  # Remove duplicates while preserving order


def main():
    """CLI entry point."""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "."
    
    analyzer = ProjectAnalyzer(project_root)
    result = analyzer.analyze()
    
    # Output as JSON
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
