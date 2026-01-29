"""Country-specific number plate formats"""

from typing import Dict
import re

class CountryFormats:
    """
    Repository of country-specific number plate formats
    
    Contains regex patterns for different countries
    """
    
    def __init__(self):
        """Initialize country formats"""
        self.formats = self._load_formats()
    
    def _load_formats(self) -> Dict[str, Dict[str, str]]:
        """
        Load all country formats
        
        Returns:
            Dict: Country code -> format patterns
        """
        return {
            "IN": self._get_indian_formats(),
            "US": self._get_us_formats(),
            "UK": self._get_uk_formats(),
            "DE": self._get_german_formats(),
            "FR": self._get_french_formats(),
            "AU": self._get_australian_formats(),
            "CA": self._get_canadian_formats()
        }
    
    def _get_indian_formats(self) -> Dict[str, str]:
        """Indian number plate formats"""
        return {
            "standard": r"^[A-Z]{2}\d{2}[A-Z]{1,2}\d{1,4}$",
            "bh_series": r"^\d{2}BH\d{4}[A-Z]{2}$",
            "army": r"^\d{2}[A-Z]\d{5}$",
            "temporary": r"^[A-Z]{2}\d{2}TR\d{1,4}$",
            "rental": r"^[A-Z]{2}\d{2}RC\d{1,4}$",
            "diplomatic": r"^(CC|CD|UN)\d{5,6}$"
        }
    
    def _get_us_formats(self) -> Dict[str, str]:
        """US number plate formats (varies by state)"""
        return {
            "standard": r"^[A-Z0-9]{2,8}$",
            "california": r"^[0-9][A-Z]{3}[0-9]{3}$",
            "new_york": r"^[A-Z]{3}[0-9]{4}$",
            "texas": r"^[A-Z]{3}[0-9]{4}$",
            "florida": r"^[A-Z]{3}[0-9]{3}$"
        }
    
    def _get_uk_formats(self) -> Dict[str, str]:
        """UK number plate formats"""
        return {
            "current": r"^[A-Z]{2}\d{2}[A-Z]{3}$",
            "prefix": r"^[A-Z]\d{1,3}[A-Z]{3}$",
            "suffix": r"^[A-Z]{3}\d{1,3}[A-Z]$",
            "dateless": r"^[A-Z]{1,3}\d{1,4}$"
        }
    
    def _get_german_formats(self) -> Dict[str, str]:
        """German number plate formats"""
        return {
            "standard": r"^[A-Z]{1,3}[A-Z]{1,2}\d{1,4}$",
            "electric": r"^[A-Z]{1,3}[A-Z]{1,2}\d{1,4}E$"
        }
    
    def _get_french_formats(self) -> Dict[str, str]:
        """French number plate formats"""
        return {
            "current": r"^[A-Z]{2}\d{3}[A-Z]{2}$",
            "old": r"^\d{1,4}[A-Z]{1,3}\d{2}$"
        }
    
    def _get_australian_formats(self) -> Dict[str, str]:
        """Australian number plate formats"""
        return {
            "standard": r"^[A-Z0-9]{6}$",
            "custom": r"^[A-Z0-9]{2,6}$"
        }
    
    def _get_canadian_formats(self) -> Dict[str, str]:
        """Canadian number plate formats"""
        return {
            "standard": r"^[A-Z]{4}\d{3}$",
            "ontario": r"^[A-Z]{4}\d{3}$",
            "quebec": r"^[A-Z]{3}\d{3}$"
        }
    
    def get_formats(self, country_code: str) -> Dict[str, str]:
        """
        Get formats for a country
        
        Args:
            country_code: ISO country code
            
        Returns:
            Dict: Format name -> regex pattern
        """
        return self.formats.get(country_code, {})
    
    def validate_against_country(self, plate_text: str, country_code: str) -> bool:
        """
        Validate plate against country formats
        
        Args:
            plate_text: Plate text
            country_code: Country code
            
        Returns:
            bool: True if matches any format
        """
        formats = self.get_formats(country_code)
        
        for pattern in formats.values():
            if re.match(pattern, plate_text):
                return True
        
        return False
    
    def detect_country(self, plate_text: str) -> str:
        """
        Attempt to detect country from plate text
        
        Args:
            plate_text: Plate text
            
        Returns:
            str: Detected country code or "UNKNOWN"
        """
        for country_code, formats in self.formats.items():
            for pattern in formats.values():
                if re.match(pattern, plate_text):
                    return country_code
        
        return "UNKNOWN"
    
    def add_custom_format(
        self,
        country_code: str,
        format_name: str,
        pattern: str
    ) -> None:
        """
        Add custom format for a country
        
        Args:
            country_code: Country code
            format_name: Format name
            pattern: Regex pattern
        """
        if country_code not in self.formats:
            self.formats[country_code] = {}
        
        self.formats[country_code][format_name] = pattern
    
    def __repr__(self) -> str:
        return f"CountryFormats(countries={len(self.formats)})"