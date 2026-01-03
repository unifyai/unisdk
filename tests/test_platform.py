import math

import pytest
import unify
from unify.utils import http


class TestDeductCredits:
    """Tests for the deduct_credits function."""

    def test_deduct_credits_success(self):
        """Test successful credit deduction."""
        # Deduct a small amount
        deduct_amount = 0.001
        result = unify.deduct_credits(deduct_amount)

        # Verify response structure
        assert "previous_credits" in result
        assert "deducted" in result
        assert "current_credits" in result

        # Verify the deduction math is correct
        assert result["deducted"] == deduct_amount
        assert math.isclose(
            result["current_credits"],
            result["previous_credits"] - deduct_amount,
        )

    def test_deduct_credits_fractional_amount(self):
        """Test deducting fractional credit amounts."""
        result = unify.deduct_credits(0.00123)

        assert result["deducted"] == 0.00123
        assert "previous_credits" in result
        assert "current_credits" in result

    def test_deduct_credits_zero_amount(self):
        """Test deduction fails with zero amount."""
        with pytest.raises(http.RequestError) as exc_info:
            unify.deduct_credits(0)

        assert exc_info.value.response.status_code == 422

    def test_deduct_credits_negative_amount(self):
        """Test deduction fails with negative amount (cannot add credits)."""
        with pytest.raises(http.RequestError) as exc_info:
            unify.deduct_credits(-5.0)

        assert exc_info.value.response.status_code == 422

    def test_deduct_credits_insufficient_funds(self):
        """Test deduction fails when user has insufficient credits."""
        # Try to deduct an absurdly large amount
        with pytest.raises(http.RequestError) as exc_info:
            unify.deduct_credits(999_999_999_999.0)

        assert exc_info.value.response.status_code == 400
        assert "Insufficient credits" in str(exc_info.value)
