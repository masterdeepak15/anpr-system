"""Validation engine with extensible rules"""

import re
from typing import List, Dict, Any, Callable
import logging

from ..core.interfaces import IValidator
from .validation_rules import ValidationRule, RuleSet
from .country_formats import CountryFormats

class ValidationEngine(IValidator):
    """
    Extensible validation engine
    
    Validates plate text against multiple rules:
    - Format rules (regex patterns)
    - Length rules
    - Character position rules
    - Custom rules
    """
    
    def __init__(self, country_code: str = "IN"):
        """
        Initialize validation engine
        
        Args:
            country_code: Country code for format rules
        """
        self.country_code = country_code
        self.rules: List[ValidationRule] = []
        self.formats = CountryFormats()
        
        self.logger = logging.getLogger("ValidationEngine")
        
        # Initialize default rules
        self._init_default_rules()
    
    def _init_default_rules(self) -> None:
        """Initialize country-specific validation rules"""
        
        if self.country_code == "IN":
            self._init_indian_rules()
        elif self.country_code == "US":
            self._init_us_rules()
        elif self.country_code == "UK":
            self._init_uk_rules()
        else:
            self._init_generic_rules()
    
    def _init_indian_rules(self) -> None:
        """Initialize Indian number plate validation rules"""
        
        # Get Indian formats
        indian_formats = self.formats.get_formats("IN")
        
        # Rule 1: Format pattern check (high weight)
        def check_format(text: str, meta: Dict) -> bool:
            for pattern_name, pattern in indian_formats.items():
                if re.match(pattern, text):
                    return True
            return False
        
        self.add_rule("format_check", check_format, weight=3.0)
        
        # Rule 2: Length check
        def check_length(text: str, meta: Dict) -> bool:
            return 7 <= len(text) <= 10
        
        self.add_rule("length_check", check_length, weight=1.0)
        
        # Rule 3: No consecutive identical characters (unlikely)
        def no_repetition(text: str, meta: Dict) -> bool:
            return not re.search(r"(.)\1{3,}", text)
        
        self.add_rule("no_repetition", no_repetition, weight=0.5)
        
        # Rule 4: Valid state codes (for standard format)
        valid_states = {
            "AP", "AR", "AS", "BR", "CG", "GA", "GJ", "HR", "HP", "JH",
            "KA", "KL", "MP", "MH", "MN", "ML", "MZ", "NL", "OD", "PB",
            "RJ", "SK", "TN", "TS", "TR", "UP", "UK", "WB",
            "AN", "CH", "DN", "DD", "DL", "LD", "PY", "LA"
        }
        
        def valid_state_code(text: str, meta: Dict) -> bool:
            if len(text) >= 2:
                state_code = text[:2]
                # Check if it's a standard format plate
                if state_code.isalpha():
                    return state_code in valid_states
            return True  # Not applicable for non-standard formats
        
        self.add_rule("valid_state_code", valid_state_code, weight=1.5)
        
        # Rule 5: Valid district code (01-99 for standard format)
        def valid_district_code(text: str, meta: Dict) -> bool:
            if len(text) >= 4 and text[:2].isalpha() and text[2:4].isdigit():
                district = int(text[2:4])
                return 1 <= district <= 99
            return True  # Not applicable for non-standard formats
        
        self.add_rule("valid_district_code", valid_district_code, weight=1.0)
        
        # Rule 6: Alphanumeric only
        def alphanumeric_only(text: str, meta: Dict) -> bool:
            return text.isalnum()
        
        self.add_rule("alphanumeric_only", alphanumeric_only, weight=2.0)
    
    def _init_us_rules(self) -> None:
        """Initialize US number plate validation rules"""
        
        us_formats = self.formats.get_formats("US")
        
        def check_format(text: str, meta: Dict) -> bool:
            for pattern in us_formats.values():
                if re.match(pattern, text):
                    return True
            return False
        
        self.add_rule("format_check", check_format, weight=2.0)
        
        def check_length(text: str, meta: Dict) -> bool:
            return 2 <= len(text) <= 8
        
        self.add_rule("length_check", check_length, weight=1.0)
    
    def _init_uk_rules(self) -> None:
        """Initialize UK number plate validation rules"""
        
        uk_formats = self.formats.get_formats("UK")
        
        def check_format(text: str, meta: Dict) -> bool:
            for pattern in uk_formats.values():
                if re.match(pattern, text):
                    return True
            return False
        
        self.add_rule("format_check", check_format, weight=2.0)
        
        def check_length(text: str, meta: Dict) -> bool:
            return len(text) == 7
        
        self.add_rule("length_check", check_length, weight=1.0)
    
    def _init_generic_rules(self) -> None:
        """Initialize generic validation rules"""
        
        def alphanumeric_only(text: str, meta: Dict) -> bool:
            return text.isalnum()
        
        self.add_rule("alphanumeric_only", alphanumeric_only, weight=1.0)
        
        def min_length(text: str, meta: Dict) -> bool:
            return len(text) >= 4
        
        self.add_rule("min_length", min_length, weight=1.0)
    
    def add_rule(
        self,
        name: str,
        validator: Callable[[str, Dict], bool],
        weight: float = 1.0
    ) -> None:
        """
        Add a custom validation rule
        
        Args:
            name: Rule name
            validator: Validation function
            weight: Rule weight (importance)
        """
        rule = ValidationRule(name, validator, weight)
        self.rules.append(rule)
        self.logger.debug(f"Added validation rule: {name} (weight: {weight})")
    
    def validate(self, plate_text: str, metadata: Dict = None) -> bool:
        """
        Validate plate text against all rules
        
        Args:
            plate_text: Plate text to validate
            metadata: Additional metadata
            
        Returns:
            bool: True if passes validation threshold (70%)
        """
        if not plate_text or len(plate_text) == 0:
            return False
        
        score = self.get_validation_score(plate_text, metadata)
        
        # Pass if score >= 70%
        threshold = 0.7
        passed = score >= threshold
        
        if not passed:
            failed_rules = self.get_failed_rules(plate_text, metadata)
            self.logger.debug(
                f"Validation failed for '{plate_text}' - "
                f"Score: {score:.2f}, Failed rules: {failed_rules}"
            )
        
        return passed
    
    def get_validation_score(self, plate_text: str, metadata: Dict = None) -> float:
        """
        Get validation score (0.0 to 1.0)
        
        Args:
            plate_text: Plate text to score
            metadata: Additional metadata
            
        Returns:
            float: Validation score
        """
        if not plate_text:
            return 0.0
        
        total_weight = sum(rule.weight for rule in self.rules)
        if total_weight == 0:
            return 0.0
        
        passed_weight = 0.0
        meta = metadata or {}
        
        for rule in self.rules:
            try:
                if rule.validate(plate_text, meta):
                    passed_weight += rule.weight
            except Exception as e:
                self.logger.warning(f"Rule '{rule.name}' error: {e}")
        
        return passed_weight / total_weight
    
    def get_failed_rules(self, plate_text: str, metadata: Dict = None) -> List[str]:
        """
        Get list of failed rule names
        
        Args:
            plate_text: Plate text
            metadata: Additional metadata
            
        Returns:
            List[str]: Failed rule names
        """
        failed = []
        meta = metadata or {}
        
        for rule in self.rules:
            try:
                if not rule.validate(plate_text, meta):
                    failed.append(rule.name)
            except Exception as e:
                failed.append(f"{rule.name} (error: {e})")
        
        return failed
    
    def get_detailed_validation(self, plate_text: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        Get detailed validation report
        
        Args:
            plate_text: Plate text
            metadata: Additional metadata
            
        Returns:
            Dict: Detailed validation information
        """
        meta = metadata or {}
        rule_results = []
        
        for rule in self.rules:
            try:
                passed = rule.validate(plate_text, meta)
                rule_results.append({
                    "name": rule.name,
                    "passed": passed,
                    "weight": rule.weight
                })
            except Exception as e:
                rule_results.append({
                    "name": rule.name,
                    "passed": False,
                    "weight": rule.weight,
                    "error": str(e)
                })
        
        score = self.get_validation_score(plate_text, meta)
        
        return {
            "plate_text": plate_text,
            "valid": score >= 0.7,
            "score": score,
            "rules": rule_results,
            "failed_rules": self.get_failed_rules(plate_text, meta)
        }
    
    def set_country(self, country_code: str) -> None:
        """
        Update country and reinitialize rules
        
        Args:
            country_code: New country code
        """
        self.country_code = country_code
        self.rules.clear()
        self._init_default_rules()
        self.logger.info(f"Validation rules updated for: {country_code}")
    
    def __repr__(self) -> str:
        return f"ValidationEngine(country={self.country_code}, rules={len(self.rules)})"