"""Input Validator - Character forensics and input sanitization.

This module implements the S06 steal from Eye-of-Sauron: comprehensive input
validation with character-level forensics to detect injection attacks, encoding
issues, and malicious patterns.

Validates all user input before it enters the system, preventing:
- SQL injection
- Command injection
- Path traversal
- Unicode encoding attacks
- Homoglyph attacks
- Control character injection
"""

import re
import unicodedata
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ValidationLevel(str, Enum):
    """Validation strictness levels."""

    PERMISSIVE = "permissive"  # Allow most input, warn on suspicious patterns
    STANDARD = "standard"  # Balance security and usability (default)
    STRICT = "strict"  # Maximum security, reject anything questionable
    PARANOID = "paranoid"  # Ultra-strict, reject even borderline safe input


class ValidationViolation(BaseModel):
    """A validation rule violation."""

    rule: str = Field(..., description="Rule that was violated")
    severity: str = Field(..., description="Severity: low, medium, high, critical")
    message: str = Field(..., description="Human-readable explanation")
    location: int | None = Field(default=None, description="Character position (if applicable)")
    character: str | None = Field(default=None, description="Offending character (if applicable)")
    suggestion: str | None = Field(default=None, description="How to fix")

    model_config = {"frozen": True}


class ValidationResult(BaseModel):
    """Result of input validation."""

    valid: bool = Field(..., description="Whether input passed validation")
    violations: list[ValidationViolation] = Field(
        default_factory=list, description="List of violations found"
    )
    sanitized: str | None = Field(
        default=None, description="Sanitized version (if auto-fix attempted)"
    )
    warnings: list[str] = Field(default_factory=list, description="Non-fatal warnings")

    model_config = {"frozen": True}

    def is_safe(self) -> bool:
        """Check if input is safe (valid or only low-severity violations)."""
        if self.valid:
            return True
        return all(v.severity == "low" for v in self.violations)

    def has_critical_violations(self) -> bool:
        """Check if any violations are critical severity."""
        return any(v.severity == "critical" for v in self.violations)

    def has_high_violations(self) -> bool:
        """Check if any violations are high severity."""
        return any(v.severity in ("high", "critical") for v in self.violations)


class InputValidator:
    """Validates and sanitizes user input with character-level forensics.

    Examples:
        >>> validator = InputValidator()
        >>>
        >>> # Valid input
        >>> result = validator.validate_string("react", field_name="package_name")
        >>> result.valid
        True
        >>>
        >>> # SQL injection attempt
        >>> result = validator.validate_string(
        ...     "'; DROP TABLE users; --",
        ...     field_name="search_query"
        ... )
        >>> result.valid
        False
        >>> result.violations[0].severity
        'critical'
        >>>
        >>> # Path traversal attempt
        >>> result = validator.validate_string(
        ...     "../../../etc/passwd",
        ...     field_name="file_path"
        ... )
        >>> result.valid
        False
    """

    # Dangerous patterns that indicate injection attacks
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|/\*|\*/)",  # SQL comments
        r"(;.*?--)",  # Command chaining with comment
        r"(\bunion\b.*?\bselect\b)",  # UNION-based injection
        r"(\bor\b.*?=.*?)",  # OR-based injection
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$()]",  # Shell metacharacters
        r"(\$\(.*?\))",  # Command substitution
        r"(`.*?`)",  # Backtick execution
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",  # Directory traversal
        r"\.\./\.\./",  # Multiple levels
        r"\.\.\\",  # Windows path traversal
    ]

    # Suspicious Unicode patterns
    ZERO_WIDTH_CHARS = [
        "\u200B",  # Zero-width space
        "\u200C",  # Zero-width non-joiner
        "\u200D",  # Zero-width joiner
        "\uFEFF",  # Zero-width no-break space
    ]

    # Control characters (except tab, newline, carriage return)
    CONTROL_CHARS = [chr(i) for i in range(32) if i not in (9, 10, 13)]

    def __init__(self, level: ValidationLevel = ValidationLevel.STANDARD) -> None:
        """Initialize validator with specified strictness level.

        Args:
            level: Validation strictness (default: STANDARD)
        """
        self.level = level

    def validate_string(
        self,
        value: str,
        field_name: str,
        max_length: int | None = None,
        min_length: int = 0,
        allow_unicode: bool = True,
        allow_whitespace: bool = True,
    ) -> ValidationResult:
        """Validate a string value with character forensics.

        Args:
            value: String to validate
            field_name: Name of field (for error messages)
            max_length: Maximum allowed length
            min_length: Minimum required length
            allow_unicode: Whether to allow non-ASCII characters
            allow_whitespace: Whether to allow whitespace characters

        Returns:
            ValidationResult with detailed findings
        """
        violations: list[ValidationViolation] = []
        warnings: list[str] = []

        # Basic length checks
        if len(value) < min_length:
            violations.append(
                ValidationViolation(
                    rule="min_length",
                    severity="high",
                    message=f"{field_name} must be at least {min_length} characters",
                    suggestion=f"Provide a longer value (min: {min_length})",
                )
            )

        if max_length and len(value) > max_length:
            violations.append(
                ValidationViolation(
                    rule="max_length",
                    severity="high",
                    message=f"{field_name} exceeds max length of {max_length}",
                    suggestion=f"Shorten to {max_length} characters or less",
                )
            )

        # Check for SQL injection patterns
        sql_violations = self._check_sql_injection(value, field_name)
        violations.extend(sql_violations)

        # Check for command injection patterns
        cmd_violations = self._check_command_injection(value, field_name)
        violations.extend(cmd_violations)

        # Check for path traversal
        path_violations = self._check_path_traversal(value, field_name)
        violations.extend(path_violations)

        # Check for dangerous Unicode
        unicode_violations = self._check_unicode_attacks(value, field_name)
        violations.extend(unicode_violations)

        # Check for control characters
        control_violations = self._check_control_characters(value, field_name)
        violations.extend(control_violations)

        # Check for non-ASCII if not allowed
        if not allow_unicode:
            for i, char in enumerate(value):
                if ord(char) > 127:
                    violations.append(
                        ValidationViolation(
                            rule="non_ascii",
                            severity="medium",
                            message=f"Non-ASCII character in {field_name}",
                            location=i,
                            character=char,
                            suggestion="Use only ASCII characters",
                        )
                    )

        # Check for whitespace if not allowed
        if not allow_whitespace and any(c.isspace() for c in value):
            violations.append(
                ValidationViolation(
                    rule="no_whitespace",
                    severity="medium",
                    message=f"Whitespace not allowed in {field_name}",
                    suggestion="Remove spaces and whitespace characters",
                )
            )

        # Check for homoglyph attacks (look-alike characters)
        homoglyph_warnings = self._check_homoglyphs(value, field_name)
        warnings.extend(homoglyph_warnings)

        # Attempt sanitization if violations found
        sanitized = None
        if violations:
            sanitized = self._sanitize(value)

        return ValidationResult(
            valid=len(violations) == 0,
            violations=violations,
            sanitized=sanitized,
            warnings=warnings,
        )

    def validate_identifier(
        self,
        value: str,
        field_name: str = "identifier",
    ) -> ValidationResult:
        """Validate an identifier (package name, entity name, etc).

        Identifiers must:
        - Be 1-500 characters
        - Contain only alphanumeric, dash, underscore, dot, slash
        - Not start with special characters
        - Not contain path traversal sequences

        Args:
            value: Identifier to validate
            field_name: Name of field (for error messages)

        Returns:
            ValidationResult
        """
        violations: list[ValidationViolation] = []

        # Length check
        if not 1 <= len(value) <= 500:
            violations.append(
                ValidationViolation(
                    rule="identifier_length",
                    severity="high",
                    message=f"{field_name} must be 1-500 characters",
                )
            )

        # Character check: alphanumeric + - _ . / @
        allowed_pattern = r"^[a-zA-Z0-9\-_./@]+$"
        if not re.match(allowed_pattern, value):
            violations.append(
                ValidationViolation(
                    rule="identifier_chars",
                    severity="high",
                    message=f"{field_name} contains invalid characters",
                    suggestion="Use only: a-z A-Z 0-9 - _ . / @",
                )
            )

        # Must not start with special chars
        if value and value[0] in "-_./@":
            violations.append(
                ValidationViolation(
                    rule="identifier_start",
                    severity="medium",
                    message=f"{field_name} cannot start with special character",
                    suggestion="Start with alphanumeric character",
                )
            )

        # No path traversal
        if ".." in value:
            violations.append(
                ValidationViolation(
                    rule="path_traversal",
                    severity="critical",
                    message="Path traversal sequence detected",
                )
            )

        return ValidationResult(
            valid=len(violations) == 0,
            violations=violations,
        )

    def validate_version(
        self,
        value: str,
        field_name: str = "version",
    ) -> ValidationResult:
        """Validate a version string.

        Accepts:
        - Semantic versions: 1.2.3, 1.0.0-alpha, 2.1.0+build123
        - Git refs: commit hashes, branch names, tags
        - Version ranges: ^1.2.3, ~2.0.0, >=3.0.0

        Args:
            value: Version to validate
            field_name: Name of field (for error messages)

        Returns:
            ValidationResult
        """
        violations: list[ValidationViolation] = []

        # Length check
        if len(value) > 200:
            violations.append(
                ValidationViolation(
                    rule="version_length",
                    severity="high",
                    message=f"{field_name} exceeds max length of 200",
                )
            )

        # Character check: alphanumeric + . - + ^ ~ < > = *
        allowed_pattern = r"^[a-zA-Z0-9.\-+^~<>=*]+$"
        if not re.match(allowed_pattern, value):
            violations.append(
                ValidationViolation(
                    rule="version_chars",
                    severity="high",
                    message=f"{field_name} contains invalid characters",
                    suggestion="Use only: a-z A-Z 0-9 . - + ^ ~ < > = *",
                )
            )

        return ValidationResult(
            valid=len(violations) == 0,
            violations=violations,
        )

    # Private helper methods

    def _check_sql_injection(self, value: str, field_name: str) -> list[ValidationViolation]:
        """Check for SQL injection patterns."""
        violations: list[ValidationViolation] = []

        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                violations.append(
                    ValidationViolation(
                        rule="sql_injection",
                        severity="critical",
                        message=f"SQL injection pattern detected in {field_name}",
                        suggestion="Remove SQL keywords and special characters",
                    )
                )
                break  # One violation is enough

        return violations

    def _check_command_injection(
        self, value: str, field_name: str
    ) -> list[ValidationViolation]:
        """Check for command injection patterns."""
        violations: list[ValidationViolation] = []

        for pattern in self.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value):
                violations.append(
                    ValidationViolation(
                        rule="command_injection",
                        severity="critical",
                        message=f"Command injection pattern detected in {field_name}",
                        suggestion="Remove shell metacharacters",
                    )
                )
                break

        return violations

    def _check_path_traversal(self, value: str, field_name: str) -> list[ValidationViolation]:
        """Check for path traversal patterns."""
        violations: list[ValidationViolation] = []

        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value):
                violations.append(
                    ValidationViolation(
                        rule="path_traversal",
                        severity="critical",
                        message=f"Path traversal detected in {field_name}",
                        suggestion="Remove directory traversal sequences",
                    )
                )
                break

        return violations

    def _check_unicode_attacks(self, value: str, field_name: str) -> list[ValidationViolation]:
        """Check for Unicode-based attacks."""
        violations: list[ValidationViolation] = []

        # Check for zero-width characters
        for i, char in enumerate(value):
            if char in self.ZERO_WIDTH_CHARS:
                violations.append(
                    ValidationViolation(
                        rule="zero_width_char",
                        severity="high",
                        message=f"Zero-width character in {field_name}",
                        location=i,
                        character=repr(char),
                        suggestion="Remove invisible characters",
                    )
                )

        # Check for right-to-left override (text direction manipulation)
        rtl_chars = ["\u202E", "\u202D"]  # RLO, LRO
        for i, char in enumerate(value):
            if char in rtl_chars:
                violations.append(
                    ValidationViolation(
                        rule="rtl_override",
                        severity="high",
                        message=f"Text direction override in {field_name}",
                        location=i,
                        character=repr(char),
                        suggestion="Remove direction control characters",
                    )
                )

        return violations

    def _check_control_characters(
        self, value: str, field_name: str
    ) -> list[ValidationViolation]:
        """Check for dangerous control characters."""
        violations: list[ValidationViolation] = []

        for i, char in enumerate(value):
            if char in self.CONTROL_CHARS:
                violations.append(
                    ValidationViolation(
                        rule="control_char",
                        severity="medium",
                        message=f"Control character in {field_name}",
                        location=i,
                        character=repr(char),
                        suggestion="Remove control characters",
                    )
                )

        return violations

    def _check_homoglyphs(self, value: str, field_name: str) -> list[str]:
        """Check for homoglyph attacks (look-alike characters).

        Returns warnings (not violations) since these may be legitimate.
        """
        warnings: list[str] = []

        # Common homoglyphs (Cyrillic, Greek lookalikes)
        homoglyph_pairs = [
            ("a", "а"),  # Latin vs Cyrillic
            ("e", "е"),
            ("o", "о"),
            ("p", "р"),
            ("c", "с"),
            ("x", "х"),
            ("y", "у"),
        ]

        for latin, lookalike in homoglyph_pairs:
            if lookalike in value:
                warnings.append(
                    f"Possible homoglyph attack in {field_name}: "
                    f"'{lookalike}' looks like '{latin}' but isn't"
                )

        return warnings

    def _sanitize(self, value: str) -> str:
        """Attempt to sanitize dangerous input.

        Removes:
        - SQL/command injection characters
        - Control characters
        - Zero-width characters
        - Path traversal sequences

        Args:
            value: String to sanitize

        Returns:
            Sanitized string
        """
        # Remove zero-width characters
        sanitized = value
        for char in self.ZERO_WIDTH_CHARS:
            sanitized = sanitized.replace(char, "")

        # Remove control characters
        for char in self.CONTROL_CHARS:
            sanitized = sanitized.replace(char, "")

        # Remove common injection characters
        dangerous = [";", "|", "&", "`", "$", "(", ")", "<", ">"]
        for char in dangerous:
            sanitized = sanitized.replace(char, "")

        # Remove path traversal
        sanitized = sanitized.replace("../", "").replace("..\\", "")

        # Normalize Unicode
        sanitized = unicodedata.normalize("NFKC", sanitized)

        return sanitized
