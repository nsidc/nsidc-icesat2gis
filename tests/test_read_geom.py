from pathlib import Path

import pyproj

from nsidc.icesat2gis.read_geom import (
    _linestring_for_isolated_point,
    lines_from_atl08_points,
    read_points_from_atl08,
)

_THIS_DIR = Path(__file__).parent
TEST_DATA_DIR = _THIS_DIR / "data"


def test_read_point_geoms_from_atl08():
    test_data_path = TEST_DATA_DIR / "test_atl08.h5"

    points = read_points_from_atl08(filepath=test_data_path)

    assert points is not None
    # One line per expected ground track
    assert len(set(points.ground_track)) == 6

    assert points.h_canopy is not None

    assert points.delta_time is not None


def test_lines_from_atl08_points():
    test_data_path = TEST_DATA_DIR / "test_atl08.h5"

    points = read_points_from_atl08(filepath=test_data_path)

    lines = lines_from_atl08_points(points=points)

    assert lines is not None
    # One line per expected ground track
    assert len(lines.ground_track) == 6

    assert lines.h_canopy_min is not None
    assert lines.h_canopy_max is not None
    assert lines.h_canopy_std is not None
    assert lines.h_canopy_mean is not None

    assert lines.delta_time_start is not None
    assert lines.delta_time_end is not None


def test__linestring_for_isolated_point():
    test_data_path = TEST_DATA_DIR / "test_atl08.h5"

    points = read_points_from_atl08(filepath=test_data_path)

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
