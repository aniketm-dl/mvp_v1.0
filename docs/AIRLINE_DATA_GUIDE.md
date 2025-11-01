# Airline Dataset Deep Dive Guide

This guide will help you explore and understand the raw airline dataset used in this MVP.

## Overview

The dataset contains **400 airline passenger records** from the Kaggle Airline Passenger Satisfaction Dataset. It includes:

- **Demographics**: Gender, age
- **Travel profile**: Customer type, travel type, flight class
- **Flight details**: Distance, delays
- **Service ratings**: 14 service items rated 1-5
- **Satisfaction label**: Satisfied vs. Neutral/Dissatisfied

## Dataset Files

### 1. Raw Dataset
**Location**: [DATA/airline/demo_airline.parquet](../DATA/airline/demo_airline.parquet)

**Format**: Parquet (compressed binary format)

**Size**: 400 rows × 25 columns

**CSV Version**: [DATA/airline/csv/demo_airline.csv](../DATA/airline/csv/demo_airline.csv)

### 2. Processed Datasets
After running the data processing pipeline:

- **clean_with_bands.parquet**: Raw data + age/distance/delay buckets (28 columns)
- **clean_with_tags.parquet**: Bands + psychographic tags (36 columns)

## Dataset Schema

### Demographics (2 columns)
| Column | Type | Values | Description |
|--------|------|--------|-------------|
| `gender` | object | Male, Female | Passenger gender |
| `age` | int64 | 18-79 | Passenger age in years |

### Travel Profile (3 columns)
| Column | Type | Values | Description |
|--------|------|--------|-------------|
| `customer_type` | object | Loyal Customer, Disloyal Customer | Loyalty status |
| `type_of_travel` | object | Business travel, Personal Travel | Trip purpose |
| `flight_class` | object | Eco, Business, Eco Plus | Cabin class |

### Flight Details (3 columns)
| Column | Type | Range | Description |
|--------|------|-------|-------------|
| `flight_distance` | int64 | 101-4,989 miles | Flight distance |
| `departure_delay_minutes` | int64 | 0-111 min | Departure delay |
| `arrival_delay_minutes` | int64 | 0-96 min | Arrival delay |

### Service Ratings (14 columns)
All rated 1-5 (Likert scale):

1. `inflight_wifi_service` - Inflight WiFi quality
2. `departure_arrival_time_convenient` - Schedule convenience
3. `ease_of_online_booking` - Booking system usability
4. `gate_location` - Gate convenience
5. `food_and_drink` - Food & beverage quality
6. `online_boarding` - Online boarding experience
7. `seat_comfort` - Seat comfort level
8. `inflight_entertainment` - Entertainment quality
9. `on_board_service` - Service quality
10. `leg_room_service` - Leg room adequacy
11. `baggage_handling` - Baggage service
12. `checkin_service` - Check-in experience
13. `inflight_service` - Overall inflight service
14. `cleanliness` - Aircraft cleanliness

### Target Variable (1 column)
| Column | Type | Values | Description |
|--------|------|--------|-------------|
| `y` | int64 | 0 (dissatisfied), 1 (satisfied) | Binary satisfaction |

### Identifiers (2 columns)
| Column | Type | Description |
|--------|------|-------------|
| `row_id` | int64 | Unique row identifier (0-399) |
| `split_id` | category | Train/test/validation split |

## Dataset Statistics

### Distribution Summary

**Gender**: 50.2% Male, 49.8% Female (balanced)

**Customer Type**: 71% Loyal, 29% Disloyal

**Travel Type**: 60.5% Business, 39.5% Personal

**Flight Class**: 47.2% Eco, 30.5% Business, 22.2% Eco Plus

**Satisfaction**: 35.2% Satisfied, 64.8% Dissatisfied

### Numerical Features

| Feature | Mean | Median | Min | Max |
|---------|------|--------|-----|-----|
| Age | 49.5 years | 50 | 18 | 79 |
| Flight Distance | 2,432 miles | 2,363 | 101 | 4,989 |
| Departure Delay | 14.9 min | 10 | 0 | 111 |
| Arrival Delay | 14.3 min | 10 | 0 | 96 |

### Service Ratings Average

All 14 service items average around **3.2-3.4** out of 5 (neutral to slightly positive).

Top correlated with satisfaction:
1. Departure/Arrival Time Convenient (r=0.472)
2. Inflight Entertainment (r=0.471)
3. Online Boarding (r=0.465)
4. Seat Comfort (r=0.464)

## How to Explore the Dataset

### Option 1: Open CSV in Excel/Numbers

The CSV files are ready to open in any spreadsheet application:

```bash
# Location
open DATA/airline/csv/demo_airline.csv
```

1. Open file in Excel or Numbers
2. Use filters to explore subgroups
3. Create pivot tables for analysis
4. Sort by satisfaction to compare satisfied vs. dissatisfied passengers

### Option 2: Python/Pandas Analysis

```python
import pandas as pd

# Load data
df = pd.read_csv('DATA/airline/csv/demo_airline.csv')

# Basic info
print(df.info())
print(df.describe())

# Satisfaction breakdown by class
print(df.groupby('flight_class')['y'].value_counts())

# Average ratings by satisfaction
satisfied = df[df['y'] == 1]
dissatisfied = df[df['y'] == 0]

service_cols = [
    'inflight_wifi_service',
    'seat_comfort',
    'inflight_entertainment',
    # ... add more
]

print("\nSatisfied passengers:")
print(satisfied[service_cols].mean())

print("\nDissatisfied passengers:")
print(dissatisfied[service_cols].mean())
```

### Option 3: Use Exploration Script

We've created a comprehensive exploration script:

```bash
# Activate virtual environment
source venv/bin/activate

# Explore demo dataset
python scripts/explore_airline_data.py --file demo_airline.parquet

# Explore all processed versions
python scripts/explore_airline_data.py --all
```

This generates a detailed report including:
- Dataset overview (shape, memory, columns)
- Missing value analysis
- Categorical distributions
- Numerical statistics
- Service rating averages
- Satisfaction breakdown
- Correlation analysis
- Psychographic tags (if available)
- Bucketed features (if available)

### Option 4: Jupyter Notebook Analysis

Create a notebook for interactive exploration:

```python
# notebook: explore_airline.ipynb

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
df = pd.read_parquet('DATA/airline/demo_airline.parquet')

# Visualize satisfaction by class
df.groupby(['flight_class', 'y']).size().unstack().plot(kind='bar')
plt.title('Satisfaction by Flight Class')
plt.ylabel('Count')
plt.show()

# Heatmap of service ratings
service_cols = [col for col in df.columns if col in [
    'inflight_wifi_service', 'seat_comfort', 'inflight_entertainment',
    'food_and_drink', 'online_boarding', 'cleanliness'
]]

plt.figure(figsize=(10, 6))
sns.heatmap(df[service_cols].corr(), annot=True, cmap='coolwarm')
plt.title('Service Ratings Correlation')
plt.show()

# Distribution of delays
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
df['departure_delay_minutes'].hist(bins=30, ax=axes[0])
axes[0].set_title('Departure Delay Distribution')
df['arrival_delay_minutes'].hist(bins=30, ax=axes[1])
axes[1].set_title('Arrival Delay Distribution')
plt.show()
```

## Key Insights from the Data

### 1. Service Quality Drives Satisfaction
The strongest predictors of satisfaction are service-related ratings:
- Time convenience (r=0.472)
- Entertainment (r=0.471)
- Online boarding (r=0.465)
- Seat comfort (r=0.464)

Delays have minimal correlation (r=-0.02 to -0.04).

### 2. Business Class Advantage
Business class passengers tend to be more satisfied due to:
- Better seat comfort
- More leg room
- Superior service quality

### 3. Balanced Demographics
The dataset has good representation across:
- Gender (50/50 split)
- Age groups (18-79, median 50)
- Travel types (60% business, 40% personal)

### 4. Satisfaction Gap
Only 35% satisfied vs. 65% dissatisfied suggests room for improvement in:
- Service delivery
- Amenities
- Customer experience

## Data Processing Pipeline

The raw data goes through these transformations:

```
demo_airline.parquet (400 rows, 25 cols)
    ↓
[airline_processing.py: add_bands()]
    ↓
clean_with_bands.parquet (400 rows, 28 cols)
    ├── delay_dep_bucket (short, medium, long)
    ├── delay_arr_bucket (short, medium, long)
    └── distance_bucket (short, medium, long)
    ↓
[airline_processing.py: add_psychographic_tags()]
    ↓
clean_with_tags.parquet (400 rows, 36 cols)
    ├── punctuality_sensitive_tag (bool)
    ├── comfort_seeker_tag (bool)
    ├── value_conscious_tag (bool)
    ├── digital_first_tag (bool)
    ├── service_reliability_tag (bool)
    ├── business_oriented_tag (bool)
    └── flight_distance_sensitive_tag (bool)
```

View processing code: [src/data/airline/airline_processing.py](../src/data/airline/airline_processing.py)

## Sample Records

Here are a few example records to understand the data:

### Example 1: Satisfied Business Traveler
```
row_id: 42
gender: Male
age: 38
customer_type: Loyal Customer
type_of_travel: Business travel
flight_class: Business
flight_distance: 3201 miles
departure_delay_minutes: 5
arrival_delay_minutes: 3
seat_comfort: 5
inflight_entertainment: 5
online_boarding: 4
y: 1 (satisfied)
```

### Example 2: Dissatisfied Economy Passenger
```
row_id: 127
gender: Female
age: 52
customer_type: Disloyal Customer
type_of_travel: Personal Travel
flight_class: Eco
flight_distance: 845 miles
departure_delay_minutes: 35
arrival_delay_minutes: 42
seat_comfort: 2
inflight_entertainment: 1
online_boarding: 2
y: 0 (dissatisfied)
```

## Common Analysis Tasks

### Task 1: Find passengers with highest satisfaction potential
```python
# High service ratings but dissatisfied
high_service = df[
    (df['seat_comfort'] >= 4) &
    (df['inflight_entertainment'] >= 4) &
    (df['y'] == 0)  # but still dissatisfied
]

print(f"Found {len(high_service)} passengers with high service ratings but dissatisfied")
print(high_service[['age', 'flight_class', 'departure_delay_minutes']].head())
```

### Task 2: Segment by loyalty and travel type
```python
segments = df.groupby(['customer_type', 'type_of_travel', 'flight_class'])['y'].agg([
    'count',
    'mean',
    'sum'
])
segments.columns = ['n_passengers', 'satisfaction_rate', 'n_satisfied']
print(segments.sort_values('satisfaction_rate', ascending=False))
```

### Task 3: Identify service improvement priorities
```python
service_cols = [
    'inflight_wifi_service',
    'ease_of_online_booking',
    'food_and_drink',
    'seat_comfort',
    'inflight_entertainment',
    'cleanliness'
]

# Average rating by satisfaction
service_gaps = pd.DataFrame({
    'satisfied': df[df['y'] == 1][service_cols].mean(),
    'dissatisfied': df[df['y'] == 0][service_cols].mean()
})

service_gaps['gap'] = service_gaps['satisfied'] - service_gaps['dissatisfied']
service_gaps = service_gaps.sort_values('gap', ascending=False)

print("\nService improvement priorities (biggest gaps):")
print(service_gaps)
```

## Next Steps

1. **Explore the CSV files** in Excel/Numbers to get familiar with the data
2. **Run the exploration script** to see comprehensive statistics
3. **Review the twin cards** in [DATA/airline/twins/](../DATA/airline/twins/) to see how personas are built from this data
4. **Check the cohort priors** in [DATA/airline/cohorts/cohort_priors.jsonl](../DATA/airline/cohorts/cohort_priors.jsonl) to see aggregated statistics
5. **Read the architecture doc** ([AIRLINE_ARCHITECTURE.md](AIRLINE_ARCHITECTURE.md)) to understand how data flows through the system

## Questions?

Common questions about the dataset:

**Q: Where does this data come from?**
A: Kaggle Airline Passenger Satisfaction Dataset (public domain)

**Q: Is 400 rows enough for analysis?**
A: Yes for MVP demonstration. We sampled 400 from 100k+ to create diverse twins while keeping costs manageable.

**Q: Can I add my own data?**
A: Yes! Follow the schema in [DATA/airline/airline_schema.json](../DATA/airline/airline_schema.json) and use [src/data/airline/airline_loader.py](../src/data/airline/airline_loader.py) to load it.

**Q: What if I want to see the full dataset?**
A: Download from Kaggle: https://www.kaggle.com/datasets/teejmahal20/airline-passenger-satisfaction

**Q: How were the 400 samples selected?**
A: Stratified sampling ensuring diversity across satisfaction, class, and travel type. See [scripts/resplit_airline_data.py](../scripts/resplit_airline_data.py).

## Related Files

- [AIRLINE_README.md](AIRLINE_README.md) - System overview
- [AIRLINE_ARCHITECTURE.md](AIRLINE_ARCHITECTURE.md) - Technical architecture
- [AIRLINE_EVALUATION.md](AIRLINE_EVALUATION.md) - Testing and validation
- [airline_schema.json](../DATA/airline/airline_schema.json) - Full schema definition
- [airline_expected_values.json](../DATA/airline/airline_expected_values.json) - Valid enum values

---

**Built with care by Darpan Labs**
