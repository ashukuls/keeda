"""General-purpose template manager for prompt rendering"""

from typing import Dict, Any, Optional, List
import json
from jinja2 import Environment, select_autoescape, BaseLoader
import logging

logger = logging.getLogger(__name__)


class DictLoader(BaseLoader):
    """Jinja2 loader that loads templates from a dictionary"""

    def __init__(self, templates: Dict[str, str]):
        self.templates = templates

    def get_source(self, environment, template):
        if template in self.templates:
            source = self.templates[template]
            return source, None, lambda: True
        raise ValueError(f"Template {template} not found")


class PromptTemplateManager:
    """Manages and renders prompt templates using Jinja2"""

    def __init__(self):
        self.templates: Dict[str, str] = {}

        # Setup Jinja2 environment with dict loader
        self.env = Environment(
            loader=DictLoader(self.templates),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Register custom filters
        self.env.filters['json'] = lambda x: json.dumps(x, indent=2)
        self.env.filters['truncate_list'] = self._truncate_list

    def _truncate_list(self, lst: List[Any], max_items: int = 5) -> List[Any]:
        """Custom filter to truncate long lists"""
        if len(lst) <= max_items:
            return lst
        return lst[:max_items] + [f"... and {len(lst) - max_items} more items"]

    def register_template(self, name: str, template_str: str):
        """Register a template string with a name"""
        self.templates[name] = template_str
        # Update the loader with new templates
        self.env.loader = DictLoader(self.templates)
        logger.debug(f"Registered template: {name}")

    def render(self, template_name: str, **kwargs) -> str:
        """Render a template with context"""
        if template_name not in self.templates:
            raise ValueError(f"Template not found: {template_name}")

        try:
            template = self.env.get_template(template_name)
            return template.render(**kwargs)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {str(e)}")
            raise ValueError(f"Template rendering failed: {str(e)}")

    def render_string(self, template_str: str, **kwargs) -> str:
        """Render a template string directly without registering"""
        try:
            template = self.env.from_string(template_str)
            return template.render(**kwargs)
        except Exception as e:
            logger.error(f"Failed to render template string: {str(e)}")
            raise ValueError(f"Template rendering failed: {str(e)}")

    def list_templates(self) -> List[str]:
        """List all registered template names"""
        return list(self.templates.keys())

    def get_template(self, name: str) -> Optional[str]:
        """Get a registered template string"""
        return self.templates.get(name)

    def clear_templates(self):
        """Clear all registered templates"""
        self.templates.clear()
        self.env.loader = DictLoader(self.templates)


# Global singleton instance
_template_manager: Optional[PromptTemplateManager] = None


def get_template_manager() -> PromptTemplateManager:
    """Get or create the singleton template manager"""
    global _template_manager
    if _template_manager is None:
        _template_manager = PromptTemplateManager()
    return _template_manager