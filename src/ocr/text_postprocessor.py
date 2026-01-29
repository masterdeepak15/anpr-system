"""Text post-processing and format correction"""

import re
from typing import Tuple, Dict, Any, List
import logging

class TextPostProcessor:
    """
    Post-process OCR text:
    - Apply format rules (including multiple Indian formats)
    - Correct common OCR mistakes
    - Validate against patterns
    """
    
    def __init__(self, country_code: str = "IN"):
        """
        Initialize post-processor
        
        Args:
            country_code: Country code for format rules
        """
        self.country_code = country_code
        self.format_rules = self._get_format_rules(country_code)
        self.corrections = self._build_correction_map()
        
        self.logger = logging.getLogger("TextPostProcessor")
    
    def process(self, plate_text: str) -> Tuple[str, bool]:
        """
        Post-process plate text
        
        Args:
            plate_text: Raw OCR text
            
        Returns:
            Tuple of (corrected_text, was_corrected)
        """
        if not plate_text:
            return ("", False)
        
        original_text = plate_text
        
        # Remove spaces
        plate_text = plate_text.replace(" ", "").upper()
        
        # Detect format type (for Indian plates)
        if self.country_code == "IN":
            format_type = self._detect_indian_format(plate_text)
            plate_text = self._apply_indian_corrections(plate_text, format_type)
        else:
            # Apply generic corrections
            plate_text = self._apply_generic_corrections(plate_text)
        
        was_corrected = (plate_text != original_text.replace(" ", "").upper())
        
        return (plate_text, was_corrected)
    
    def _detect_indian_format(self, text: str) -> str:
        """
        Detect which Indian number plate format
        
        Args:
            text: Plate text
            
        Returns:
            str: Format type ('standard', 'bh', 'army', 'temp', 'rental', 'diplomatic', 'unknown')
        """
        # BH Series (Bharat Series) - 22BH1234XX
        if "BH" in text and len(text) >= 10:
            return "bh"
        
        # Temporary Registration - XX00TR0000
        if "TR" in text:
            return "temp"
        
        # Rental/Leased - XX00RC0000
        if "RC" in text:
            return "rental"
        
        # Diplomatic - CC/CD/UN followed by digits
        if text.startswith(("CC", "CD", "UN")) and len(text) >= 7:
            return "diplomatic"
        
        # Army/Defense - 00X00000
        if len(text) >= 8 and text[0:2].isdigit() and text[2].isalpha():
            # Check if rest are digits
            if text[3:].isdigit():
                return "army"
        
        # Standard format - XX00XX0000 (most common)
        if len(text) >= 7 and text[0:2].isalpha() and text[2:4].isdigit():
            return "standard"
        
        return "unknown"
    
    def _apply_indian_corrections(self, text: str, format_type: str) -> str:
        """
        Apply corrections based on detected Indian format
        
        Args:
            text: Input text
            format_type: Detected format type
            
        Returns:
            str: Corrected text
        """
        if format_type == "standard":
            return self._correct_standard_format(text)
        elif format_type == "bh":
            return self._correct_bh_format(text)
        elif format_type == "army":
            return self._correct_army_format(text)
        elif format_type == "temp":
            return self._correct_temp_format(text)
        elif format_type == "rental":
            return self._correct_rental_format(text)
        elif format_type == "diplomatic":
            return self._correct_diplomatic_format(text)
        else:
            return self._apply_generic_corrections(text)
    
    def _correct_standard_format(self, text: str) -> str:
        """
        Correct standard Indian format: XX00XX0000
        Format: State(2) + District(2) + Series(1-2) + Number(1-4)
        Examples: MH12AB1234, DL8CAA9999, KA01A123
        
        Args:
            text: Input text
            
        Returns:
            str: Corrected text
        """
        if len(text) < 7:
            return text
        
        corrected = list(text)
        
        # Position 0-1: State code (must be letters)
        for i in [0, 1]:
            if i < len(corrected) and corrected[i].isdigit():
                corrected[i] = self._digit_to_letter(corrected[i])
        
        # Position 2-3: District code (must be digits)
        for i in [2, 3]:
            if i < len(corrected) and corrected[i].isalpha():
                corrected[i] = self._letter_to_digit(corrected[i])
        
        # Find where series letters end and numbers begin
        # Series can be 1 or 2 letters (positions 4-5 or just 4)
        series_end = 4
        if len(corrected) > 5 and corrected[5].isalpha():
            series_end = 5
        elif len(corrected) > 4 and corrected[4].isalpha():
            series_end = 4
        
        # Series positions: must be letters
        for i in range(4, min(series_end + 1, len(corrected))):
            if corrected[i].isdigit():
                corrected[i] = self._digit_to_letter(corrected[i])
        
        # Remaining positions: must be digits (1-4 digits)
        for i in range(series_end + 1, len(corrected)):
            if corrected[i].isalpha():
                corrected[i] = self._letter_to_digit(corrected[i])
        
        return "".join(corrected)
    
    def _correct_bh_format(self, text: str) -> str:
        """
        Correct BH Series format: 22BH1234XX
        Format: Year(2) + BH + Number(4) + Code(2)
        
        Args:
            text: Input text
            
        Returns:
            str: Corrected text
        """
        corrected = list(text)
        
        # Position 0-1: Year (must be digits)
        for i in [0, 1]:
            if i < len(corrected) and corrected[i].isalpha():
                corrected[i] = self._letter_to_digit(corrected[i])
        
        # Position 2-3: Must be "BH"
        if len(corrected) > 3:
            corrected[2] = 'B'
            corrected[3] = 'H'
        
        # Position 4-7: Number (must be digits)
        for i in range(4, min(8, len(corrected))):
            if corrected[i].isalpha():
                corrected[i] = self._letter_to_digit(corrected[i])
        
        # Position 8-9: Code (must be letters)
        for i in range(8, min(10, len(corrected))):
            if corrected[i].isdigit():
                corrected[i] = self._digit_to_letter(corrected[i])
        
        return "".join(corrected)
    
    def _correct_army_format(self, text: str) -> str:
        """
        Correct Army/Defense format: 00X00000
        Format: Prefix(2 digits) + Code(1 letter) + Number(5 digits)
        
        Args:
            text: Input text
            
        Returns:
            str: Corrected text
        """
        if len(text) < 8:
            return text
        
        corrected = list(text)
        
        # Position 0-1: Must be digits
        for i in [0, 1]:
            if i < len(corrected) and corrected[i].isalpha():
                corrected[i] = self._letter_to_digit(corrected[i])
        
        # Position 2: Must be letter
        if len(corrected) > 2 and corrected[2].isdigit():
            corrected[2] = self._digit_to_letter(corrected[2])
        
        # Position 3-7: Must be digits
        for i in range(3, min(8, len(corrected))):
            if corrected[i].isalpha():
                corrected[i] = self._letter_to_digit(corrected[i])
        
        return "".join(corrected)
    
    def _correct_temp_format(self, text: str) -> str:
        """
        Correct Temporary Registration format: XX00TR0000
        Format: State(2) + District(2) + TR + Number(1-4)
        
        Args:
            text: Input text
            
        Returns:
            str: Corrected text
        """
        corrected = list(text)
        
        # Position 0-1: State (must be letters)
        for i in [0, 1]:
            if i < len(corrected) and corrected[i].isdigit():
                corrected[i] = self._digit_to_letter(corrected[i])
        
        # Position 2-3: District (must be digits)
        for i in [2, 3]:
            if i < len(corrected) and corrected[i].isalpha():
                corrected[i] = self._letter_to_digit(corrected[i])
        
        # Find "TR" in the string
        tr_pos = text.find("TR")
        if tr_pos > 0:
            # Ensure TR is correct
            if tr_pos < len(corrected) - 1:
                corrected[tr_pos] = 'T'
                corrected[tr_pos + 1] = 'R'
                
                # Everything after TR must be digits
                for i in range(tr_pos + 2, len(corrected)):
                    if corrected[i].isalpha():
                        corrected[i] = self._letter_to_digit(corrected[i])
        
        return "".join(corrected)
    
    def _correct_rental_format(self, text: str) -> str:
        """
        Correct Rental/Leased format: XX00RC0000
        Format: State(2) + District(2) + RC + Number(1-4)
        
        Args:
            text: Input text
            
        Returns:
            str: Corrected text
        """
        corrected = list(text)
        
        # Position 0-1: State (must be letters)
        for i in [0, 1]:
            if i < len(corrected) and corrected[i].isdigit():
                corrected[i] = self._digit_to_letter(corrected[i])
        
        # Position 2-3: District (must be digits)
        for i in [2, 3]:
            if i < len(corrected) and corrected[i].isalpha():
                corrected[i] = self._letter_to_digit(corrected[i])
        
        # Find "RC" in the string
        rc_pos = text.find("RC")
        if rc_pos > 0:
            # Ensure RC is correct
            if rc_pos < len(corrected) - 1:
                corrected[rc_pos] = 'R'
                corrected[rc_pos + 1] = 'C'
                
                # Everything after RC must be digits
                for i in range(rc_pos + 2, len(corrected)):
                    if corrected[i].isalpha():
                        corrected[i] = self._letter_to_digit(corrected[i])
        
        return "".join(corrected)
    
    def _correct_diplomatic_format(self, text: str) -> str:
        """
        Correct Diplomatic format: CC/CD/UN + 5-6 digits
        
        Args:
            text: Input text
            
        Returns:
            str: Corrected text
        """
        corrected = list(text)
        
        # First 2 characters must be CC, CD, or UN
        prefix = "".join(corrected[0:2])
        if prefix not in ["CC", "CD", "UN"]:
            # Try to correct
            if corrected[0] == '0' or corrected[0] == 'O':
                corrected[0] = 'C'
            if corrected[1] == '0' or corrected[1] == 'O':
                if corrected[0] == 'C':
                    corrected[1] = 'C'  # CC
                elif corrected[0] == 'U':
                    corrected[1] = 'N'  # UN
        
        # Rest must be digits
        for i in range(2, len(corrected)):
            if corrected[i].isalpha():
                corrected[i] = self._letter_to_digit(corrected[i])
        
        return "".join(corrected)
    
    def _apply_generic_corrections(self, text: str) -> str:
        """
        Apply generic OCR error corrections
        
        Args:
            text: Input text
            
        Returns:
            str: Corrected text
        """
        # Common OCR mistakes
        replacements = {
            "0O": "00",
            "OO": "00",
            "O0": "00",
            "1I": "11",
            "I1": "11",
            "II": "11"
        }
        
        for wrong, correct in replacements.items():
            text = text.replace(wrong, correct)
        
        return text
    
    def _digit_to_letter(self, digit: str) -> str:
        """Convert commonly confused digit to letter"""
        corrections = {
            "0": "O",
            "1": "I",
            "5": "S",
            "8": "B"
        }
        return corrections.get(digit, digit)
    
    def _letter_to_digit(self, letter: str) -> str:
        """Convert commonly confused letter to digit"""
        corrections = {
            "O": "0",
            "I": "1",
            "S": "5",
            "B": "8",
            "Z": "2",
            "G": "6",
            "T": "7"
        }
        return corrections.get(letter, letter)
    
    def _build_correction_map(self) -> Dict[str, str]:
        """
        Build character correction map
        
        Returns:
            Dict mapping incorrect chars to correct ones
        """
        return {
            # Digit to letter
            "0": "O", "1": "I", "5": "S", "8": "B",
            # Letter to digit
            "O": "0", "I": "1", "S": "5", "B": "8", "Z": "2", "G": "6", "T": "7"
        }
    
    def _get_format_rules(self, country_code: str) -> Dict[str, Any]:
        """
        Get format rules for country
        
        Args:
            country_code: Country code
            
        Returns:
            Dict with format rules
        """
        formats = {
            "IN": {
                "patterns": {
                    "standard": r"^[A-Z]{2}\d{2}[A-Z]{1,2}\d{1,4}$",
                    "bh": r"^\d{2}BH\d{4}[A-Z]{2}$",
                    "army": r"^\d{2}[A-Z]\d{5}$",
                    "temp": r"^[A-Z]{2}\d{2}TR\d{1,4}$",
                    "rental": r"^[A-Z]{2}\d{2}RC\d{1,4}$",
                    "diplomatic": r"^(CC|CD|UN)\d{5,6}$"
                },
                "description": "Indian number plates (multiple formats)"
            },
            "US": {
                "patterns": {
                    "standard": r"^[A-Z0-9]{2,8}$"
                },
                "description": "US format: 2-8 alphanumeric"
            },
            "UK": {
                "patterns": {
                    "standard": r"^[A-Z]{2}\d{2}[A-Z]{3}$"
                },
                "description": "UK format: XX00XXX"
            }
        }
        
        return formats.get(country_code, formats["IN"])
    
    def set_country(self, country_code: str) -> None:
        """
        Update country format
        
        Args:
            country_code: New country code
        """
        self.country_code = country_code
        self.format_rules = self._get_format_rules(country_code)
        self.logger.info(f"Format updated to: {country_code}")
    
    def validate_format(self, text: str) -> bool:
        """
        Validate text against all format patterns
        
        Args:
            text: Plate text
            
        Returns:
            bool: True if valid against any pattern
        """
        patterns = self.format_rules.get("patterns", {})
        
        # Check against all patterns
        for pattern_name, pattern in patterns.items():
            if re.match(pattern, text):
                self.logger.debug(f"Matched format: {pattern_name}")
                return True
        
        return False
    
    def get_format_type(self, text: str) -> str:
        """
        Get the format type of the plate text
        
        Args:
            text: Plate text
            
        Returns:
            str: Format type name or 'unknown'
        """
        if self.country_code == "IN":
            return self._detect_indian_format(text)
        
        patterns = self.format_rules.get("patterns", {})
        for pattern_name, pattern in patterns.items():
            if re.match(pattern, text):
                return pattern_name
        
        return "unknown"
    
    def __repr__(self) -> str:
        return f"TextPostProcessor(country={self.country_code})"