// SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
// All user-facing strings live here (NFR15). Portuguese (pt.ts) is a stretch goal.
// The product name and concept are team decisions (C1): keep the working title until DECISIONS.md says otherwise.
export const en = {
  "meta.title": "FieldShift (working title)",
  "meta.description": "NASA Space Apps Challenge 2026 project. Work in progress.",
  "canary.heading": "FieldShift (working title)",
  "canary.body": "NASA Space Apps Challenge 2026. This page is a deployment canary: the app is under construction.",
  "disclaimer.support":
    "This tool supports, and does not replace, the judgment of farmers and agronomists. It explores options; it does not prescribe actions or promise yields, profit or carbon credits.",

  // Units (ADR-7). "delta" units are temperature differences: same symbol, converted without +32.
  "unit.degC": "°C",
  "unit.delta_degC": "°C",
  "unit.degC_d": "°C·d",
  "unit.mm": "mm",
  "unit.mm/d": "mm/day",
  "unit.mm/month": "mm/month",
  "unit.m3/m3": "m³/m³",
  "unit.MJ/m2/d": "MJ/m²/day",
  "unit.m/s": "m/s",
  "unit.kPa": "kPa",
  "unit.%": "%",
  "unit.m": "m",
  "unit.ha": "ha",
  "unit.deg": "°",
  "unit.days": "days",
  "unit.count": "",
  "unit.probability": "",
  "unit.1": "",
  "unit.degF": "°F",
  "unit.delta_degF": "°F",
  "unit.degF_d": "°F·d",
  "unit.in": "in",
  "unit.in/d": "in/day",
  "unit.in/month": "in/month",
  "unit.ft": "ft",
  "unit.ac": "ac",
  "unit.mph": "mph",

  // Unit selector (FR23)
  "units.selector.label": "Units",
  "units.system.metric": "Metric",
  "units.system.imperial": "Imperial",

  // Values and provenance (FR19, ADR-8)
  "value.unavailable": "Not available",
  "provenance.open": "{value} {unit}. Show data source",
  "provenance.panel.title": "Data source",
  "provenance.panel.description": "Where this number comes from and how it was produced.",
  "provenance.panel.close": "Close",
  "provenance.panel.notFound": "No provenance record found for {id}.",
  "provenance.field.dataType": "Data type",
  "provenance.field.dataset": "Dataset and provider",
  "provenance.field.product": "Product and version",
  "provenance.field.collection": "Collection ID",
  "provenance.field.variable": "Variable and unit",
  "provenance.field.nativeUnit": "Unit in the source",
  "provenance.field.spatial": "Spatial resolution",
  "provenance.field.temporal": "Temporal resolution",
  "provenance.field.period": "Period",
  "provenance.field.aggregation": "Aggregation",
  "provenance.field.method": "Method",
  "provenance.field.inputs": "Computed from",
  "provenance.field.authoredBy": "Provided by",
  "provenance.field.refs": "References",
  "provenance.field.accessedAt": "Accessed on",
  "provenance.field.link": "Link",
  "provenance.field.doi": "DOI",
  "provenance.field.terms": "Terms of use",
  "provenance.field.license": "License",
  "provenance.field.limitations": "Limitations",
  "provenance.link.source": "Open the source",
  "provenance.link.terms": "Read the terms",
  "provenance.period.range": "{start} to {end}",
  "provenance.support.point": "point",
  "provenance.support.polygon": "field polygon",
  "provenance.support.containing_pixel": "pixel containing the field",
  "provenance.support.regional": "regional",
  "provenance.none": "None listed",

  // Data type labels (FR9)
  "dataType.satellite_observed": "Satellite-observed",
  "dataType.modeled": "Modeled",
  "dataType.computed": "Computed",
  "dataType.user_provided": "User-provided",
  "dataType.unknown": "Unknown data type",

  // Agricultural year (ADR-7, FR22): months are named; no season labels (they flip between hemispheres).
  "agyear.axis.label": "Months of the agricultural year, starting in {month}",
  "agyear.year": "Year {n}",
  "month.short.1": "Jan",
  "month.short.2": "Feb",
  "month.short.3": "Mar",
  "month.short.4": "Apr",
  "month.short.5": "May",
  "month.short.6": "Jun",
  "month.short.7": "Jul",
  "month.short.8": "Aug",
  "month.short.9": "Sep",
  "month.short.10": "Oct",
  "month.short.11": "Nov",
  "month.short.12": "Dec",
  "month.long.1": "January",
  "month.long.2": "February",
  "month.long.3": "March",
  "month.long.4": "April",
  "month.long.5": "May",
  "month.long.6": "June",
  "month.long.7": "July",
  "month.long.8": "August",
  "month.long.9": "September",
  "month.long.10": "October",
  "month.long.11": "November",
  "month.long.12": "December",

  // Soil state per month of the rotation (FR4, FR21; PRD §3 soil-state tokens). Never color alone.
  "soil.strip.label": "Soil cover month by month",
  "soil.strip.legend": "Soil state",
  "soil.state.covered": "Covered",
  "soil.state.residue": "Crop residue",
  "soil.state.transition": "In transition",
  "soil.state.bare": "Bare soil",
  "soil.cell": "{month}: {state}",
  "soil.cell.segments": "{month}: {state} ({segments})",
  // Navigation
  "nav.label": "Pages",
  "nav.home": "Home",
  "nav.dataMethods": "Data & Methods",
  "nav.glossary": "Glossary",

  // Shared content blocks
  "content.pending": "Pending",
  "content.refs": "References",
  "content.externalLink": "(opens in a new tab)",

  // Data & Methods (Story 1.4, FR17, FR18)
  "dataMethods.meta.title": "Data & Methods · FieldShift (working title)",
  "dataMethods.meta.description":
    "Datasets, methods, limitations, validation, related work and use of AI behind the project.",
  "dataMethods.heading": "Data & Methods",
  "dataMethods.intro":
    "Every dataset, method and tool behind this project, how each number is produced, what it cannot tell you, related work and how AI was used. Sections marked Pending are filled as the work ships.",
  "dataMethods.toc": "On this page",
  "dataMethods.section.data": "Data, resources and tools",
  "dataMethods.section.data.intro":
    "Generated from RESOURCES.md, the single list of datasets, licences and tools in the repository.",
  "dataMethods.section.satelliteGround": "Satellite vs. ground",
  "dataMethods.section.satelliteGround.legend": "Every number carries one of these four data-type labels:",
  "dataMethods.section.methods": "Methods",
  "dataMethods.section.methods.pending":
    "Methods for the satellite layers and for the comparison itself are added here as each one is implemented.",
  "dataMethods.section.limitations": "Limitations",
  "dataMethods.section.limitations.pending":
    "Limitations of layers that are not implemented yet are added with them.",
  "dataMethods.section.validation": "Validation",
  "dataMethods.section.validation.pending":
    "For each site, a known past event (for example a drought year) will be compared with what the NASA data recorded, and the result will be published here, including negative or inconclusive results.",
  "dataMethods.section.scale": "Scale of the problem",
  "dataMethods.section.scale.pending":
    "The figures on the scale of the problem are shown here once each one has a source record, like every other number in the app.",
  "dataMethods.section.relatedWork": "Related work",
  "dataMethods.section.useOfAi": "Use of AI",
  "dataMethods.section.useOfAi.intro":
    "AI tools were used for research, code and text, never to choose the concept, the differentiator or the name. Every AI-assisted change is logged below (generated from SI-USAGE.md).",
  "dataMethods.section.glossary": "Glossary",
  "dataMethods.section.glossary.body": "Plain-language definitions of the technical terms used on this site.",
  "dataMethods.methodFrom": "From",

  // Entry page: list of sites (T1)
  "home.sites.heading": "Sites",
  "home.sites.intro": "Climate context from NASA POWER, with the source of every number one click away.",

  // Site names, by site id. Text only: coordinates and numbers come from the site's data files.
  "site.name.cruz-alta": "Cruz Alta, RS, Brazil",

  // Site page (T2, FR2, FR19)
  "site.meta.title": "{name} · FieldShift (working title)",
  "site.meta.description": "Climate of {name} from NASA POWER, with the provenance of every number.",
  "site.eyebrow": "Site",
  "site.header.point": "Point sent to NASA POWER",
  "site.header.lat": "Latitude",
  "site.header.lon": "Longitude",
  "site.header.pointNote":
    "A point inside one NASA POWER grid cell, not a farm field.",
  "site.header.source": "Data source",
  "site.header.record": "Monthly record",
  "site.header.recordRange": "{first} to {last}",
  "site.header.accessed": "Downloaded on {date}",
  "site.header.units": "Units",
  "site.header.howTo": "Select any underlined number to see where it comes from.",

  "site.recent.heading": "Recent months: rain and temperature",
  "site.recent.intro":
    "Monthly values from the NASA POWER record for the most recent months with data. Precipitation is the monthly total; temperatures are the monthly mean of the daily maximum and minimum.",
  "site.recent.noClimatology":
    "A monthly climate normal of rain and temperature is not in this site's data files yet, so this chart shows recorded months, not a climate average.",
  "site.recent.precipChart": "Monthly precipitation, {first} to {last}",
  "site.recent.tempChart": "Monthly mean of daily maximum and minimum temperature, {first} to {last}",
  "site.recent.chartDesc":
    "The same values are listed in the table below the charts. Each value there opens its data source.",
  "site.recent.legend.precip": "Precipitation (bars)",
  "site.recent.legend.tmax": "Daily maximum (solid line, circles)",
  "site.recent.legend.tmin": "Daily minimum (dashed line, squares)",
  "site.recent.table.show": "Show the numbers as a table",
  "site.recent.table.caption": "Monthly values, {first} to {last}",
  "site.recent.table.month": "Month",
  "site.recent.table.precip": "Precipitation",
  "site.recent.table.tmax": "Daily max. temperature",
  "site.recent.table.tmin": "Daily min. temperature",

  "site.indices.heading": "Climate indices, {start}–{end}",
  "site.indices.intro":
    "Computed from NASA POWER daily values for the reference period. Thresholds are generic defaults until the agronomist sets them for this site.",
  "site.indices.method": "How the indices are computed",

  "site.profiles.heading": "Month by month, {start}–{end}",
  "site.profiles.intro": "Mean of each calendar month over the reference period.",
  "site.profiles.caption": "Climate indices by calendar month, mean {start}–{end}",
  "site.profiles.scroll": "Table of climate indices by month; scroll sideways to see every column",
  "site.profiles.month": "Month",

  "site.limits.heading": "What the ground check found",
  "site.limits.intro":
    "The team compared NASA POWER with weather stations in Cruz Alta. These notes are part of the data source of the numbers listed under each one.",
  "site.limits.appliesTo": "Applies to:",
  "site.limits.more": "Satellite and reanalysis vs. ground stations",
  "site.limits.general": "Every number on this page is a regional value of one grid cell, not a field measurement.",

  // Glossary (FR8)
  "glossary.meta.title": "Glossary · FieldShift (working title)",
  "glossary.meta.description": "Plain-language definitions of the technical terms used in the project.",
  "glossary.heading": "Glossary",
  "glossary.intro": "Technical terms used on this site, in plain language.",
  "glossary.reviewPending": "Agronomist review pending",
  "glossary.reviewedBy": "Reviewed by {name}",
} as const;

export type MessageKey = keyof typeof en;
