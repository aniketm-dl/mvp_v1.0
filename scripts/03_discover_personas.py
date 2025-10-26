#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.personas.discovery import PersonaDiscovery
from src.personas.profiler import PersonaProfiler

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="Discover personas from OPeRA behavioral data using UMAP + HDBSCAN + LLM summarization."
    )
    parser.add_argument(
        "--features",
        type=str,
        default="DATA/OPeRA/processed/persona_features.parquet",
        help="Path to persona features parquet",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="models/persona_profiles.json",
        help="Output path for persona profiles JSON",
    )
    parser.add_argument(
        "--min-cluster-size",
        type=int,
        default=50,
        help="Minimum cluster size for HDBSCAN",
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=10,
        help="Minimum samples for HDBSCAN core points",
    )
    parser.add_argument(
        "--use-llm-summary",
        action="store_true",
        help="Use GPT-4o-mini for persona descriptions (requires OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--save-clustering",
        type=str,
        default="DATA/OPeRA/interim/cluster_assignments.parquet",
        help="Save cluster assignments (user_id, cluster_id, umap coords)",
    )

    args = parser.parse_args()

    console.print("\n[bold cyan]🔍 Persona Discovery Pipeline[/bold cyan]")
    console.print(f"   Features: {args.features}")
    console.print(f"   Output: {args.out}\n")

    # Check for OpenAI API key if LLM summary requested
    if args.use_llm_summary:
        if not os.getenv("OPENAI_API_KEY"):
            console.print(
                "[bold yellow]⚠️  OPENAI_API_KEY not set. Using template-based descriptions.[/bold yellow]\n"
            )
            args.use_llm_summary = False
        else:
            console.print("[bold green]✅ OpenAI API key found. Will use GPT-4o-mini for persona descriptions.[/bold green]\n")

    # Initialize discovery
    discovery = PersonaDiscovery(
        min_cluster_size=args.min_cluster_size,
        min_samples=args.min_samples,
        umap_n_neighbors=15,
        umap_min_dist=0.1,
        random_state=42,
    )

    # Load features
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Loading persona features...", total=None)
        n_users = discovery.load_features(Path(args.features))
        progress.update(task, completed=True)

    if n_users == 0:
        console.print("[bold red]❌ Failed to load features. Exiting.[/bold red]")
        return

    console.print(f"  ✅ Loaded features for {n_users:,} users\n")

    # UMAP dimensionality reduction
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running UMAP dimensionality reduction...", total=None)
        success = discovery.fit_umap()
        progress.update(task, completed=True)

    if not success:
        console.print("[bold red]❌ UMAP failed. Exiting.[/bold red]")
        return

    console.print("  ✅ UMAP complete (12-D → 2-D)\n")

    # HDBSCAN clustering
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running HDBSCAN clustering...", total=None)
        n_clusters = discovery.fit_hdbscan()
        progress.update(task, completed=True)

    if n_clusters == 0:
        console.print("[bold red]❌ No clusters found. Try reducing --min-cluster-size.[/bold red]")
        return

    console.print(f"  ✅ Found {n_clusters} clusters\n")

    # Compute silhouette score
    silhouette = discovery.compute_silhouette_score()
    if silhouette >= 0.35:
        console.print(f"  ✅ Silhouette score: [bold green]{silhouette:.3f}[/bold green] (≥0.35 target)\n")
    else:
        console.print(f"  ⚠️  Silhouette score: [bold yellow]{silhouette:.3f}[/bold yellow] (<0.35 target)\n")

    # Extract cluster profiles
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Extracting cluster profiles...", total=None)
        cluster_profiles = discovery.extract_cluster_profiles()
        progress.update(task, completed=True)

    console.print(f"  ✅ Extracted {len(cluster_profiles)} cluster profiles\n")

    # Generate persona descriptions
    profiler = PersonaProfiler(use_llm=args.use_llm_summary)

    console.print("[bold cyan]🎨 Generating persona descriptions...[/bold cyan]\n")

    # Get sample users for each cluster
    sample_users_map = {}
    for profile in cluster_profiles:
        cluster_id = profile["cluster_id"]
        sample_users = discovery.get_cluster_sample_users(cluster_id, n=5)
        sample_users_map[cluster_id] = sample_users

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Generating descriptions {'with GPT-4o-mini' if args.use_llm_summary else 'with templates'}...",
            total=None
        )
        personas = profiler.generate_all_personas(cluster_profiles, sample_users_map)
        progress.update(task, completed=True)

    console.print(f"  ✅ Generated {len(personas)} persona profiles\n")

    # Display persona table
    table = Table(title="Discovered Personas", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan")
    table.add_column("Label", style="green")
    table.add_column("Size", justify="right", style="yellow")
    table.add_column("Description", style="white")

    for persona in personas:
        table.add_row(
            persona["id"],
            persona["label"],
            f"{persona['size']:,}",
            persona["description"][:60] + "..." if len(persona["description"]) > 60 else persona["description"]
        )

    console.print(table)
    console.print()

    # Save persona profiles
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump({"personas": personas}, f, indent=2)

    console.print(f"[bold green]✅ Saved persona profiles to: {output_path}[/bold green]\n")

    # Save clustering results
    if args.save_clustering:
        clustering_path = Path(args.save_clustering)
        discovery.save_clustering_results(clustering_path)
        console.print(f"[bold green]✅ Saved clustering assignments to: {clustering_path}[/bold green]\n")

    # Summary statistics
    console.print("[bold cyan]📊 Summary Statistics:[/bold cyan]")
    console.print(f"   • Total users: {n_users:,}")
    console.print(f"   • Personas discovered: {n_clusters}")
    console.print(f"   • Silhouette score: {silhouette:.3f}")
    console.print(f"   • Average cluster size: {n_users / n_clusters:.0f}")
    console.print(f"   • Smallest cluster: {min(p['size'] for p in personas):,} users")
    console.print(f"   • Largest cluster: {max(p['size'] for p in personas):,} users")

    # Quality assessment
    console.print("\n[bold cyan]✨ Quality Assessment:[/bold cyan]")
    if silhouette >= 0.35:
        console.print("   ✅ [bold green]Clustering quality: GOOD[/bold green]")
    elif silhouette >= 0.25:
        console.print("   ⚠️  [bold yellow]Clustering quality: ACCEPTABLE[/bold yellow]")
    else:
        console.print("   ❌ [bold red]Clustering quality: POOR (consider adjusting parameters)[/bold red]")

    if n_clusters >= 8 and n_clusters <= 15:
        console.print("   ✅ [bold green]Number of personas: OPTIMAL[/bold green]")
    elif n_clusters >= 5:
        console.print("   ⚠️  [bold yellow]Number of personas: ACCEPTABLE[/bold yellow]")
    else:
        console.print("   ❌ [bold red]Number of personas: TOO FEW (reduce --min-cluster-size)[/bold red]")

    console.print("\n[bold green]✅ Persona discovery complete![/bold green]\n")


if __name__ == "__main__":
    main()
