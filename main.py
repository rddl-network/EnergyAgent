import asyncio
from app.energy_meter_interaction.energy_fetcher import DataFetcher


async def main():
    data_fetcher = DataFetcher()
    await data_fetcher.fetch_data()


if __name__ == "__main__":
    print("Starting data fetcher...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    print("Data fetcher stopped")
