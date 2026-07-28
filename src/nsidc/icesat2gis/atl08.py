from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Literal, cast, get_args

import earthaccess
import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from pyproj import Geod
from shapely import LineString, Point
from shapely.geometry import MultiLineString

from nsidc.icesat2gis.exceptions import ICESat2GISError, ICESat2MissingDataError

GroundTrack = Literal["gt1l", "gt1r", "gt2l", "gt2r", "gt3l", "gt3r"]


# Default ground_track core variables for ATL08.
ATL08_DEFAULT_GT_CORE_VARS = (
    # Canopy variables
    "canopy/h_canopy",
    "canopy/h_canopy_uncertainty",
    "canopy/h_min_canopy",
    "canopy/h_max_canopy",
    "canopy/h_median_canopy",
    "canopy/h_mean_canopy",
    "canopy/h_canopy_abs",
    "canopy/h_min_canopy_abs",
    "canopy/h_max_canopy_abs",
    "canopy/h_median_canopy_abs",
    "canopy/h_mean_canopy_abs",
    "canopy/canopy_openness",
    "canopy/h_dif_canopy",
    "canopy/photon_rate_can",
    "canopy/canopy_h_metrics",
    # Terrain variables
    "terrain/h_te_best_fit",
    "terrain/h_te_uncertainty",
    "terrain/terrain_slope",
    "terrain/h_te_min",
    "terrain/h_te_max",
    "terrain/h_te_median",
    "terrain/h_te_mean",
    "terrain/photon_rate_te",
    # Reference information
    "solar_elevation",
    "brightness_flag",
    "urban_flag",
    "rgt",
    "layer_flag",
    "msw_flag",
    "dem_h",
    # Lat/lon included separately as columns for easy queries.
    "latitude",
    "longitude",
)

ATL08_DEFAULT_VARIABLES_TO_CHECK_ALL_NULL = (
    "canopy/h_canopy",
    "terrain/h_te_best_fit",
)


BeamStrength = Literal["weak", "strong"]


def _beam_strength_from_orientation(
    *,
    ground_track: GroundTrack,
    orientation: int,
) -> BeamStrength:
    """Return 'weak' or 'strong' depending on the ground track and spacecraft orientation.

    Orientation can be found in the "orbit_info/sc_orient" variable and take a
    value of either 0, 1, or 2. A value of 0 indicates that the spacecraft is
    flying in the "backwards" configuration. A value of 1 indicates that the
    spacecraft is flying in the "forward" orientation, and a value of 2
    indicates that the spacecraft is in transition. This function will raise an
    error if a value of 2 is encountered.
    """
    if orientation not in (0, 1):
        msg = "Expected a spacecraft orientation value of 0 or 1. Got: {orientation=}"
        raise ICESat2GISError(msg)

    orientation_mapping: dict[int, dict[GroundTrack, BeamStrength]] = {
        # Backward config
        0: {
            "gt1l": "strong",
            "gt1r": "weak",
            "gt2l": "strong",
            "gt2r": "weak",
            "gt3l": "strong",
            "gt3r": "weak",
        },
        # Forward config
        1: {
            "gt1l": "weak",
            "gt1r": "strong",
            "gt2l": "weak",
            "gt2r": "strong",
            "gt3l": "weak",
            "gt3r": "strong",
        },
    }

    beam_strength = orientation_mapping[orientation][ground_track]

    return beam_strength


def _read_points_for_gt(
    *,
    ground_track: GroundTrack,
    ds: xr.DataTree,
    filename: str,
    variables_to_include: Sequence[str],
    variables_to_check_all_null: Sequence[str],
) -> gpd.GeoDataFrame:
    """Reads 100m segment points from ATL08 for the given ground track.

    Raises an `ICESat2MissingDataError` when a ground track is missing data
    (either the ground track group or the ground track's `land_segments` group
    is missing).

    * `ground_track`: one of "gt1l", "gt1r", "gt2l", "gt2r", "gt3l", "gt3r"
    * `filepath`: filepath to the ATL08 granule
    * `variables_to_include`: sequence of strings representing GT variables to
      include in the output (e.g,. `"canopy/h_canopy"`).
    * `variables_to_check_all_null`: sequence of strings representing GT
      variables to check for Null values. If all of the variables specified in
      this sequence are Null for a record, that record is excluded.
    """
    if not all(
        var_to_check in variables_to_include
        for var_to_check in variables_to_check_all_null
    ):
        msg = (
            f"All `variables_to_check_all_null` must be in `variables_to_include`."
            f"Got {variables_to_include=} {variables_to_check_all_null=}."
        )
        raise ValueError(msg)

    if len(ds["orbit_info/sc_orient"]) != 1:
        msg = (
            "Expected granule to contain single `sc_orient`."
            f" Got {len(ds['orbit_info/sc_orient'])}"
        )
        raise ICESat2GISError(msg)

    try:
        land_seg_group = ds[f"{ground_track}/land_segments/"]
    except KeyError as e:
        # This could be because the ground track group is missing, or the
        # `land_segments` group is missing.
        msg = f"No `land_segment` data for {ground_track} from {filename}: {e}"
        print(msg)
        raise ICESat2MissingDataError(msg) from e

    # Extract variables
    delta_time = land_seg_group.delta_time

    variables = {}
    for var_path in variables_to_include:
        var_name = var_path.rsplit("/", maxsplit=1)[-1]
        variable = land_seg_group[var_path]
        if "canopy_h_metrics" in var_name:
            # Special case for canopy_h_metrics. This must be broken out into
            # multiple columns.
            # Create a list of values from 10-95 at increments of 5.
            metrics_percents = list(range(10, 95 + 5, 5))
            metrics_array = variable.to_numpy()  # Shape: (n_points, n_metrics)
            for idx, percent in enumerate(metrics_percents):
                variables[f"{var_name}{percent}"] = metrics_array[:, idx]
        elif "flag_meanings" in variable.attrs:
            # Decode flag meanings
            flag_meanings = variable.flag_meanings.split(" ")
            decoded_values = np.array(flag_meanings)[variable.to_numpy()]
            variables[var_name] = decoded_values
        else:
            # Just use the variable as-is
            variables[var_name] = variable.to_numpy()

    # Get the beam strength
    sc_orientation = int(ds["orbit_info/sc_orient"][0])
    beam_strength = _beam_strength_from_orientation(
        ground_track=ground_track,
        orientation=sc_orientation,
    )

    # Construct df from variables
    df = pd.DataFrame(variables)

    # Add other columns. Scalars are broadcast to the correct len.
    # Reference info
    df["ground_track"] = ground_track
    df["source_filename"] = filename
    df["bm_strength"] = beam_strength
    # rename to datetime, since this has been decoded to datetime
    # objects.
    df["datetime"] = delta_time
    # Get orbit characteristics
    df["orbit_number"] = np.int32(ds["orbit_info/orbit_number"][0])
    df["cycle_number"] = np.int16(ds["orbit_info/cycle_number"][0])

    # Drop points that are all-NaN for the user's selected variables.
    if variables_to_check_all_null:
        variables_to_check_all_null_names = [
            var.rsplit("/", maxsplit=1)[-1] for var in variables_to_check_all_null
        ]
        df = df.dropna(
            subset=variables_to_check_all_null_names,
            how="all",
        ).reset_index(drop=True)

    # Localize the timestamp to UTC. Otherwise it inherits the system TZ
    # (e.g., MST).
    df["datetime"] = df.datetime.dt.tz_localize("UTC")

    return df


def dataframe_from_atl08(
    *,
    filepath: Path | earthaccess.store.EarthAccessFile,
    gt_variables_to_include: Sequence[str] = ATL08_DEFAULT_GT_CORE_VARS,
    gt_variables_to_check_all_null: Sequence[
        str
    ] = ATL08_DEFAULT_VARIABLES_TO_CHECK_ALL_NULL,
) -> pd.DataFrame:
    """Return a pandas DataFrame containing points representing ground tracks."""
    ds = xr.open_datatree(
        filepath,
        chunks={},
        phony_dims="sort",
    )

    filename = Path(ds.encoding["source"]).name

    dfs = []
    for ground_track in get_args(GroundTrack):
        try:
            df = _read_points_for_gt(
                ground_track=ground_track,
                filename=filename,
                ds=ds,
                variables_to_include=gt_variables_to_include,
                variables_to_check_all_null=gt_variables_to_check_all_null,
            )
            dfs.append(df)
        except ICESat2MissingDataError:
            continue

    if not dfs:
        msg = f"Found no valid ground track data for {filepath}"
        raise ICESat2MissingDataError(msg)

    combined_df = pd.concat(dfs)
    combined_df.attrs["source_filename"] = filename

    # Create utc timestamp string as a field. The datetime field itself loses
    # precision on write, so it is worth maintaining a timestamp as a string
    # column.
    combined_df["utc_timestamp_string"] = combined_df["datetime"].apply(
        lambda x: x.isoformat()
    )

    combined_df = cast("pd.DataFrame", combined_df)

    return combined_df


def geodataframe_from_atl08(
    *,
    filepath: Path | earthaccess.store.EarthAccessFile,
    gt_variables_to_include: Sequence[str] = ATL08_DEFAULT_GT_CORE_VARS,
    gt_variables_to_check_all_null: Sequence[
        str
    ] = ATL08_DEFAULT_VARIABLES_TO_CHECK_ALL_NULL,
) -> gpd.GeoDataFrame:
    """Return a GeoDataFrame containing points representing ground tracks."""
    df = dataframe_from_atl08(
        filepath=filepath,
        gt_variables_to_include=gt_variables_to_include,
        gt_variables_to_check_all_null=gt_variables_to_check_all_null,
    )

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326",
    )

    gdf = cast("gpd.GeoDataFrame", gdf)

    return gdf


def read_points_from_atl08(
    *,
    filepath: Path | earthaccess.store.EarthAccessFile,
    gt_variables_to_include: Sequence[str] = ATL08_DEFAULT_GT_CORE_VARS,
    gt_variables_to_check_all_null: Sequence[
        str
    ] = ATL08_DEFAULT_VARIABLES_TO_CHECK_ALL_NULL,
) -> gpd.GeoDataFrame:
    """Return a GeoDataFrame containing points representing ground tracks."""
    return geodataframe_from_atl08(
        filepath=filepath,
        gt_variables_to_include=gt_variables_to_include,
        gt_variables_to_check_all_null=gt_variables_to_check_all_null,
    )


def get_atl08_points(**search_kwargs) -> Iterator[gpd.GeoDataFrame]:
    """Use `earthaccess` to find matching granules and return as points gdfs.

    Requires earthdata login credentials.

    Yields one geodataframe per matching granule.
    """
    earthaccess.login()
    results = earthaccess.search_data(short_name="ATL08", **search_kwargs)

    print(f"Found {len(results)} granules with {search_kwargs=}")

    for result in results:
        ea_files = earthaccess.open([result])
        points = read_points_from_atl08(filepath=ea_files[0])
        yield points


def _linestring_for_isolated_point(
    *,
    isolated_point: gpd.GeoDataFrame,
    points_for_track: gpd.GeoDataFrame,
    geod: Geod,
    isolated_point_line_meters: int,
) -> LineString:
    """Return a linestring for a single isolated point.

    The single point is placed at the center of the linestring of
    `isolated_point_line_meters` length.
    """
    point_idx = int(isolated_point.index[0])
    if point_idx == 0:
        adjacent_point = points_for_track.iloc[1]
    else:
        adjacent_point = points_for_track.iloc[point_idx - 1]

    # Find the forward azimuth between the isolated point and it's adjacent point
    fwd_az, back_az, _ = geod.inv(
        # Ensure all lat/lon inputs are a list of floats. FutureWarning is raised from
        # the pyproj internals otherwise.
        lons1=[float(isolated_point.geometry.x.to_numpy()[0])],
        lats1=[float(isolated_point.geometry.y.to_numpy()[0])],
        lons2=[float(adjacent_point.geometry.x)],
        lats2=[float(adjacent_point.geometry.y)],
    )

    # Use the fwd and back azimuth to project points away from the
    # isolated point to construct a short line
    new_fwd_lon, new_fwd_lat, _ = geod.fwd(
        # Ensure all lat/lon inputs are a list of floats. FutureWarning is raised from
        # the pyproj internals otherwise.
        lons=[float(isolated_point.geometry.x.to_numpy()[0])],
        lats=[float(isolated_point.geometry.y.to_numpy()[0])],
        az=fwd_az,
        dist=isolated_point_line_meters / 2,
    )

    new_back_lon, new_back_lat, _ = geod.fwd(
        # Ensure all lat/lon inputs are a list of floats. FutureWarning is raised from
        # the pyproj internals otherwise.
        lons=[float(isolated_point.geometry.x.to_numpy()[0])],
        lats=[float(isolated_point.geometry.y.to_numpy()[0])],
        az=back_az,
        dist=isolated_point_line_meters / 2,
    )

    line = LineString(
        [
            Point(new_back_lon, new_back_lat),
            *isolated_point.geometry.to_list(),
            Point(new_fwd_lon, new_fwd_lat),
        ]
    )

    return line


def lines_from_atl08_points(
    *,
    points: gpd.GeoDataFrame,
    gap_threshold_meters: int = 500,
    isolated_point_line_meters: int = 17,  # 17m is the approx. ground spot size of ICESat2.
    simplify_line_tolerance: None | float = None,
) -> gpd.GeoDataFrame:
    """Return a GeoDataFrame containing linestrings representing ground tracks.

    GeoDataFrame contains one MultiLineString per ground track from the
    `land_segments` group in the given ATL08 filepath.

    Each consitutient LineString in the MultiLineString for a ground track
    represents a continuous line of points with valid observations. Gaps greater
    than `gap_threshold_meters` are where linestrings are split, so that no-data
    areas are more obvious.

    NOTE: Single isolated points are represented by a line 17m in length (which
    is the approx. ground spot size of ICESat2). The isolated point lies at the
    center of the line, and endpoints are projected out from it (8.5m in each
    direction). We do this so that single points can be represented without
    needing to mix geometry types (which is usually not possible in a single GIS
    layer). This is a bit misleading, but is probably better than dropping
    the point or connecting it to an adjacent line that might be far away.

    TODO/NOTE: currently, lines are constructed from the lat/lon pairs from the
    ATL08 data file, but the ground resolution/area of each point is not
    considered (i.e., the footprint size of each spot on the ground is
    ~17m). Maybe we should buffer endpoints of lines to account for the spot
    size? Isolated points are represented as a line 17m in
    length and the isolated point is the center of that line. This is
    also be misleading, because we would only be representing this in one axis
    (line length - polyons would be necessary to capture the actual "shape" of
    the ground track).
    """
    geod = Geod(ellps="WGS84")
    multi_linestrings = {}
    for ground_track in set(points.ground_track):
        points_for_track = points[points.ground_track == ground_track].copy()

        # Distances between consecutive pairs in meters
        _, _, distances = geod.inv(
            lons1=points_for_track.geometry.x[:-1],
            lats1=points_for_track.geometry.y[:-1],
            lons2=points_for_track.geometry.x[1:],
            lats2=points_for_track.geometry.y[1:],
        )

        # Find gaps where distances are gt the threshold
        gaps = np.where(distances > gap_threshold_meters)[0]
        # create groupings of indices for each linestring, split by the gaps
        # found above.
        groups = np.searchsorted(gaps, points_for_track.index)

        points_for_track["group"] = groups

        lines = []
        for group_idx in set(groups):
            points_for_group = points_for_track[points_for_track.group == group_idx]
            if len(points_for_group) == 1:
                line = _linestring_for_isolated_point(
                    isolated_point=points_for_group,
                    points_for_track=points_for_track,
                    geod=geod,
                    isolated_point_line_meters=isolated_point_line_meters,
                )
            else:
                line = LineString(points_for_group.geometry.to_list())

            if simplify_line_tolerance is not None:
                # Apply simplification to the line.
                line = line.simplify(tolerance=0.0001)

            lines.append(line)

        multi_line = MultiLineString(lines=list(lines))

        # Track multilinestring and attrs per ground track
        multi_linestrings[ground_track] = {
            "geometry": multi_line,
            "datetime_start": points_for_track.datetime.min(),
            "datetime_end": points_for_track.datetime.max(),
        }

    all_lines = gpd.GeoDataFrame(
        data={
            "ground_track": list(multi_linestrings.keys()),
            "source_filename": [list(set(points.source_filename))[0]]
            * len(multi_linestrings),
            "datetime_start": [
                line["datetime_start"] for line in multi_linestrings.values()
            ],
            "datetime_end": [
                line["datetime_end"] for line in multi_linestrings.values()
            ],
        },
        geometry=[line["geometry"] for line in multi_linestrings.values()],
        crs="EPSG:4326",
    )

    return all_lines


def read_lines_from_atl08(
    *,
    filepath: Path | earthaccess.store.EarthAccessFile,
    gap_threshold_meters: int = 500,
    isolated_point_line_meters: int = 17,  # 17m is the approx. ground spot size of ICESat2.
    simplify_line_tolerance: None | float = None,
) -> gpd.GeoDataFrame:
    points = read_points_from_atl08(filepath=filepath)

    lines = lines_from_atl08_points(
        points=points,
        gap_threshold_meters=gap_threshold_meters,
        simplify_line_tolerance=simplify_line_tolerance,
        isolated_point_line_meters=isolated_point_line_meters,
    )

    return lines
