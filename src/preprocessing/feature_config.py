"""
Defines the canonical feature schema expected by the model.
This must stay in sync with the BigQuery `absenteeism_cleaned` view —
if the SQL view's columns change, update this list to match.
"""

FEATURE_COLUMNS = [
    'reason_1', 'reason_2', 'reason_3', 'reason_4',
    'month_value', 'day_of_week', 'transportation_expense',
    'distance_to_work', 'age', 'daily_work_load_average',
    'body_mass_index', 'education_binary', 'children', 'pets'
]