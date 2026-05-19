class IceSatMissingDataError(Exception):
    """Raised when there expected data is missing from an IceSat granule.

    This is often expected. E.g., ATL08 produces empty granules even when there
    are no valid data.
    """
