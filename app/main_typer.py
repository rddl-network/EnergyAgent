import typer

from app.energy_meter_interaction.energy_fetcher import DataFetcher

app = typer.Typer()


@app.command()
def fetch_data():
    data_fetcher = DataFetcher()
    data_fetcher.fetch_data()


if __name__ == "__main__":
    app()
