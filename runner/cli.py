"""Command line interface for k8s script runner."""

import click

@click.command()
def main() -> None:
    """Entry point for the k8s script runner CLI."""
    click.echo("k8s-script-runner invoked")

if __name__ == "__main__":
    main()
