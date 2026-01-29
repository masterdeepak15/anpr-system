"""Validation rule definitions"""

from typing import Callable, Dict, Any, List
from dataclasses import dataclass

@dataclass
class ValidationRule:
    """
    Single validation rule
    
    Attributes:
        name: Rule name
        validator: Validation function
        weight: Rule importance (default 1.0)
    """
    name: str
    validator: Callable[[str, Dict], bool]
    weight: float = 1.0
    
    def validate(self, plate_text: str, metadata: Dict = None) -> bool:
        """
        Execute validation
        
        Args:
            plate_text: Plate text to validate
            metadata: Additional metadata
            
        Returns:
            bool: True if validation passes
        """
        return self.validator(plate_text, metadata or {})
    
    def __repr__(self) -> str:
        return f"ValidationRule(name='{self.name}', weight={self.weight})"


class RuleSet:
    """
    Collection of validation rules
    
    Allows grouping and managing multiple rules
    """
    
    def __init__(self, name: str):
        """
        Initialize rule set
        
        Args:
            name: Rule set name
        """
        self.name = name
        self.rules: List[ValidationRule] = []
    
    def add_rule(
        self,
        name: str,
        validator: Callable[[str, Dict], bool],
        weight: float = 1.0
    ) -> None:
        """
        Add rule to set
        
        Args:
            name: Rule name
            validator: Validation function
            weight: Rule weight
        """
        rule = ValidationRule(name, validator, weight)
        self.rules.append(rule)
    
    def validate(self, plate_text: str, metadata: Dict = None) -> bool:
        """
        Validate against all rules in set
        
        Args:
            plate_text: Plate text
            metadata: Additional metadata
            
        Returns:
            bool: True if passes majority of weighted rules
        """
        if not self.rules:
            return True
        
        total_weight = sum(rule.weight for rule in self.rules)
        passed_weight = 0.0
        
        for rule in self.rules:
            if rule.validate(plate_text, metadata):
                passed_weight += rule.weight
        
        return (passed_weight / total_weight) >= 0.5 if total_weight > 0 else False
    
    def get_score(self, plate_text: str, metadata: Dict = None) -> float:
        """
        Get validation score for rule set
        
        Args:
            plate_text: Plate text
            metadata: Additional metadata
            
        Returns:
            float: Score between 0 and 1
        """
        if not self.rules:
            return 1.0
        
        total_weight = sum(rule.weight for rule in self.rules)
        if total_weight == 0:
            return 0.0
        
        passed_weight = 0.0
        
        for rule in self.rules:
            try:
                if rule.validate(plate_text, metadata):
                    passed_weight += rule.weight
            except:
                pass
        
        return passed_weight / total_weight
    
    def __len__(self) -> int:
        return len(self.rules)
    
    def __repr__(self) -> str:
        return f"RuleSet(name='{self.name}', rules={len(self.rules)})"


# Predefined rule sets

def create_strict_ruleset(country_code: str) -> RuleSet:
    """
    Create strict validation rule set
    
    Args:
        country_code: Country code
        
    Returns:
        RuleSet: Strict validation rules
    """
    ruleset = RuleSet(f"strict_{country_code}")
    
    # Add strict rules
    ruleset.add_rule(
        "no_special_chars",
        lambda text, meta: text.isalnum(),
        weight=2.0
    )
    
    ruleset.add_rule(
        "min_length",
        lambda text, meta: len(text) >= 6,
        weight=1.5
    )
    
    ruleset.add_rule(
        "max_length",
        lambda text, meta: len(text) <= 12,
        weight=1.5
    )
    
    return ruleset


def create_lenient_ruleset() -> RuleSet:
    """
    Create lenient validation rule set
    
    Returns:
        RuleSet: Lenient validation rules
    """
    ruleset = RuleSet("lenient")
    
    ruleset.add_rule(
        "not_empty",
        lambda text, meta: len(text) > 0,
        weight=1.0
    )
    
    ruleset.add_rule(
        "alphanumeric",
        lambda text, meta: text.replace(" ", "").isalnum(),
        weight=1.0
    )
    
    return ruleset