"""Create test atl08 data for unit tests.

NOTE: This script relies on the assumption that the user has downloaded
`ATL08_20260118035703_05313006_007_01.h5` and placed it ../data/.
"""

from collections import defaultdict
from pathlib import Path

import xarray as xr

from nsidc.icesat2gis.atl08 import ATL08_DEFAULT_GT_CORE_VARS

TEST_DIR = Path(__file__).parent / ".." / "tests"

SOURCE_DATA_PATH = (
    Path(__file__).parent / ".." / "data" / "ATL08_20260118035703_05313006_007_01.h5"
)

if not SOURCE_DATA_PATH.is_file():
    msg = "Source data path does not exist."
    raise RuntimeError(msg)


if __name__ == "__main__":
    test_data_dir = TEST_DIR / "data"
    test_data_dir.mkdir(exist_ok=True, parents=True)
    test_data_filepath = test_data_dir / "test_atl08.h5"

    # Remove the existing test data file if it already exists.
    test_data_filepath.unlink(missing_ok=True)

    # Note: "gt2l" is intentionally missing to test cases where one or more
    # ground tracks have no data.
    for ground_track in ("gt1l", "gt1r", "gt2r", "gt3l", "gt3r"):
        ds = xr.open_datatree(
            SOURCE_DATA_PATH,
            group=f"{ground_track}/land_segments/",
            chunks={},
        )
        lats = ds.latitude
        filtered_lats = xr.concat(
            [
                # First 50 observations
                lats.isel(delta_time=slice(0, 50)),
                # One isolated point in the middle
                lats.isel(delta_time=int(len(lats) / 2)),
                # Last 50 observations
                lats.isel(delta_time=slice(-50, None)),
            ],
            dim="delta_time",
            coords="minimal",
        )
        lons = ds.longitude
        filtered_lons = xr.concat(
            [
                # First 50 observations
                lons.isel(delta_time=slice(0, 50)),
                # One isolated point in the middle
                lons.isel(delta_time=int(len(lons) / 2)),
                # Last 50 observations
                lons.isel(delta_time=slice(-50, None)),
            ],
            dim="delta_time",
            coords="minimal",
        )

        variables = defaultdict(dict)
        for var_path in ATL08_DEFAULT_GT_CORE_VARS:
            group_name, var_name = var_path.split("/")
            data_var = ds[var_path]
            variables[group_name][var_name] = xr.concat(
                [
                    # First 50 observations
                    data_var.isel(delta_time=slice(0, 50)),
                    # One isolated point in the middle
                    data_var.isel(delta_time=int(len(data_var) / 2)),
                    # Last 50 observations
                    data_var.isel(delta_time=slice(-50, None)),
                ],
                dim="delta_time",
                coords="minimal",
            )

        test_ds = xr.DataTree.from_dict(
            {
                f"{ground_track}/land_segments/": {
                    "latitude": filtered_lats,
                    "longitude": filtered_lons,
                    **variables,
                }
            },
            nested=True,
        )

        test_ds.to_netcdf(
            test_data_filepath,
            mode="a",
        )
