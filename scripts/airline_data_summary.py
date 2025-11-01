#!/usr/bin/env python3
"""
Generate a concise HTML summary report of the airline dataset.

This creates a nice visual summary that you can open in a browser.

Usage:
    python scripts/airline_data_summary.py

Output:
    DATA/airline/data_summary.html
"""

from __future__ import annotations

import pandas as pd
from pathlib import Path


def generate_html_summary(df: pd.DataFrame, output_path: Path) -> None:
    """Generate an HTML summary report."""

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Airline Dataset Summary</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .section {{
            background: white;
            padding: 30px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            margin-top: 0;
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .progress-bar {{
            background: #e0e0e0;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            margin: 5px 0;
        }}
        .progress-fill {{
            background: #667eea;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 40px;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Airline Dataset Summary</h1>
        <p>Comprehensive overview of {len(df):,} passenger records</p>
    </div>

    <div class="section">
        <h2>📈 Dataset Overview</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(df):,}</div>
                <div class="stat-label">Total Records</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(df.columns)}</div>
                <div class="stat-label">Columns</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{df.memory_usage(deep=True).sum() / 1024:.1f}KB</div>
                <div class="stat-label">Memory Usage</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{df.isnull().sum().sum()}</div>
                <div class="stat-label">Missing Values</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>👥 Demographics</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Distribution</th>
            </tr>
"""

    # Gender distribution
    gender_counts = df['gender'].value_counts()
    for gender, count in gender_counts.items():
        pct = (count / len(df)) * 100
        html += f"""
            <tr>
                <td><strong>Gender:</strong> {gender}</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {pct}%">{count:,} ({pct:.1f}%)</div>
                    </div>
                </td>
            </tr>
"""

    # Age stats
    html += f"""
            <tr>
                <td><strong>Age Range</strong></td>
                <td>{df['age'].min()} - {df['age'].max()} years (median: {df['age'].median():.0f})</td>
            </tr>
"""

    html += """
        </table>
    </div>

    <div class="section">
        <h2>✈️ Travel Profile</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Distribution</th>
            </tr>
"""

    # Customer type
    for customer_type, count in df['customer_type'].value_counts().items():
        pct = (count / len(df)) * 100
        html += f"""
            <tr>
                <td><strong>Customer Type:</strong> {customer_type}</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {pct}%">{count:,} ({pct:.1f}%)</div>
                    </div>
                </td>
            </tr>
"""

    # Travel type
    for travel_type, count in df['type_of_travel'].value_counts().items():
        pct = (count / len(df)) * 100
        html += f"""
            <tr>
                <td><strong>Travel Type:</strong> {travel_type}</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {pct}%">{count:,} ({pct:.1f}%)</div>
                    </div>
                </td>
            </tr>
"""

    # Flight class
    for flight_class, count in df['flight_class'].value_counts().items():
        pct = (count / len(df)) * 100
        html += f"""
            <tr>
                <td><strong>Flight Class:</strong> {flight_class}</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {pct}%">{count:,} ({pct:.1f}%)</div>
                    </div>
                </td>
            </tr>
"""

    html += """
        </table>
    </div>

    <div class="section">
        <h2>🎯 Satisfaction Analysis</h2>
        <table>
            <tr>
                <th>Satisfaction Level</th>
                <th>Distribution</th>
            </tr>
"""

    # Satisfaction breakdown
    satisfaction_map = {0: "😞 Neutral/Dissatisfied", 1: "😊 Satisfied"}
    for val, label in satisfaction_map.items():
        count = (df['y'] == val).sum()
        pct = (count / len(df)) * 100
        color = "#667eea" if val == 1 else "#999"
        html += f"""
            <tr>
                <td><strong>{label}</strong></td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {pct}%; background: {color}">{count:,} ({pct:.1f}%)</div>
                    </div>
                </td>
            </tr>
"""

    html += """
        </table>
    </div>

    <div class="section">
        <h2>⭐ Service Ratings (1-5 Scale)</h2>
        <table>
            <tr>
                <th>Service Item</th>
                <th>Average Rating</th>
                <th>Median</th>
            </tr>
"""

    # Service ratings
    service_items = [
        ('inflight_wifi_service', 'Inflight WiFi'),
        ('departure_arrival_time_convenient', 'Schedule Convenience'),
        ('ease_of_online_booking', 'Online Booking'),
        ('gate_location', 'Gate Location'),
        ('food_and_drink', 'Food & Drink'),
        ('online_boarding', 'Online Boarding'),
        ('seat_comfort', 'Seat Comfort'),
        ('inflight_entertainment', 'Entertainment'),
        ('on_board_service', 'Onboard Service'),
        ('leg_room_service', 'Leg Room'),
        ('baggage_handling', 'Baggage Handling'),
        ('checkin_service', 'Check-in Service'),
        ('inflight_service', 'Inflight Service'),
        ('cleanliness', 'Cleanliness'),
    ]

    for col, label in service_items:
        if col in df.columns:
            mean_val = df[col].mean()
            median_val = df[col].median()
            pct = (mean_val / 5) * 100
            html += f"""
            <tr>
                <td>{label}</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {pct}%">{mean_val:.2f} / 5.0</div>
                    </div>
                </td>
                <td>{median_val:.0f}</td>
            </tr>
"""

    html += """
        </table>
    </div>

    <div class="section">
        <h2>🔢 Flight Statistics</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Mean</th>
                <th>Median</th>
                <th>Min</th>
                <th>Max</th>
            </tr>
"""

    # Flight metrics
    flight_metrics = [
        ('flight_distance', 'Distance (miles)'),
        ('departure_delay_minutes', 'Departure Delay (min)'),
        ('arrival_delay_minutes', 'Arrival Delay (min)'),
    ]

    for col, label in flight_metrics:
        if col in df.columns:
            html += f"""
            <tr>
                <td><strong>{label}</strong></td>
                <td>{df[col].mean():,.1f}</td>
                <td>{df[col].median():,.0f}</td>
                <td>{df[col].min():,.0f}</td>
                <td>{df[col].max():,.0f}</td>
            </tr>
"""

    html += """
        </table>
    </div>

    <div class="section">
        <h2>🔗 Top Correlations with Satisfaction</h2>
        <table>
            <tr>
                <th>Feature</th>
                <th>Correlation</th>
            </tr>
"""

    # Correlations
    num_cols = df.select_dtypes(include=['int8', 'int16', 'int32', 'int64', 'float64']).columns
    num_cols = [c for c in num_cols if c not in ['row_id', 'y']]

    if num_cols and 'y' in df.columns:
        corrs = df[num_cols + ['y']].corr()['y'].drop('y').sort_values(ascending=False)

        for feature, corr in corrs.head(10).items():
            display_name = feature.replace('_', ' ').title()
            color = "#667eea" if corr > 0 else "#e74c3c"
            width = abs(corr) * 100
            html += f"""
            <tr>
                <td>{display_name}</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {width}%; background: {color}">{corr:+.3f}</div>
                    </div>
                </td>
            </tr>
"""

    html += """
        </table>
    </div>

    <div class="footer">
        <p>Generated by Darpan Labs MVP v1.0</p>
        <p>Dataset: Airline Passenger Satisfaction (Kaggle)</p>
    </div>
</body>
</html>
"""

    # Write HTML file
    with open(output_path, 'w') as f:
        f.write(html)

    print(f"✅ HTML summary generated: {output_path}")
    print(f"   Open in browser: open {output_path}")


def main():
    """Generate HTML summary report."""

    # Load data
    data_path = Path("DATA/airline/demo_airline.parquet")
    output_path = Path("DATA/airline/data_summary.html")

    print(f"Loading data from {data_path}...")
    df = pd.read_parquet(data_path)

    print(f"Generating HTML summary...")
    generate_html_summary(df, output_path)

    print("\n" + "="*80)
    print("SUMMARY COMPLETE")
    print("="*80)
    print(f"\nOpen the summary in your browser:")
    print(f"  open {output_path}")
    print()


if __name__ == "__main__":
    main()
