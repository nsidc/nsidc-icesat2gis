# v0.3.0 (TBD)

- Handle missing ground track data gracefully. Raise an `IceSatMissingDataError`
  when no data exists in a granule at all.
- Remove aggregate statistics fields from ATL08 linestrings (e.g.,
  `h_canopy_mean`). These are not very informative on linestring geometries
  because they cover such a large area.

# v0.2.0 (2026-05-08)

- First pypi release.
- Initial structure and functionality defined for ATL08.
