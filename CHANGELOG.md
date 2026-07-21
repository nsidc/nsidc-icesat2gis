# v0.6.0 (2026-07-21)

ATL08 updates:

- Update dtypes for `orbit_number` (`int64` -> `int32`) and `cycle_number`
  (`int64` -> `int16`).

# v0.5.0 (2026-07-20)

ATL08 updates:

- Add `bm_strength` field that indicates beam strength (weak or strong) for each
  point.
- Add new default variables for ATL08 points based on feedback from user
  community survey.
- Decode flag values into their string representation.
- Add `utc_timestamp_string` to ensure that the full resolution datetime data
  are included when writing to formats (e.g., geopackage) that have reduced
  datetime precision.
- Rename decoded `delta_time` to `datetime`.
- Add new functions `geodataframe_from_atl08` and `dataframe_from_atl08`,
  separating logic between reading data as a `pandas.DataFrame` and a
  `geopandas.GeoDataFrame`.

# v0.4.0 (2026-06-01)

- Support earthaccess workflow:
  - Add support for passing an `earthaccess.store.EarthAccessFile` (from
    `earthaccess.open`) in place of a local filepath.
  - Add `get_atl08_points` that searches for matching granules via earthacces
    and iterates through them, yielding GeoDataFrames of points for each
    granule.

# v0.3.0 (2026-05-20)

- Handle missing ground track data gracefully. Raise an
  `ICESat2MissingDataError` when no data exists in a granule at all.
- Remove aggregate statistics fields from ATL08 linestrings (e.g.,
  `h_canopy_mean`). These are not very informative on linestring geometries
  because they cover such a large area.
- Add core variables identified in
  [NDS-10](https://bugs.earthdata.nasa.gov/browse/NDS-10) to points by default.
  Allow custom sets of variables via the `gt_variables_to_include` kwarg to
  `read_points_from_atl08`
- Drop points where, by default, `canopy/h_canopy` and `terrain/h_te_best_fit`
  are null.
- Add CLI to project scripts (`nsidc-icesat2gis`)

# v0.2.0 (2026-05-08)

- First pypi release.
- Initial structure and functionality defined for ATL08.
