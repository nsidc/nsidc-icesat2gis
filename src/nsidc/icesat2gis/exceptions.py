class ICESat2GISError(Exception):
    """Base exception for ICESat2GISError.

    Something specific to the `icesat2gis` library has gone wrong. More specific
    exceptions should inherit this one.
    """


class ICESat2MissingDataError(ICESat2GISError):
    """Raised when there expected data is missing from an ICESat granule.

    This is often expected. E.g., ATL08 produces empty granules even when there
    are no valid data.
    """
