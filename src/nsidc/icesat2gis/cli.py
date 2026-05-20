"""CLI for icesat2gis"""

from pathlib import Path

import click

from nsidc.icesat2gis.atl08 import read_lines_from_atl08, read_points_from_atl08


@click.group()  # type: ignore[untyped-decorator]
def cli() -> None:
    pass


@cli.command()  # type: ignore[untyped-decorator]
@click.argument("input_filepath", required=True, type=click.Path(path_type=Path))  # type: ignore[untyped-decorator]
@click.argument("output_filepath", required=True, type=click.Path(path_type=Path))  # type: ignore[untyped-decorator]
def atl08_to_points(input_filepath: Path, output_filepath: Path) -> None:
    """Given an ATL08 hdf5 as input, output a file with point geometries."""
    points = read_points_from_atl08(filepath=input_filepath)

    points.to_file(output_filepath)


@cli.command()  # type: ignore[untyped-decorator]
@click.argument("input_filepath", required=True, type=click.Path(path_type=Path))  # type: ignore[untyped-decorator]
@click.argument("output_filepath", required=True, type=click.Path(path_type=Path))  # type: ignore[untyped-decorator]
@click.option(
    "--gap-threshold-meters",
    default=500,
    type=int,
    help="Length, in meters, between consecutive points that when exceeded should be considered a 'gap' and produce a new line segment.",
)  # type: ignore[untyped-decorator]
@click.option(
    "--simplify-line-tolerance",
    default=None,
    type=float,
    help="Simplify the line with the given tolerance. Tolerance is given in degrees. See https://shapely.readthedocs.io/en/stable/reference/shapely.simplify.html for more information. If not given, no simplification will be applied.",
)  # type: ignore[untyped-decorator]
def atl08_to_lines(
    input_filepath: Path,
    output_filepath: Path,
    gap_threshold_meters: int,
    simplify_line_tolerance: None | float,
) -> None:
    """Given an ATL08 hdf5 as input, output a file with line geometries."""
    lines = read_lines_from_atl08(
        filepath=input_filepath,
        gap_threshold_meters=gap_threshold_meters,
        simplify_line_tolerance=simplify_line_tolerance,
    )

    lines.to_file(output_filepath)


@cli.command()  # type: ignore[untyped-decorator]
@click.argument("input_filepath", required=True, type=click.Path(path_type=Path))  # type: ignore[untyped-decorator]
@click.argument(
    "output_dir",
    required=True,
    type=click.Path(
        file_okay=False, dir_okay=True, exists=True, writable=True, path_type=Path
    ),
)  # type: ignore[untyped-decorator]
@click.option(
    "--gap-threshold-meters",
    default=500,
    type=int,
    help="Length, in meters, between consecutive points that when exceeded should be considered a 'gap' and produce a new line segment.",
)  # type: ignore[untyped-decorator]
@click.option(
    "--simplify-line-tolerance",
    default=None,
    type=float,
    help="Simplify the line with the given tolerance. Tolerance is given in degrees. See https://shapely.readthedocs.io/en/stable/reference/shapely.simplify.html for more information. If not given, no simplification will be applied.",
)  # type: ignore[untyped-decorator]
def atl08_to_lines_parquet(
    input_filepath: Path,
    output_dir: Path,
    gap_threshold_meters: int,
    simplify_line_tolerance: None | float,
) -> None:
    """Given an ATL08 hdf5 as input, output a file with line geometries as geoparquet."""
    lines = read_lines_from_atl08(
        filepath=input_filepath,
        gap_threshold_meters=gap_threshold_meters,
        simplify_line_tolerance=simplify_line_tolerance,
    )

    output_filepath = output_dir / (input_filepath.stem + ".parquet")
    lines.to_parquet(output_filepath)


@cli.command()  # type: ignore[untyped-decorator]
@click.argument(
    "input_dir",
    required=True,
    type=click.Path(
        file_okay=False, dir_okay=True, exists=True, writable=True, path_type=Path
    ),
)  # type: ignore[untyped-decorator]
@click.argument(
    "output_dir",
    required=True,
    type=click.Path(
        file_okay=False, dir_okay=True, exists=True, writable=True, path_type=Path
    ),
)  # type: ignore[untyped-decorator]
@click.option(
    "--gap-threshold-meters",
    default=500,
    type=int,
    help="Length, in meters, between consecutive points that when exceeded should be considered a 'gap' and produce a new line segment.",
)  # type: ignore[untyped-decorator]
@click.option(
    "--simplify-line-tolerance",
    default=None,
    type=float,
    help="Simplify the line with the given tolerance. Tolerance is given in degrees. See https://shapely.readthedocs.io/en/stable/reference/shapely.simplify.html for more information. If not given, no simplification will be applied.",
)  # type: ignore[untyped-decorator]
def lines_in_dir(
    input_dir: Path,
    output_dir: Path,
    gap_threshold_meters: int,
    simplify_line_tolerance: None | float,
) -> None:
    """Produce parquet files containing ATL08 lines for all of the ATL08 .h5 files in a directory."""
    for input_filepath in input_dir.glob("*.h5"):
        print(f"processing {input_filepath}")
        try:
            lines = read_lines_from_atl08(
                filepath=input_filepath,
                gap_threshold_meters=gap_threshold_meters,
                simplify_line_tolerance=simplify_line_tolerance,
            )

            output_filepath = output_dir / (input_filepath.stem + ".parquet")
            lines.to_parquet(output_filepath)
        except Exception as e:
            print(f"Problem processing {input_filepath}.")
            print(e)


if __name__ == "__main__":
    cli()
