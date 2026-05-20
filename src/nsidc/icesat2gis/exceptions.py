class IceSat2GISError(Exception):
    """Base exception for IceSat2GISError.

    Something specific to the `icesat2gis` library has gone wrong. More specific
    exceptions should inherit this one.
    """


class IceSatMissingDataError(IceSat2GISError):
    """Raised when there expected data is missing from an IceSat granule.

    This is often expected. E.g., ATL08 produces empty granules even when there
    are no valid data.
    """
