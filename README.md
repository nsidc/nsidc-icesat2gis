<p align="center">
  <img alt="NSIDC logo" src="https://nsidc.org/themes/custom/nsidc/logo.svg" width="150" />
</p>

# ICESat-2 to GIS conversion utilities

<!-- prettier-ignore -->
> [!WARNING]
> This repository is in early phases of development and currently focuses on
> ATL08. The intention is to generalize for other ICESat-2 products in the
> future.

Code for converting ICESat-2 (ATL08) .h5 data into GIS-compatible points and
polylines.

## Installation

`pip install nsidc-icesat2gis`

## Usage

`nsidc-icesat2gis` is primarily intended to be used programmatically as a Python
library:

```
from nsidc.icesat2gis.atl08 import read_points_from_atl08


points_geodataframe = read_points_from_atl08(filepath="/path/to/example/ATL08_20260118035703_05313006_007_01.h5")
```

A CLI is also available:

```
$ nsidc-icesat2gis --help
Usage: nsidc-icesat2gis [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  atl08-to-lines          Given an ATL08 hdf5 as input, output a file...
  atl08-to-lines-parquet  Given an ATL08 hdf5 as input, output a file...
  atl08-to-points         Given an ATL08 hdf5 as input, output a file...
  lines-in-dir            Produce parquet files containing ATL08 lines...

```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## Level of Support

This repository is not actively supported by NSIDC but we welcome issue
submissions and pull requests in order to foster community contribution.

See the [LICENSE](LICENSE) for details on permissions and warranties. Please
contact nsidc@nsidc.org for more information.

## Credit

This content was developed by the National Snow and Ice Data Center with funding
from multiple sources.
