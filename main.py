import asyncio
from app.dependencies import ensure_database
from app.energy_meter_interaction.energy_fetcher import DataFetcher


async def main():
    while True:
        try:
            ensure_database()
            break
        except Exception as e:
            print(e)
            print("Database seems to be down or initializing. Retrying in 5 seconds...")
            await asyncio.sleep(5)

    data_fetcher = DataFetcher()
    await data_fetcher.fetch_data()


if __name__ == "__main__":
    print("Starting data fetcher...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    print("Data fetcher stopped")
