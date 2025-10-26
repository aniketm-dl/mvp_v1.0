from __future__ import annotations

import numpy as np
import pytest

from src.ssr.reference_statements import ReferenceStatementSets


class TestReferenceStatementSets:
    """Test suite for reference statement sets."""

    def test_all_sets_have_five_statements(self):
        """Each reference set should have exactly 5 statements (Likert 1-5)."""
        for set_name, statements in ReferenceStatementSets.ALL_SETS.items():
            assert len(statements) == 5, (
                f"{set_name} should have 5 statements, got {len(statements)}"
            )

    def test_statements_are_unique_within_sets(self):
        """No duplicate statements within a set."""
        for set_name, statements in ReferenceStatementSets.ALL_SETS.items():
            assert len(set(statements)) == 5, (
                f"{set_name} has duplicate statements"
            )

    def test_statements_are_non_empty(self):
        """All statements should be non-empty strings."""
        for set_name, statements in ReferenceStatementSets.ALL_SETS.items():
            for i, stmt in enumerate(statements):
                assert isinstance(stmt, str), (
                    f"{set_name}[{i}] is not a string"
                )
                assert stmt.strip(), (
                    f"{set_name}[{i}] is empty or whitespace"
                )

    def test_get_statement_set(self):
        """Test getting a statement set by name."""
        t1_set = ReferenceStatementSets.get_statement_set("T1_purchase_intent")
        assert len(t1_set) == 5
        assert "never buy" in t1_set[0].lower()
        assert "definitely buy" in t1_set[4].lower()

    def test_get_statement_set_invalid_name(self):
        """Invalid set name should raise KeyError."""
        with pytest.raises(KeyError):
            ReferenceStatementSets.get_statement_set("INVALID_SET")

    def test_get_statement_for_rating(self):
        """Test getting individual statements by Likert rating."""
        # Rating 1 (lowest)
        stmt_1 = ReferenceStatementSets.get_statement_for_rating(
            "T1_purchase_intent", 1
        )
        assert "never" in stmt_1.lower()

        # Rating 5 (highest)
        stmt_5 = ReferenceStatementSets.get_statement_for_rating(
            "T1_purchase_intent", 5
        )
        assert "definitely" in stmt_5.lower()

    def test_get_statement_for_rating_invalid(self):
        """Invalid Likert rating should raise ValueError."""
        with pytest.raises(ValueError):
            ReferenceStatementSets.get_statement_for_rating(
                "T1_purchase_intent", 0
            )

        with pytest.raises(ValueError):
            ReferenceStatementSets.get_statement_for_rating(
                "T1_purchase_intent", 6
            )

    def test_create_training_pairs(self):
        """Test creating contrastive training pairs."""
        llm_response = "I love this product!"
        likert_rating = 5

        response_text, reference_text = ReferenceStatementSets.create_training_pairs(
            llm_response, likert_rating
        )

        assert response_text == llm_response
        assert "definitely buy" in reference_text.lower()

    def test_create_training_pairs_with_different_sets(self):
        """Test training pairs with different reference sets."""
        llm_response = "This is terrible value."
        likert_rating = 1

        _, ref_purchase = ReferenceStatementSets.create_training_pairs(
            llm_response, likert_rating, "T1_purchase_intent"
        )

        _, ref_value = ReferenceStatementSets.create_training_pairs(
            llm_response, likert_rating, "T2_value_perception"
        )

        # Different sets should have different reference statements
        assert ref_purchase != ref_value
        assert "never" in ref_purchase.lower()
        assert "terrible value" in ref_value.lower()

    def test_get_similarity_targets_one_hot(self):
        """Test one-hot similarity targets."""
        targets = ReferenceStatementSets.get_similarity_targets(
            likert_rating=3,
            similarity_function="one_hot"
        )

        assert targets.shape == (5,)
        assert targets[2] == 1.0  # Index 2 = rating 3
        assert targets[0] == 0.0
        assert targets[4] == 0.0
        assert np.sum(targets) == 1.0

    def test_get_similarity_targets_ordinal_distance(self):
        """Test ordinal distance similarity targets."""
        targets = ReferenceStatementSets.get_similarity_targets(
            likert_rating=3,
            similarity_function="ordinal_distance"
        )

        assert targets.shape == (5,)
        assert targets[2] == 1.0  # Exact match
        assert targets[1] == 0.67  # Distance 1
        assert targets[3] == 0.67  # Distance 1
        assert targets[0] == 0.33  # Distance 2
        assert targets[4] == 0.33  # Distance 2

    def test_get_similarity_targets_boundary_cases(self):
        """Test similarity targets for boundary ratings (1 and 5)."""
        # Rating 1 (lowest)
        targets_1 = ReferenceStatementSets.get_similarity_targets(
            likert_rating=1,
            similarity_function="ordinal_distance"
        )
        assert targets_1[0] == 1.0  # Exact match
        assert targets_1[1] == 0.67  # Distance 1
        assert targets_1[2] == 0.33  # Distance 2
        assert targets_1[3] == 0.0   # Distance 3
        assert targets_1[4] == 0.0   # Distance 4

        # Rating 5 (highest)
        targets_5 = ReferenceStatementSets.get_similarity_targets(
            likert_rating=5,
            similarity_function="ordinal_distance"
        )
        assert targets_5[4] == 1.0  # Exact match
        assert targets_5[3] == 0.67  # Distance 1
        assert targets_5[2] == 0.33  # Distance 2
        assert targets_5[1] == 0.0   # Distance 3
        assert targets_5[0] == 0.0   # Distance 4

    def test_get_all_sets(self):
        """Test getting all reference sets."""
        all_sets = ReferenceStatementSets.get_all_sets()

        assert isinstance(all_sets, dict)
        assert len(all_sets) == 6  # T1-T6
        assert "T1_purchase_intent" in all_sets
        assert "T6_urgency" in all_sets

        # Should be a copy, not reference
        all_sets["NEW_SET"] = ["test"]
        assert "NEW_SET" not in ReferenceStatementSets.ALL_SETS

    def test_validate_sets(self):
        """Test that validation passes for all predefined sets."""
        result = ReferenceStatementSets.validate_sets()
        assert result is True

    def test_statement_ordinal_progression(self):
        """Test that statements follow ordinal progression (low to high)."""
        # T1: Purchase intent should progress from negative to positive
        t1 = ReferenceStatementSets.T1_PURCHASE_INTENT
        assert "never" in t1[0].lower()
        assert "probably" in t1[1].lower() and "not" in t1[1].lower()
        assert "might" in t1[2].lower()
        assert "likely" in t1[3].lower()
        assert "definitely" in t1[4].lower()

        # T2: Value perception should progress from terrible to excellent
        t2 = ReferenceStatementSets.T2_VALUE_PERCEPTION
        assert "terrible" in t2[0].lower()
        assert "poor" in t2[1].lower()
        assert "acceptable" in t2[2].lower()
        assert "good" in t2[3].lower()
        assert "excellent" in t2[4].lower()

    def test_all_sets_present(self):
        """Ensure all 6 reference sets are defined."""
        expected_sets = [
            "T1_purchase_intent",
            "T2_value_perception",
            "T3_product_appeal",
            "T4_satisfaction",
            "T5_recommendation",
            "T6_urgency",
        ]

        for set_name in expected_sets:
            assert set_name in ReferenceStatementSets.ALL_SETS, (
                f"Missing reference set: {set_name}"
            )

    def test_use_case_semantic_similarity_training(self):
        """
        Integration test: Simulate creating training data for SSR.

        This mimics the workflow in src/ssr/trainer.py where we create
        contrastive pairs for sentence-transformers training.
        """
        # Mock LLM responses with ground-truth Likert ratings
        mock_data = [
            ("I absolutely love this deal!", 5),
            ("This is terrible value for money.", 1),
            ("It's okay, nothing special.", 3),
            ("Pretty good offer, I'd consider it.", 4),
            ("Not interested at all.", 1),
        ]

        training_pairs = []
        for llm_response, likert_rating in mock_data:
            response_text, ref_text = ReferenceStatementSets.create_training_pairs(
                llm_response, likert_rating, "T1_purchase_intent"
            )

            # Get similarity targets for multi-reference training
            targets = ReferenceStatementSets.get_similarity_targets(
                likert_rating, similarity_function="ordinal_distance"
            )

            training_pairs.append({
                "llm_response": response_text,
                "reference_statement": ref_text,
                "likert_rating": likert_rating,
                "similarity_targets": targets,
            })

        # Verify we have training data
        assert len(training_pairs) == 5

        # Verify high ratings map to positive statements
        high_rating_pair = training_pairs[0]  # Rating 5
        assert "definitely" in high_rating_pair["reference_statement"].lower()
        assert high_rating_pair["similarity_targets"][4] == 1.0

        # Verify low ratings map to negative statements
        low_rating_pair = training_pairs[1]  # Rating 1
        assert "never" in low_rating_pair["reference_statement"].lower()
        assert low_rating_pair["similarity_targets"][0] == 1.0
