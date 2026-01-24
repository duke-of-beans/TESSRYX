"""Unit tests for Input Validator.

Tests the S06 steal from Eye-of-Sauron: character forensics and input
sanitization to prevent injection attacks.
"""

import pytest

from tessryx.kernel.validator import InputValidator, ValidationLevel, ValidationResult


class TestInputValidator:
    """Tests for InputValidator class."""

    def test_init_default_level(self) -> None:
        """Test creating validator with default strictness."""
        validator = InputValidator()
        assert validator.level == ValidationLevel.STANDARD

    def test_init_custom_level(self) -> None:
        """Test creating validator with custom strictness."""
        validator = InputValidator(level=ValidationLevel.STRICT)
        assert validator.level == ValidationLevel.STRICT

    def test_validate_simple_string(self) -> None:
        """Test validating a simple, safe string."""
        validator = InputValidator()

        result = validator.validate_string("react", field_name="package_name")

        assert result.valid
        assert len(result.violations) == 0
        assert len(result.warnings) == 0

    def test_validate_string_with_numbers(self) -> None:
        """Test validating string with numbers."""
        validator = InputValidator()

        result = validator.validate_string("package123", field_name="name")

        assert result.valid

    def test_min_length_violation(self) -> None:
        """Test minimum length validation."""
        validator = InputValidator()

        result = validator.validate_string("ab", field_name="name", min_length=3)

        assert not result.valid
        assert any(v.rule == "min_length" for v in result.violations)
        assert any(v.severity == "high" for v in result.violations)

    def test_max_length_violation(self) -> None:
        """Test maximum length validation."""
        validator = InputValidator()

        result = validator.validate_string("a" * 200, field_name="name", max_length=100)

        assert not result.valid
        assert any(v.rule == "max_length" for v in result.violations)

    def test_sql_injection_select(self) -> None:
        """Test detecting SQL injection with SELECT."""
        validator = InputValidator()

        result = validator.validate_string(
            "'; SELECT * FROM users; --",
            field_name="search_query",
        )

        assert not result.valid
        assert any(v.rule == "sql_injection" for v in result.violations)
        assert any(v.severity == "critical" for v in result.violations)

    def test_sql_injection_drop_table(self) -> None:
        """Test detecting SQL injection with DROP TABLE."""
        validator = InputValidator()

        result = validator.validate_string(
            "'; DROP TABLE users; --",
            field_name="input",
        )

        assert not result.valid
        assert result.has_critical_violations()

    def test_sql_injection_union(self) -> None:
        """Test detecting UNION-based SQL injection."""
        validator = InputValidator()

        result = validator.validate_string(
            "1 UNION SELECT password FROM users",
            field_name="id",
        )

        assert not result.valid
        assert result.has_critical_violations()

    def test_command_injection_pipe(self) -> None:
        """Test detecting command injection with pipe."""
        validator = InputValidator()

        result = validator.validate_string(
            "file.txt | cat /etc/passwd",
            field_name="filename",
        )

        assert not result.valid
        assert any(v.rule == "command_injection" for v in result.violations)
        assert result.has_critical_violations()

    def test_command_injection_semicolon(self) -> None:
        """Test detecting command injection with semicolon."""
        validator = InputValidator()

        result = validator.validate_string(
            "file.txt; rm -rf /",
            field_name="filename",
        )

        assert not result.valid
        assert result.has_critical_violations()

    def test_command_injection_backticks(self) -> None:
        """Test detecting command injection with backticks."""
        validator = InputValidator()

        result = validator.validate_string(
            "file`whoami`.txt",
            field_name="filename",
        )

        assert not result.valid
        assert result.has_critical_violations()

    def test_path_traversal_dotdot(self) -> None:
        """Test detecting path traversal with ../ sequences."""
        validator = InputValidator()

        result = validator.validate_string(
            "../../../etc/passwd",
            field_name="file_path",
        )

        assert not result.valid
        assert any(v.rule == "path_traversal" for v in result.violations)
        assert result.has_critical_violations()

    def test_path_traversal_windows(self) -> None:
        """Test detecting Windows path traversal."""
        validator = InputValidator()

        result = validator.validate_string(
            "..\\..\\..\\windows\\system32",
            field_name="file_path",
        )

        assert not result.valid
        assert result.has_critical_violations()

    def test_zero_width_character(self) -> None:
        """Test detecting zero-width characters."""
        validator = InputValidator()

        # String with zero-width space
        result = validator.validate_string(
            "package\u200Bname",
            field_name="name",
        )

        assert not result.valid
        assert any(v.rule == "zero_width_char" for v in result.violations)
        assert result.has_high_violations()

    def test_rtl_override(self) -> None:
        """Test detecting right-to-left override attack."""
        validator = InputValidator()

        # String with RLO character
        result = validator.validate_string(
            "file\u202Etxt.exe",  # Displays as "fileexe.txt"
            field_name="filename",
        )

        assert not result.valid
        assert any(v.rule == "rtl_override" for v in result.violations)

    def test_control_characters(self) -> None:
        """Test detecting control characters."""
        validator = InputValidator()

        # String with null byte
        result = validator.validate_string(
            "package\x00name",
            field_name="name",
        )

        assert not result.valid
        assert any(v.rule == "control_char" for v in result.violations)

    def test_non_ascii_rejected_when_disabled(self) -> None:
        """Test rejecting non-ASCII when not allowed."""
        validator = InputValidator()

        result = validator.validate_string(
            "café",  # Contains é
            field_name="name",
            allow_unicode=False,
        )

        assert not result.valid
        assert any(v.rule == "non_ascii" for v in result.violations)

    def test_non_ascii_allowed_when_enabled(self) -> None:
        """Test allowing non-ASCII when enabled."""
        validator = InputValidator()

        result = validator.validate_string(
            "café",
            field_name="name",
            allow_unicode=True,
        )

        # Should pass (no SQL injection, just Unicode)
        assert result.valid

    def test_whitespace_rejected_when_disabled(self) -> None:
        """Test rejecting whitespace when not allowed."""
        validator = InputValidator()

        result = validator.validate_string(
            "package name",
            field_name="identifier",
            allow_whitespace=False,
        )

        assert not result.valid
        assert any(v.rule == "no_whitespace" for v in result.violations)

    def test_homoglyph_warning(self) -> None:
        """Test warning about homoglyph characters."""
        validator = InputValidator()

        # String with Cyrillic 'a' instead of Latin 'a'
        result = validator.validate_string(
            "pаckage",  # Cyrillic а
            field_name="name",
        )

        # Should not fail validation but should warn
        assert len(result.warnings) > 0
        assert "homoglyph" in result.warnings[0].lower()

    def test_sanitization(self) -> None:
        """Test that sanitized version is provided for invalid input."""
        validator = InputValidator()

        result = validator.validate_string(
            "file; cat /etc/passwd",
            field_name="input",
        )

        assert not result.valid
        assert result.sanitized is not None
        assert ";" not in result.sanitized  # Dangerous char removed
        assert "cat" in result.sanitized  # Safe text preserved


class TestValidatorIdentifier:
    """Tests for identifier validation."""

    def test_valid_identifier(self) -> None:
        """Test validating a valid identifier."""
        validator = InputValidator()

        result = validator.validate_identifier("express")

        assert result.valid

    def test_identifier_with_hyphen(self) -> None:
        """Test identifier with hyphen."""
        validator = InputValidator()

        result = validator.validate_identifier("my-package")

        assert result.valid

    def test_identifier_with_slash(self) -> None:
        """Test identifier with slash (scoped packages)."""
        validator = InputValidator()

        result = validator.validate_identifier("@scope/package")

        assert result.valid

    def test_identifier_too_long(self) -> None:
        """Test identifier exceeding max length."""
        validator = InputValidator()

        result = validator.validate_identifier("a" * 600)  # Max is 500

        assert not result.valid
        assert any(v.rule == "identifier_length" for v in result.violations)

    def test_identifier_empty(self) -> None:
        """Test empty identifier."""
        validator = InputValidator()

        result = validator.validate_identifier("")

        assert not result.valid

    def test_identifier_invalid_chars(self) -> None:
        """Test identifier with invalid characters."""
        validator = InputValidator()

        result = validator.validate_identifier("pack age")  # Space not allowed

        assert not result.valid
        assert any(v.rule == "identifier_chars" for v in result.violations)

    def test_identifier_starts_with_special(self) -> None:
        """Test identifier starting with special character."""
        validator = InputValidator()

        result = validator.validate_identifier("-package")

        assert not result.valid
        assert any(v.rule == "identifier_start" for v in result.violations)

    def test_identifier_path_traversal(self) -> None:
        """Test identifier with path traversal."""
        validator = InputValidator()

        result = validator.validate_identifier("../etc/passwd")

        assert not result.valid
        assert any(v.rule == "path_traversal" for v in result.violations)
        assert result.has_critical_violations()


class TestValidatorVersion:
    """Tests for version string validation."""

    def test_valid_semver(self) -> None:
        """Test validating semantic version."""
        validator = InputValidator()

        result = validator.validate_version("1.2.3")

        assert result.valid

    def test_valid_semver_prerelease(self) -> None:
        """Test validating prerelease version."""
        validator = InputValidator()

        result = validator.validate_version("2.0.0-alpha.1")

        assert result.valid

    def test_valid_semver_build(self) -> None:
        """Test validating version with build metadata."""
        validator = InputValidator()

        result = validator.validate_version("1.0.0+20240101")

        assert result.valid

    def test_valid_version_range(self) -> None:
        """Test validating version range."""
        validator = InputValidator()

        result = validator.validate_version("^1.2.3")
        assert result.valid

        result = validator.validate_version("~2.0.0")
        assert result.valid

        result = validator.validate_version(">=3.0.0")
        assert result.valid

    def test_version_too_long(self) -> None:
        """Test version exceeding max length."""
        validator = InputValidator()

        result = validator.validate_version("1." * 150)  # Way too long

        assert not result.valid
        assert any(v.rule == "version_length" for v in result.violations)

    def test_version_invalid_chars(self) -> None:
        """Test version with invalid characters."""
        validator = InputValidator()

        result = validator.validate_version("1.2.3; DROP TABLE")

        assert not result.valid
        assert any(v.rule == "version_chars" for v in result.violations)


class TestValidationResult:
    """Tests for ValidationResult helper methods."""

    def test_is_safe_when_valid(self) -> None:
        """Test is_safe() for valid input."""
        result = ValidationResult(valid=True, violations=[])
        assert result.is_safe()

    def test_is_safe_with_low_severity(self) -> None:
        """Test is_safe() with only low-severity violations."""
        from tessryx.kernel.validator import ValidationViolation

        result = ValidationResult(
            valid=False,
            violations=[
                ValidationViolation(
                    rule="test",
                    severity="low",
                    message="Low severity issue",
                )
            ],
        )

        assert result.is_safe()  # Low severity is considered safe

    def test_not_safe_with_high_severity(self) -> None:
        """Test is_safe() with high-severity violations."""
        from tessryx.kernel.validator import ValidationViolation

        result = ValidationResult(
            valid=False,
            violations=[
                ValidationViolation(
                    rule="test",
                    severity="high",
                    message="High severity issue",
                )
            ],
        )

        assert not result.is_safe()

    def test_has_critical_violations(self) -> None:
        """Test has_critical_violations()."""
        from tessryx.kernel.validator import ValidationViolation

        result = ValidationResult(
            valid=False,
            violations=[
                ValidationViolation(rule="test", severity="critical", message="Critical"),
            ],
        )

        assert result.has_critical_violations()

    def test_has_high_violations(self) -> None:
        """Test has_high_violations()."""
        from tessryx.kernel.validator import ValidationViolation

        result = ValidationResult(
            valid=False,
            violations=[
                ValidationViolation(rule="test", severity="high", message="High"),
            ],
        )

        assert result.has_high_violations()


class TestValidatorEdgeCases:
    """Edge case tests for validator."""

    def test_empty_string(self) -> None:
        """Test validating empty string."""
        validator = InputValidator()

        result = validator.validate_string("", field_name="test")

        # Empty string is valid unless min_length > 0
        assert result.valid

    def test_very_long_string(self) -> None:
        """Test validating very long string."""
        validator = InputValidator()

        result = validator.validate_string(
            "a" * 10000,
            field_name="test",
            max_length=5000,
        )

        assert not result.valid

    def test_mixed_attacks(self) -> None:
        """Test input with multiple attack types."""
        validator = InputValidator()

        result = validator.validate_string(
            "../../../etc/passwd; cat /etc/shadow | SELECT * FROM users",
            field_name="evil_input",
        )

        assert not result.valid
        assert result.has_critical_violations()

        # Should detect multiple attack types
        violation_rules = {v.rule for v in result.violations}
        assert len(violation_rules) >= 2  # Multiple different attacks detected

    def test_unicode_normalization_in_sanitize(self) -> None:
        """Test that sanitization normalizes Unicode."""
        validator = InputValidator()

        # String with combining characters
        result = validator.validate_string(
            "café\u0301",  # e + combining acute accent
            field_name="test",
        )

        # Should have sanitized version with normalized Unicode
        if result.sanitized:
            # Check that it's normalized (NFKC)
            import unicodedata

            assert result.sanitized == unicodedata.normalize("NFKC", result.sanitized)
