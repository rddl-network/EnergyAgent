from app.energy_meter_interaction.energy_fetcher import DataFetcher


def main():
    data_fetcher = DataFetcher()
    data_fetcher.connect_to_mqtt()


if __name__ == "__main__":
    print("Starting data fetcher...")
    main()
    print("Data fetcher stopped")
