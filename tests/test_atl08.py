import pyproj
import pytest

from nsidc.icesat2gis.atl08 import (
    ATL08_DEFAULT_GT_CORE_VARS,
    ATL08_DEFAULT_VARIABLES_TO_CHECK_ALL_NULL,
    _linestring_for_isolated_point,
    _read_points_for_gt,
    lines_from_atl08_points,
    read_points_from_atl08,
)
from nsidc.icesat2gis.exceptions import IceSat2MissingDataError


def test_read_point_geoms_from_atl08(atl08_test_filepath):
    points = read_points_from_atl08(filepath=atl08_test_filepath)

    assert points is not None
    # One line per expected ground track (one is intentionally missing in the
    # test data - ATL08 generally has 6 ground tracks.)
    assert len(set(points.ground_track)) == 5

    for core_var in [
        var_path.rsplit("/", maxsplit=1)[-1] for var_path in ATL08_DEFAULT_GT_CORE_VARS
    ]:
        assert points[core_var] is not None


def test_lines_from_atl08_points(atl08_test_filepath):
    points = read_points_from_atl08(filepath=atl08_test_filepath)

    lines = lines_from_atl08_points(points=points)

    assert lines is not None
    assert len(lines.ground_track) == 5

    assert lines.delta_time_start is not None
    assert lines.delta_time_end is not None


def test__linestring_for_isolated_point(atl08_test_filepath):
    points = read_points_from_atl08(filepath=atl08_test_filepath)

    points_for_gt = points[points["ground_track"] == "gt3r"]
    # Filter down to just the first and last points
    points_for_gt = points_for_gt.iloc[[0, -1]]

    isolated_point = points_for_gt[points_for_gt.index == 0]

    geod = pyproj.Geod(ellps="WGS84")

    expected_line_len_meters = 17

    line = _linestring_for_isolated_point(
        isolated_point=isolated_point,
        points_for_track=points_for_gt,
        geod=geod,
        isolated_point_line_meters=expected_line_len_meters,
    )

    assert len(list(line.coords)) == 3

    # Middle coord should be the isolated point.
    assert list(line.coords)[1] == list(isolated_point.geometry[0].coords)[0]

    _, _, distance = geod.inv(
        lons1=[list(line.coords)[0][0]],
        lats1=[list(line.coords)[0][1]],
        lons2=[list(line.coords)[-1][0]],
        lats2=[list(line.coords)[-1][1]],
    )

    assert round(distance[0]) == expected_line_len_meters


def test__read_points_for_gt(atl08_test_filepath):
    points_gdf = _read_points_for_gt(
        ground_track="gt1l",
        filepath=atl08_test_filepath,
        variables_to_include=ATL08_DEFAULT_GT_CORE_VARS,
        variables_to_check_all_null=ATL08_DEFAULT_VARIABLES_TO_CHECK_ALL_NULL,
    )

    assert points_gdf is not None
    assert len(points_gdf) > 0


def test__read_points_for_gt_missing_raises_error(atl08_test_filepath):
    with pytest.raises(IceSat2MissingDataError):
        _read_points_for_gt(
            # We expect gt2l ground track to be missing from the test data.
            ground_track="gt2l",
            filepath=atl08_test_filepath,
            variables_to_include=ATL08_DEFAULT_GT_CORE_VARS,
            variables_to_check_all_null=ATL08_DEFAULT_VARIABLES_TO_CHECK_ALL_NULL,
        )


def test__read_points_for_gt_bad_variables_to_check_all_null(atl08_test_filepath):
    with pytest.raises(
        ValueError,
        match="All `variables_to_check_all_null` must be in `variables_to_include`",
    ):
        _read_points_for_gt(
            # We expect gt2l ground track to be missing from the test data.
            ground_track="gt2l",
            filepath=atl08_test_filepath,
            variables_to_include=ATL08_DEFAULT_GT_CORE_VARS,
            variables_to_check_all_null=["foo"],
        )
