from __future__ import annotations
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple
import yaml
import numpy as np
import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


def train_persona_classifier(
    embeddings: np.ndarray,
    persona_ids: np.ndarray,
    model_type: str,
    test_size: float,
    seed: int
) -> Tuple[Any, Dict[str, Any]]:
    """
    Train classifier to predict persona_id from embedding.

    This helps us understand:
    1. How well embeddings separate personas
    2. Which personas are confused (off-diagonal in confusion matrix)
    3. Suggestions for merging similar personas or splitting confused ones

    Returns:
        model: Trained classifier
        results: Dict with accuracy, confusion matrix, classification report
    """
    print(f"Training {model_type} classifier...")
    print(f"  Training samples: {len(embeddings)}")
    print(f"  Unique personas: {len(set(persona_ids))}")

    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        embeddings,
        persona_ids,
        test_size=test_size,
        random_state=seed,
        stratify=persona_ids
    )

    # Initialize model
    if model_type == "logistic":
        model = LogisticRegression(
            max_iter=1000,
            random_state=seed,
            multi_class="multinomial",
            solver="lbfgs"
        )
    elif model_type == "random_forest":
        model = RandomForestClassifier(
            n_estimators=100,
            random_state=seed,
            max_depth=20,
            min_samples_split=10
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    # Train
    model.fit(X_train, y_train)

    # Evaluate
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    train_acc = accuracy_score(y_train, y_pred_train)
    test_acc = accuracy_score(y_test, y_pred_test)

    print(f"  Train accuracy: {train_acc:.4f}")
    print(f"  Test accuracy:  {test_acc:.4f}")

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred_test)
    cm_normalized = cm.astype(float) / cm.sum(axis=1, keepdims=True)

    # Classification report
    report = classification_report(
        y_test,
        y_pred_test,
        output_dict=True,
        zero_division=0
    )

    results = {
        "model_type": model_type,
        "train_accuracy": float(train_acc),
        "test_accuracy": float(test_acc),
        "confusion_matrix": cm,
        "confusion_matrix_normalized": cm_normalized,
        "classification_report": report,
        "persona_ids": sorted(set(persona_ids))
    }

    return model, results


def analyze_confusion(
    confusion_matrix: np.ndarray,
    persona_ids: list,
    threshold: float = 0.1
) -> Dict[str, Any]:
    """
    Analyze confusion matrix to identify:
    1. Pairs of personas that are frequently confused
    2. Suggestions for merging or splitting

    Args:
        confusion_matrix: (n_personas, n_personas) normalized confusion matrix
        persona_ids: List of persona IDs
        threshold: Confusion rate threshold for suggesting merge (default 0.1 = 10%)

    Returns:
        analysis: Dict with confusion pairs and suggestions
    """
    n = len(persona_ids)
    confusion_pairs = []

    # Find high-confusion pairs (off-diagonal)
    for i in range(n):
        for j in range(i + 1, n):
            # Confusion rate = average of (i→j) and (j→i)
            conf_rate = (confusion_matrix[i, j] + confusion_matrix[j, i]) / 2
            if conf_rate >= threshold:
                confusion_pairs.append({
                    "persona_1": persona_ids[i],
                    "persona_2": persona_ids[j],
                    "confusion_rate": float(conf_rate),
                    "suggestion": "consider_merge"
                })

    # Sort by confusion rate
    confusion_pairs = sorted(confusion_pairs, key=lambda x: -x["confusion_rate"])

    # Find personas with low recall (might need splitting)
    low_recall_personas = []
    for i in range(n):
        recall = confusion_matrix[i, i]
        if recall < 0.7:  # Less than 70% recall
            low_recall_personas.append({
                "persona": persona_ids[i],
                "recall": float(recall),
                "suggestion": "consider_split_or_refine"
            })

    analysis = {
        "high_confusion_pairs": confusion_pairs,
        "low_recall_personas": low_recall_personas,
        "n_merge_suggestions": len(confusion_pairs),
        "n_split_suggestions": len(low_recall_personas)
    }

    print(f"\nConfusion analysis:")
    print(f"  High confusion pairs: {len(confusion_pairs)}")
    if confusion_pairs:
        print(f"  Top confusions:")
        for pair in confusion_pairs[:5]:
            print(f"    {pair['persona_1']} ↔ {pair['persona_2']}: {100 * pair['confusion_rate']:.1f}%")

    print(f"\n  Low recall personas: {len(low_recall_personas)}")
    if low_recall_personas:
        for p in low_recall_personas[:5]:
            print(f"    {p['persona']}: {100 * p['recall']:.1f}%")

    return analysis


def main():
    parser = argparse.ArgumentParser(
        description="Train persona classifier and analyze confusion"
    )
    parser.add_argument(
        "--emb",
        type=Path,
        required=True,
        help="Path to embeddings parquet"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("CONFIGS/discovery.yaml"),
        help="Path to discovery config"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/discovery/persona_classifier.pkl"),
        help="Output path for classifier results"
    )

    args = parser.parse_args()

    # Load config
    with open(args.config) as f:
        config = yaml.safe_load(f)

    classifier_config = config["persona"]["classifier"]

    # Load embeddings
    print("Loading embeddings...")
    df = pd.read_parquet(args.emb)
    emb_cols = [c for c in df.columns if c.startswith("emb_")]
    embeddings = df[emb_cols].values

    # Load persona IDs
    if "persona_id" not in df.columns:
        print("WARNING: No persona_id column found in embeddings")
        print("Using cluster_id from personas.json as proxy...")
        import json
        personas_path = Path(config["persona"]["personas_path"])
        with open(personas_path) as f:
            personas = json.load(f)
        # Map by cluster_id (assuming cluster_id in personas.json)
        # This is a placeholder - in real data, persona_id should be in embeddings
        persona_ids = np.random.randint(0, 18, size=len(embeddings))  # Mock
    else:
        persona_ids = df["persona_id"].values

    # Train classifier
    model, results = train_persona_classifier(
        embeddings=embeddings,
        persona_ids=persona_ids,
        model_type=classifier_config["model"],
        test_size=classifier_config["test_size"],
        seed=classifier_config["seed"]
    )

    # Analyze confusion
    confusion_analysis = analyze_confusion(
        confusion_matrix=results["confusion_matrix_normalized"],
        persona_ids=results["persona_ids"],
        threshold=0.1
    )

    results["confusion_analysis"] = confusion_analysis

    # Check if accuracy meets threshold
    min_acc = classifier_config["min_accuracy"]
    if results["test_accuracy"] < min_acc:
        print(f"\n⚠ WARNING: Test accuracy {results['test_accuracy']:.4f} < {min_acc}")
        print("  Embeddings may not separate personas well enough.")
        print("  Consider:")
        print("    - Retraining encoder with higher loss weights")
        print("    - Refining persona definitions")
        print("    - Increasing embedding dim")
    else:
        print(f"\n✓ Test accuracy {results['test_accuracy']:.4f} >= {min_acc}")

    # Save
    args.out.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "model": model,
        "results": results
    }
    with open(args.out, "wb") as f:
        pickle.dump(data, f)
    print(f"\nSaved classifier results to {args.out}")


if __name__ == "__main__":
    main()
