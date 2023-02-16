"""
Prerequisite:
DB should be clean

To run:
docker exec -it app-business-logic python -m app.mock_scripts.generate_time_series_data start_date end_date time_delta num_machine

example:
docker exec -it app-business-logic python -m app.mock_scripts.generate_time_series_data "2023, 1, 1, 0, 0, 0" "2024, 1, 1, 0, 0, 0"  15 10
"""

import argparse
import os
import random
import string
import sys
import time
from datetime import date, datetime, timedelta

from app.database.schema import DaoMachine, DaoTimeSeriesData
from app.dependencies import get_db


def handle_date(date_string: str):
    values = date_string.split(", ")
    numeric_values = []
    for value in values:
        numeric_values.append(int(value))
    return datetime(*numeric_values)


def generate_public_key():
    # key = RSA.generate(2048)
    # public_key = key.publickey().export_key()
    # return public_key.decode()
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=256))


def generate_value(current_date):
    # Determine the value range based on the current date and time
    if 0 <= current_date.hour < 6:
        value_range = (0.5, 2) if (3 <= current_date.month <= 9 and current_date.hour >= 5) else (0, 0)
    elif 6 <= current_date.hour < 12:
        value_range = (2, 4) if (3 <= current_date.month <= 9) else (1, 2)
    elif 12 <= current_date.hour < 18:
        value_range = (3, 5) if (3 <= current_date.month <= 9) else (1, 3)
    else:
        value_range = (0.5, 3) if (3 <= current_date.month <= 9 and 18 < current_date.hour < 20) else (0, 0)

    # Generate a random value within the chosen range
    return random.uniform(*value_range)


def generate_time_series_data():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("start_date", help="Start date in yyyy-mm-dd H:MM:SS format")
    parser.add_argument("end_date", help="End date in yyyy-mm-dd H:MM:SS format")
    parser.add_argument("time_delta", help="Time delta in minutes")
    parser.add_argument("num_machines", type=int, help="Number of machines")
    args = parser.parse_args()

    # Convert command line arguments to appropriate types
    start_date = handle_date(args.start_date)
    end_date = handle_date(args.end_date)
    time_delta = int(args.time_delta)
    num_machines = args.num_machines

    # Check if the command line arguments are valid
    if start_date is None:
        print("Please provide a valid start date in the format yyyy-mm-dd")
        return

    if end_date is None:
        print("Please provide a valid end date in the format yyyy-mm-dd")
        return

    if time_delta <= 0:
        print("Please provide a valid time delta in minutes")
        return

    if num_machines <= 0:
        print("Please provide a valid number of machines")
        return

    start = time.time()

    # Generate public keys and insert machines into the database
    public_keys = [generate_public_key() for i in range(num_machines)]
    machines = [{'machine_id': public_keys[i], 'machine_type': 'energy_source'} for i in range(num_machines)]
    with next(get_db()) as db:
        db.execute(DaoMachine.__table__.insert().values(machines))
        db.commit()

    # Generate time series data and insert into the database
    batch_size = 1000
    with next(get_db()) as db:
        machines = db.query(DaoMachine).all()
        for machine in machines:
            time_series_data = []
            last_value = 0
            current_date = start_date
            while current_date < end_date:
                last_value += generate_value(current_date)
                time_series_data.append(
                    {'timestamp': current_date, 'absolute_energy': last_value, 'unit': 'kWh', 'machine_id': machine.id})
                current_date += timedelta(minutes=time_delta)
                if len(time_series_data) >= batch_size:
                    db.execute(DaoTimeSeriesData.__table__.insert().values(time_series_data))
                    db.commit()
                    time_series_data = []
            if len(time_series_data) > 0:
                db.execute(DaoTimeSeriesData.__table__.insert().values(time_series_data))
                db.commit()

    end = time.time()
    print(f"Elapsed time: {end - start:.2f} seconds")


generate_time_series_data()
