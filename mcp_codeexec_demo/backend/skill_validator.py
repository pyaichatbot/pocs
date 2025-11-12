"""
Skill Validator - Validates and manages SKILL.md format.

Implements SKILL.md format support as described in the blog post.
"""
from pathlib import Path
from typing import Dict, Any, Optional
import re


class SkillValidator:
    """Validates and manages SKILL.md files for reusable agent code."""
    
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_skill_md(self, skill_path: Path) -> Dict[str, Any]:
        """Validate a SKILL.md file format.
        
        Args:
            skill_path: Path to SKILL.md file
        
        Returns:
            Validation result with errors/warnings
        """
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "skill_info": {}
        }
        
        if not skill_path.exists():
            result["errors"].append("SKILL.md file not found")
            return result
        
        content = skill_path.read_text()
        
        # Check for required sections
        required_sections = ["Description", "Usage"]
        for section in required_sections:
            if f"## {section}" not in content:
                result["warnings"].append(f"Missing section: {section}")
        
        # Extract skill information
        skill_info = self._parse_skill_md(content)
        result["skill_info"] = skill_info
        
        result["valid"] = len(result["errors"]) == 0
        return result
    
    def _parse_skill_md(self, content: str) -> Dict[str, Any]:
        """Parse SKILL.md content to extract structured information."""
        info = {
            "name": "",
            "description": "",
            "usage": "",
            "parameters": [],
            "returns": ""
        }
        
        # Extract title
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            info["name"] = title_match.group(1).strip()
        
        # Extract description
        desc_match = re.search(r'## Description\s*\n\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
        if desc_match:
            info["description"] = desc_match.group(1).strip()
        
        # Extract usage
        usage_match = re.search(r'## Usage\s*\n\n```python\n(.+?)```', content, re.DOTALL)
        if usage_match:
            info["usage"] = usage_match.group(1).strip()
        
        # Extract parameters
        params_match = re.search(r'## Parameters\s*\n\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
        if params_match:
            params_text = params_match.group(1)
            for line in params_text.split('\n'):
                if line.strip() and line.startswith('-'):
                    info["parameters"].append(line.strip())
        
        # Extract returns
        returns_match = re.search(r'## Returns\s*\n\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
        if returns_match:
            info["returns"] = returns_match.group(1).strip()
        
        return info
    
    def generate_skill_md_template(self, skill_name: str, description: str) -> str:
        """Generate a SKILL.md template for a skill.
        
        Args:
            skill_name: Name of the skill
            description: Description of what the skill does
        
        Returns:
            SKILL.md template content
        """
        template = f"""# {skill_name}

## Description
{description}

## Usage
```python
from skills.{skill_name.lower().replace(' ', '_')} import {skill_name.lower().replace(' ', '_')}
result = await {skill_name.lower().replace(' ', '_')}(...)
```

## Parameters
- parameter1: Description
- parameter2: Description

## Returns
Description of return value
"""
        return template
    
    def list_skills(self) -> Dict[str, Path]:
        """List all available skills with their SKILL.md files.
        
        Returns:
            Dict mapping skill names to their SKILL.md paths
        """
        skills = {}
        
        if not self.skills_dir.exists():
            return skills
        
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    skills[skill_dir.name] = skill_md
        
        return skills


def get_skill_validator() -> SkillValidator:
    """Get skill validator instance."""
    from code_executor import SKILLS_DIR
    return SkillValidator(SKILLS_DIR)

