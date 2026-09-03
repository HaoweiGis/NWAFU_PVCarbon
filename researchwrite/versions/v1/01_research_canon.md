# Research canon

## Verified local facts

- The main PV archive contains 30,023 polygons in WGS84 with installation dates/years covering 2010–2022, polygon area, pre-existing major land type and centroid coordinates.
- The PV archive does not contain capacity, generation, Site ID, Phase ID or post-construction agricultural-activity retention.
- The PV dataset corresponds to the Remote Sensing of Environment article DOI `10.1016/j.rse.2024.114100`.
- CLCD 2000–2025 contains 26 annual 30 m rasters on the server and is the only land-cover time series permitted in the V1 main analysis.
- The agrivoltaics archive contains 1,174 spatial objects and 1,678 project rows with non-missing capacity, but is a subset rather than a national capacity inventory.
- ERA5-Land is present but has at least three `.part` files and is not yet approved as complete.

## Central definitions

- `A_induced`: observed stable new cropland minus counterfactual stable new cropland attributable to cropland-sited PV.
- Responsibility county: county containing the causal PV Phase.
- Territorial county: county where induced land conversion and carbon emissions occur.
- iLUC peak year: year with the maximum attributable annual iLUC emissions within the stated observation window.
- iLUC carbon-payback year: first year cumulative PV gross avoided emissions equal or exceed cumulative attributable iLUC emissions.

## Forbidden claims

- Do not equate all observed new cropland with induced expansion.
- Do not call PV–cropland overlap effective cropland loss unless agricultural activity is measured.
- Do not claim county-wide carbon peaking or carbon neutrality.
- Do not label a projected post-2022 peak/payback year as observed.
- Do not splice CACD and CLCD or use CACD in V1.
- Do not use average grid emission factors as unlabelled substitutes for marginal factors.

## Unresolved claims

- Whether cropland-sited PV causally increases off-site stable new cropland.
- Whether an identifiable distance-decay relationship exists.
- Magnitude and spatial origin of attributable iLUC emissions.
- Whether and when county-level PV avoided emissions pay back iLUC emissions.
