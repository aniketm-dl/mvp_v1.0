from __future__ import annotations

import hashlib
from typing import Dict, List, Tuple

import numpy as np


class ReferenceStatementSets:
    """
    Reference statement sets for SSR (Semantic Similarity Rating).

    Implements the methodology from "LLMs Reproduce Human Purchase Intent via
    Semantic Similarity Elicitation of Likert Ratings" (Appendix C.1).

    Each set contains 5 anchor statements representing Likert ratings 1-5
    for different aspects of purchase intent in e-commerce.
    """
    VERSION = "2025-10-SSR-T6"

    # T1: Purchase Intent (Direct)
    T1_PURCHASE_INTENT = [
        "I would never buy this product.",  # Likert 1
        "I probably would not buy this product.",  # Likert 2
        "I might buy this product.",  # Likert 3
        "I would likely buy this product.",  # Likert 4
        "I would definitely buy this product.",  # Likert 5
    ]

    # T2: Value Perception
    T2_VALUE_PERCEPTION = [
        "This offers terrible value for the price.",  # Likert 1
        "This offers poor value for the price.",  # Likert 2
        "This offers acceptable value for the price.",  # Likert 3
        "This offers good value for the price.",  # Likert 4
        "This offers excellent value for the price.",  # Likert 5
    ]

    # T3: Product Appeal
    T3_PRODUCT_APPEAL = [
        "This product is completely unappealing to me.",  # Likert 1
        "This product is somewhat unappealing to me.",  # Likert 2
        "This product is neutral to me.",  # Likert 3
        "This product is somewhat appealing to me.",  # Likert 4
        "This product is very appealing to me.",  # Likert 5
    ]

    # T4: Satisfaction Expectation
    T4_SATISFACTION = [
        "I expect this would be very unsatisfying.",  # Likert 1
        "I expect this would be somewhat unsatisfying.",  # Likert 2
        "I expect this would be neither satisfying nor unsatisfying.",  # Likert 3
        "I expect this would be somewhat satisfying.",  # Likert 4
        "I expect this would be very satisfying.",  # Likert 5
    ]

    # T5: Recommendation Likelihood
    T5_RECOMMENDATION = [
        "I would never recommend this to others.",  # Likert 1
        "I would probably not recommend this to others.",  # Likert 2
        "I might recommend this to others.",  # Likert 3
        "I would likely recommend this to others.",  # Likert 4
        "I would definitely recommend this to others.",  # Likert 5
    ]

    # T6: Urgency/Priority
    T6_URGENCY = [
        "This has no priority for me at all.",  # Likert 1
        "This has low priority for me.",  # Likert 2
        "This has medium priority for me.",  # Likert 3
        "This has high priority for me.",  # Likert 4
        "This is a top priority for me.",  # Likert 5
    ]

    ALL_SETS = {
        "T1_purchase_intent": T1_PURCHASE_INTENT,
        "T2_value_perception": T2_VALUE_PERCEPTION,
        "T3_product_appeal": T3_PRODUCT_APPEAL,
        "T4_satisfaction": T4_SATISFACTION,
        "T5_recommendation": T5_RECOMMENDATION,
        "T6_urgency": T6_URGENCY,
    }

    @classmethod
    def get_set_names(cls) -> List[str]:
        """Return the list of registered reference set names."""
        return list(cls.ALL_SETS.keys())

    @classmethod
    def get_statement_set(cls, set_name: str) -> List[str]:
        """
        Get a reference statement set by name.

        Args:
            set_name: Name of the set (e.g., "T1_purchase_intent")

        Returns:
            List of 5 anchor statements (Likert 1-5)

        Raises:
            KeyError: If set_name is invalid
        """
        if set_name not in cls.ALL_SETS:
            available = ", ".join(cls.ALL_SETS.keys())
            raise KeyError(
                f"Invalid set name: {set_name}. Available sets: {available}"
            )

        return cls.ALL_SETS[set_name]

    @classmethod
    def get_statement_for_rating(
        cls, set_name: str, likert_rating: int
    ) -> str:
        """
        Get the anchor statement for a specific Likert rating.

        Args:
            set_name: Name of the reference set
            likert_rating: Likert score (1-5)

        Returns:
            Anchor statement text

        Raises:
            ValueError: If likert_rating not in [1, 5]
        """
        if not 1 <= likert_rating <= 5:
            raise ValueError(f"Likert rating must be 1-5, got {likert_rating}")

        statement_set = cls.get_statement_set(set_name)
        return statement_set[likert_rating - 1]  # Convert 1-indexed to 0-indexed

    @classmethod
    def get_all_sets(cls) -> Dict[str, List[str]]:
        """
        Get all reference statement sets.

        Returns:
            Dict mapping set names to statement lists
        """
        return cls.ALL_SETS.copy()

    @classmethod
    def get_version(cls) -> str:
        """Return the canonical version identifier for the anchor sets."""
        return cls.VERSION

    @classmethod
    def compute_hash(cls) -> str:
        """Compute SHA256 hash covering all anchor statements for provenance logging."""
        sha = hashlib.sha256()
        for set_name in sorted(cls.ALL_SETS.keys()):
            sha.update(set_name.encode("utf-8"))
            for statement in cls.ALL_SETS[set_name]:
                sha.update(statement.encode("utf-8"))
        return sha.hexdigest()

    @classmethod
    def create_training_pairs(
        cls,
        llm_response: str,
        likert_rating: int,
        set_name: str = "T1_purchase_intent",
    ) -> Tuple[str, str]:
        """
        Create a contrastive training pair from LLM response and Likert rating.

        For SSR training, we pair the LLM's free-text response with the
        reference statement that matches the given Likert rating.

        Args:
            llm_response: Free-text response from LLM (e.g., "This looks great!")
            likert_rating: Ground-truth Likert score (1-5)
            set_name: Which reference set to use

        Returns:
            Tuple of (llm_response, reference_statement)

        Example:
            >>> pairs = ReferenceStatementSets.create_training_pairs(
            ...     "I love this product!",
            ...     5,
            ...     "T1_purchase_intent"
            ... )
            >>> pairs
            ("I love this product!", "I would definitely buy this product.")
        """
        reference_statement = cls.get_statement_for_rating(set_name, likert_rating)
        return (llm_response, reference_statement)

    @classmethod
    def get_similarity_targets(
        cls,
        likert_rating: int,
        set_name: str = "T1_purchase_intent",
        similarity_function: str = "ordinal_distance",
    ) -> np.ndarray:
        """
        Get target similarities for all 5 reference statements.

        For contrastive learning, we want the LLM response to be most similar
        to the reference statement matching the Likert rating, and less similar
        to others based on ordinal distance.

        Args:
            likert_rating: Ground-truth Likert score (1-5)
            set_name: Which reference set to use
            similarity_function: How to compute targets ("ordinal_distance" or "one_hot")

        Returns:
            Array of shape (5,) with target similarities [0, 1]

        Example:
            >>> targets = ReferenceStatementSets.get_similarity_targets(4)
            >>> targets
            array([0.00, 0.33, 0.67, 1.00, 0.67])  # Highest at index 3 (rating 4)
        """
        if not 1 <= likert_rating <= 5:
            raise ValueError(f"Likert rating must be 1-5, got {likert_rating}")

        if similarity_function == "one_hot":
            # Hard targets: 1.0 for exact match, 0.0 otherwise
            targets = np.zeros(5)
            targets[likert_rating - 1] = 1.0

        elif similarity_function == "ordinal_distance":
            # Soft targets: Decay with ordinal distance
            # Distance 0 → 1.0, Distance 1 → 0.67, Distance 2 → 0.33, Distance 3+ → 0.0
            targets = np.zeros(5)
            for rating in range(1, 6):
                distance = abs(rating - likert_rating)
                if distance == 0:
                    targets[rating - 1] = 1.0
                elif distance == 1:
                    targets[rating - 1] = 0.67
                elif distance == 2:
                    targets[rating - 1] = 0.33
                else:
                    targets[rating - 1] = 0.0

        else:
            raise ValueError(
                f"Unknown similarity_function: {similarity_function}. "
                f"Use 'one_hot' or 'ordinal_distance'"
            )

        return targets

    @classmethod
    def validate_sets(cls) -> bool:
        """
        Validate that all reference sets are well-formed.

        Returns:
            True if all sets valid

        Raises:
            AssertionError: If any set is malformed
        """
        for set_name, statements in cls.ALL_SETS.items():
            # Check length
            assert len(statements) == 5, (
                f"{set_name} must have exactly 5 statements, "
                f"got {len(statements)}"
            )

            # Check uniqueness
            assert len(set(statements)) == 5, (
                f"{set_name} has duplicate statements"
            )

            # Check non-empty
            for i, stmt in enumerate(statements):
                assert stmt and stmt.strip(), (
                    f"{set_name}[{i}] is empty or whitespace"
                )

        return True


# Validate on import
ReferenceStatementSets.validate_sets()
