# v0.3.0 (2025-05-20)

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
