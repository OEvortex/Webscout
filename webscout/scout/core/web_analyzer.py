"""
Scout Web Analyzer Module
"""

from typing import Any, Dict, Optional

from ..element import Tag


class ScoutWebAnalyzer:
    """
    Advanced web content analysis utility.
    """
    @staticmethod
    def analyze_page_structure(scout_obj) -> Dict[str, Any]:
        """
        Analyze the structure of a web page.

        Args:
            scout_obj: Parsed Scout object

        Returns:
            Dict[str, Any]: Page structure analysis
        """
        analysis = {
            'tag_distribution': {},
            'class_distribution': {},
            'id_distribution': {},
            'depth_analysis': {}
        }

        # Tag distribution
        for tag in scout_obj.find_all():
            analysis['tag_distribution'][tag.name] = analysis['tag_distribution'].get(tag.name, 0) + 1

        # Class distribution
        for tag in scout_obj.find_all(attrs={'class': True}):
            for cls in tag.get('class', []):
                analysis['class_distribution'][cls] = analysis['class_distribution'].get(cls, 0) + 1

        # ID distribution
        for tag in scout_obj.find_all(attrs={'id': True}):
            analysis['id_distribution'][tag.get('id')] = analysis['id_distribution'].get(tag.get('id'), 0) + 1

        # Depth analysis
        def _analyze_depth(tag, current_depth=0):
            analysis['depth_analysis'][current_depth] = analysis['depth_analysis'].get(current_depth, 0) + 1
            for child in tag.contents:
                if isinstance(child, Tag):
                    _analyze_depth(child, current_depth + 1)

        _analyze_depth(scout_obj._soup)

        return analysis
