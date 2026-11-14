/* eslint-disable */
/**
 * GENERATED FILE. DO NOT EDIT BY HAND.
 * Source: pydantic models in services/science/src/fieldshift/contracts (ADR-4).
 * Regenerate with `npm run contracts` at the repository root.
 */

/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "Month".
 */
export type Month = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12;
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "CanonicalUnit".
 */
export type CanonicalUnit =
  | "degC"
  | "delta_degC"
  | "degC_d"
  | "mm"
  | "mm/d"
  | "mm/month"
  | "m3/m3"
  | "MJ/m2/d"
  | "m/s"
  | "kPa"
  | "%"
  | "m"
  | "ha"
  | "deg"
  | "days"
  | "count"
  | "probability"
  | "1";
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "SchemaVersion".
 */
export type SchemaVersion = string;
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "SiteId".
 */
export type SiteId = string;
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "IsoDate".
 */
export type IsoDate = string;
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "DataType".
 */
export type DataType = "satellite_observed" | "modeled" | "computed" | "user_provided";
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "ProvenanceId".
 */
export type ProvenanceId = string;
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "IndexKey".
 */
export type IndexKey =
  | "heat_days"
  | "frost_days"
  | "extreme_precip_days"
  | "extreme_precip_total"
  | "extreme_precip_threshold"
  | "water_deficit"
  | "growing_degree_days"
  | "et0";
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "Country".
 */
export type Country = "US" | "BR";
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "SeriesId".
 */
export type SeriesId = string;
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "Hemisphere".
 */
export type Hemisphere = "N" | "S";
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "IsoDateTime".
 */
export type IsoDateTime = string;
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "IsoMonth".
 */
export type IsoMonth = string;
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "LayerId".
 */
export type LayerId =
  | "power"
  | "smap"
  | "imerg"
  | "modis_ndvi"
  | "landsat_ndvi"
  | "grace"
  | "srtm"
  | "openet"
  | "cdl"
  | "mapbiomas"
  | "satveg"
  | "ecostress";
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "LayerReasonCode".
 */
export type LayerReasonCode =
  | "AUTH_REQUIRED"
  | "SOURCE_TIMEOUT"
  | "NO_DATA_FOR_AREA"
  | "QUOTA_EXCEEDED"
  | "NOT_EXTRACTED_YET"
  | "OUT_OF_REGION"
  | "CUT_BY_FLIGHT_RULE";
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "SegmentRole".
 */
export type SegmentRole = "cash_crop" | "second_crop" | "cover_crop" | "forage_perennial" | "fallow";
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "SoilState".
 */
export type SoilState = "covered" | "residue" | "transition" | "bare";
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "VariableKey".
 */
export type VariableKey =
  | "air_temp_mean"
  | "air_temp_max"
  | "air_temp_min"
  | "dewpoint"
  | "rel_humidity"
  | "precip"
  | "wind_2m"
  | "solar_rad"
  | "surface_pressure"
  | "soil_wetness_top_modeled"
  | "soil_wetness_root_modeled"
  | "soil_wetness_profile_modeled"
  | "evap_land_modeled"
  | "et0"
  | "heat_days"
  | "frost_days"
  | "extreme_precip_days"
  | "extreme_precip_total"
  | "water_deficit"
  | "growing_degree_days"
  | "soil_moisture_surface"
  | "soil_moisture_rootzone"
  | "precip_satellite"
  | "ndvi"
  | "evi"
  | "tws_anomaly"
  | "et_actual"
  | "elevation"
  | "slope"
  | "land_cover_class";
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "UnitSystem".
 */
export type UnitSystem = "metric" | "imperial";

/**
 * FieldShift data contracts v1.1.0. Generated from the pydantic models in services/science/src/fieldshift/contracts by `fieldshift contracts export`. Do not edit by hand.
 */
export interface FieldShiftContracts {
  [k: string]: unknown;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "AgYear".
 */
export interface AgYear {
  start_month: Month;
  label: "single" | "split";
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "ClimateIndices".
 */
export interface ClimateIndices {
  schema_version: SchemaVersion;
  site_id: SiteId;
  metrics: Metric[];
  profiles: MonthlyProfile[];
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "Metric".
 */
export interface Metric {
  id: string;
  label: LocalizedText;
  value: number;
  unit: CanonicalUnit;
  period: Period;
  data_type: DataType;
  provenance_id: ProvenanceId;
  comparison?: MetricComparison | null;
  confidence?: Confidence | null;
  tags?: string[];
  index_key?: IndexKey | null;
}
/**
 * NFR15: Portuguese can be added without refactoring.
 *
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "LocalizedText".
 */
export interface LocalizedText {
  en: string;
  pt?: string | null;
}
/**
 * Inclusive period.
 *
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "Period".
 */
export interface Period {
  start: IsoDate;
  end: IsoDate;
}
/**
 * 'Before vs. now' (⏸ D5 decides which periods are shown).
 *
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "MetricComparison".
 */
export interface MetricComparison {
  baseline_value: number;
  baseline_period: Period;
  delta: number;
  delta_unit: CanonicalUnit;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "Confidence".
 */
export interface Confidence {
  level: "high" | "medium" | "low";
  reason: LocalizedText;
  independent_sources: number;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "MonthlyProfile".
 */
export interface MonthlyProfile {
  id: string;
  label: LocalizedText;
  unit: CanonicalUnit;
  /**
   * @minItems 12
   * @maxItems 12
   */
  values: [
    number | null,
    number | null,
    number | null,
    number | null,
    number | null,
    number | null,
    number | null,
    number | null,
    number | null,
    number | null,
    number | null,
    number | null
  ];
  period: Period;
  data_type: DataType;
  provenance_id: ProvenanceId;
  index_key?: IndexKey | null;
}
/**
 * ⏸ keys and computation depend on D6, D7, D18, D19.
 *
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "CriterionValue".
 */
export interface CriterionValue {
  value: number;
  unit: CanonicalUnit;
  better: "higher" | "lower";
  provenance_id: ProvenanceId;
  confidence: Confidence;
}
/**
 * VL3: every evidence item has a number, a dataset and a period.
 *
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "Evidence".
 */
export interface Evidence {
  id: string;
  statement: LocalizedText;
  value: number;
  unit: CanonicalUnit;
  period: Period;
  dataset_label: string;
  series_ids: SeriesId[];
  /**
   * @minItems 1
   */
  provenance_ids: [ProvenanceId, ...ProvenanceId[]];
  data_type: DataType;
  confidence: Confidence;
}
/**
 * WGS84, RFC 7946: positions are [lon, lat]; every ring is closed (last = first).
 *
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "GeoJSONPolygon".
 */
export interface GeoJSONPolygon {
  type: "Polygon";
  /**
   * @minItems 1
   */
  coordinates: [number[][], ...number[][][]];
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "GeoPoint".
 */
export interface GeoPoint {
  lat: number;
  lon: number;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "KnownGap".
 */
export interface KnownGap {
  start: IsoMonth;
  end: IsoMonth;
  reason: LocalizedText;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "LayerReason".
 */
export interface LayerReason {
  code: LayerReasonCode;
  message: LocalizedText;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "LayerStatus".
 */
export interface LayerStatus {
  id: LayerId;
  status: "available" | "partial" | "unavailable" | "not_applicable";
  reason?: LayerReason | null;
  series_ids: SeriesId[];
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "ManifestFile".
 */
export interface ManifestFile {
  path: string;
  contract: string;
  sha256: string;
  required: boolean;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "PipelineInfo".
 */
export interface PipelineInfo {
  git_sha: string;
  command: string;
  package_version: string;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "Provenance".
 */
export interface Provenance {
  id: ProvenanceId;
  data_type: DataType;
  title: LocalizedText;
  source?: ProvenanceSource | null;
  variable: ProvenanceVariable;
  spatial: ProvenanceSpatial;
  temporal: ProvenanceTemporal;
  aggregation: LocalizedText;
  method?: ProvenanceMethod | null;
  inputs?: ProvenanceId[];
  authored_by?: string | null;
  refs?: Ref[];
  access?: ProvenanceAccess | null;
  limitations: LocalizedText[];
}
/**
 * Required for satellite_observed and modeled.
 *
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "ProvenanceSource".
 */
export interface ProvenanceSource {
  dataset: string;
  provider: string;
  product: string;
  version: string;
  collection_id?: string | null;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "ProvenanceVariable".
 */
export interface ProvenanceVariable {
  code: string;
  name: LocalizedText;
  unit: CanonicalUnit;
  native_unit?: string | null;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "ProvenanceSpatial".
 */
export interface ProvenanceSpatial {
  resolution: string;
  resolution_m?: number | null;
  support: "point" | "polygon" | "containing_pixel" | "regional";
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "ProvenanceTemporal".
 */
export interface ProvenanceTemporal {
  resolution: "daily" | "3-hourly" | "16-day" | "monthly" | "annual" | "static";
  period: Period;
}
/**
 * Required for computed; `doc_anchor` points to content/methods (VL1).
 *
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "ProvenanceMethod".
 */
export interface ProvenanceMethod {
  name: string;
  ref: Ref;
  doc_anchor: string;
  parameters?: {
    [k: string]: number | string;
  } | null;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "Ref".
 */
export interface Ref {
  label: string;
  url?: string | null;
  doi?: string | null;
  citation?: string | null;
}
/**
 * Required for satellite_observed and modeled.
 *
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "ProvenanceAccess".
 */
export interface ProvenanceAccess {
  url: string;
  doi?: string | null;
  accessed_at: IsoDateTime;
  terms_url: string;
  license?: string | null;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "ProvenanceRegistry".
 */
export interface ProvenanceRegistry {
  schema_version: SchemaVersion;
  site_id: SiteId | "global";
  records: {
    [k: string]: Provenance;
  };
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "ProvenancedValue".
 */
export interface ProvenancedValue {
  value: number;
  provenance_id: ProvenanceId;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "RetrospectiveCheck".
 */
export interface RetrospectiveCheck {
  id: string;
  site_id: SiteId;
  event: RetrospectiveEvent;
  observed: Evidence[];
  result: "confirms" | "does_not_confirm" | "inconclusive";
  discussion: LocalizedText;
  limitations: LocalizedText[];
  checked_by: string;
}
/**
 * Event chosen by the agronomist (Q12).
 *
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "RetrospectiveEvent".
 */
export interface RetrospectiveEvent {
  name: LocalizedText;
  period: Period;
  source: Ref;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "Rotation".
 */
export interface Rotation {
  id: string;
  site_id: SiteId;
  name: LocalizedText;
  kind: "current" | "alternative";
  cycle_years: number;
  /**
   * @minItems 1
   */
  segments: [RotationSegment, ...RotationSegment[]];
  data_type: "user_provided" | "computed";
  provenance_id: ProvenanceId;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "RotationSegment".
 */
export interface RotationSegment {
  id: string;
  label: LocalizedText;
  role: SegmentRole;
  crop_id: string | null;
  start: RotationMonthRef;
  end: RotationMonthRef;
  soil: SegmentSoil;
  irrigated: boolean;
  refs: Ref[];
}
/**
 * Position inside the cycle: cycle year (relative to the agricultural year) + CIVIL month.
 *
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "RotationMonthRef".
 */
export interface RotationMonthRef {
  year_index: number;
  month: Month;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "SegmentSoil".
 */
export interface SegmentSoil {
  main: "covered" | "residue" | "bare";
  establishment_months: number;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "RotationFile".
 */
export interface RotationFile {
  schema_version: SchemaVersion;
  site_id: SiteId;
  rotation: Rotation;
  timeline: RotationTimeline;
}
/**
 * Derived by the pipeline (data_type 'computed').
 *
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "RotationTimeline".
 */
export interface RotationTimeline {
  rotation_id: string;
  months: SoilCoverMonth[];
  bare_months_per_year: Metric;
  provenance_id: ProvenanceId;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "SoilCoverMonth".
 */
export interface SoilCoverMonth {
  position: number;
  year_index: number;
  month: Month;
  state: SoilState;
  segment_ids: string[];
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "SeriesAggregation".
 */
export interface SeriesAggregation {
  temporal: "mean" | "sum" | "min" | "max" | "count" | "p95" | "composite" | "none";
  spatial: "point" | "containing_pixel" | "polygon_mean" | "polygon_median";
}
/**
 * Climatology used for anomalies (ADR-3).
 *
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "SeriesBaseline".
 */
export interface SeriesBaseline {
  period: Period;
  /**
   * @minItems 12
   * @maxItems 12
   */
  monthly_mean: [
    number | null,
    number | null,
    number | null,
    number | null,
    number | null,
    number | null,
    number | null,
    number | null,
    number | null,
    number | null,
    number | null,
    number | null
  ];
  provenance_id: ProvenanceId;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "SeriesBundle".
 */
export interface SeriesBundle {
  schema_version: SchemaVersion;
  site_id: SiteId;
  series: TimeSeries[];
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "TimeSeries".
 */
export interface TimeSeries {
  id: SeriesId;
  site_id: SiteId;
  variable_key: VariableKey;
  label: LocalizedText;
  unit: CanonicalUnit;
  frequency: "daily" | "monthly" | "annual" | "static";
  aggregation: SeriesAggregation;
  data_type: DataType;
  provenance_id: ProvenanceId;
  points: SeriesPoint[];
  coverage: SeriesCoverage;
  baseline?: SeriesBaseline | null;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "SeriesPoint".
 */
export interface SeriesPoint {
  t: IsoMonth | IsoDate;
  v: number | null;
  q?: ("ok" | "gap" | "partial" | "estimated") | null;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "SeriesCoverage".
 */
export interface SeriesCoverage {
  first: IsoMonth | IsoDate;
  last: IsoMonth | IsoDate;
  valid_pct: number;
  known_gaps: KnownGap[];
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "Site".
 */
export interface Site {
  schema_version: SchemaVersion;
  id: SiteId;
  name: LocalizedText;
  country: Country;
  hemisphere: Hemisphere;
  timezone: string;
  point: GeoPoint;
  field: GeoJSONPolygon;
  area_ha: ProvenancedValue;
  elevation_m: ProvenancedValue;
  ag_year: AgYear;
  default_units: UnitSystem;
  context: SiteContext;
  validated_by: Validation | null;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "SiteContext".
 */
export interface SiteContext {
  region: LocalizedText;
  summary: LocalizedText;
  refs: Ref[];
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "Validation".
 */
export interface Validation {
  name: string;
  at: IsoDateTime;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "SiteManifest".
 */
export interface SiteManifest {
  schema_version: SchemaVersion;
  site_id: SiteId;
  generated_at: IsoDateTime;
  pipeline: PipelineInfo;
  contracts: {
    [k: string]: SchemaVersion;
  };
  files: ManifestFile[];
  layers: LayerStatus[];
}
/**
 * data/sites/index.json (landing page, T1).
 *
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "SitesIndex".
 */
export interface SitesIndex {
  schema_version: SchemaVersion;
  sites: SitesIndexEntry[];
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "SitesIndexEntry".
 */
export interface SitesIndexEntry {
  id: SiteId;
  name: LocalizedText;
  country: Country;
  hemisphere: Hemisphere;
  default_units: UnitSystem;
  summary: LocalizedText;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "Strategy".
 */
export interface Strategy {
  id: string;
  site_id: SiteId;
  is_current: boolean;
  name: LocalizedText;
  rotation_id: string;
  blocks: StrategyBlocks;
  confidence: Confidence;
  criteria: {
    [k: string]: CriterionValue;
  };
  requirements: StrategyRequirements;
  generator: StrategyGenerator;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "StrategyBlocks".
 */
export interface StrategyBlocks {
  /**
   * @minItems 1
   */
  why: [TextItem, ...TextItem[]];
  /**
   * @minItems 1
   */
  evidence: [Evidence, ...Evidence[]];
  /**
   * @minItems 1
   */
  benefits: [TextItem, ...TextItem[]];
  /**
   * @minItems 1
   */
  gaps: [TextItem, ...TextItem[]];
  /**
   * @minItems 1
   */
  local_review: [TextItem, ...TextItem[]];
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "TextItem".
 */
export interface TextItem {
  text: LocalizedText;
  provenance_ids?: ProvenanceId[];
}
/**
 * ⏸ extension (FR16): basis of the constraint filters.
 *
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "StrategyRequirements".
 */
export interface StrategyRequirements {
  irrigation: boolean;
  livestock: boolean;
  equipment: string[];
}
/**
 * ⏸ D8.
 *
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "StrategyGenerator".
 */
export interface StrategyGenerator {
  method_id: string;
  version: string;
  provenance_id: ProvenanceId;
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "StrategySet".
 */
export interface StrategySet {
  schema_version: SchemaVersion;
  site_id: SiteId;
  rotations: Rotation[];
  timelines: RotationTimeline[];
  /**
   * @minItems 3
   */
  strategies: [Strategy, Strategy, Strategy, ...Strategy[]];
}
/**
 * This interface was referenced by `FieldShiftContracts`'s JSON-Schema
 * via the `definition` "ValidationFile".
 */
export interface ValidationFile {
  schema_version: SchemaVersion;
  site_id: SiteId;
  checks: RetrospectiveCheck[];
}
