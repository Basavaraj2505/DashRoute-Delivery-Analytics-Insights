/*
========================================================================================
DashRoute Power BI - Power Query (M) Scripts
Copy-pasteable M scripts for importing and transforming the exported analytical tables.
========================================================================================
*/

// =============================================================================
// 1. PARAMETER: SourceFolderPath
// Create a text parameter in Power BI to make source file paths portable across machines
// =============================================================================
/*
In Power BI Desktop: Home -> Manage Parameters -> New Parameter:
- Name: SourceFolderPath
- Type: Text
- Suggested Value: Any Value
- Current Value: "E:\food_distr_analysis\powerbi\data\"
*/


// =============================================================================
// 2. QUERY: fact_deliveries
// Imports the master fact table with 38,964 delivery transactions
// =============================================================================
let
    // Sourcing from local path or parameter
    SourcePath = "E:\food_distr_analysis\powerbi\data\fact_deliveries.csv",
    Source = Csv.Document(File.Contents(SourcePath), [Delimiter=",", Columns=26, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedType = Table.TransformColumnTypes(PromotedHeaders, {
        {"ID", type text},
        {"Delivery_person_ID", type text},
        {"Delivery_person_Age", type number},
        {"Delivery_person_Ratings", type number},
        {"Restaurant_latitude", type number},
        {"Restaurant_longitude", type number},
        {"Delivery_location_latitude", type number},
        {"Delivery_location_longitude", type number},
        {"Order_Date", type text},
        {"Time_Orderd", type text},
        {"Time_Order_picked", type text},
        {"Weather_conditions", type text},
        {"Road_traffic_density", type text},
        {"Vehicle_condition", Int64.Type},
        {"vehicle_condition_label", type text},
        {"Type_of_order", type text},
        {"Type_of_vehicle", type text},
        {"multiple_deliveries", type number},
        {"Festival", type text},
        {"City", type text},
        {"time_taken_min", type number},
        {"distance_km", type number},
        {"distance_tier", type text},
        {"distance_tier_order", Int64.Type},
        {"delivery_speed", type text},
        {"is_above_30min", Int64.Type}
    }),
    ReplacedBlankRatings = Table.ReplaceErrorValues(ChangedType, {{"Delivery_person_Ratings", null}}),
    ReplacedBlankAge = Table.ReplaceErrorValues(ReplacedBlankRatings, {{"Delivery_person_Age", null}})
in
    ReplacedBlankAge


// =============================================================================
// 3. QUERY: dim_traffic
// Imports traffic density dimensional lookup table (4 records)
// =============================================================================
let
    SourcePath = "E:\food_distr_analysis\powerbi\data\dim_traffic.csv",
    Source = Csv.Document(File.Contents(SourcePath), [Delimiter=",", Columns=4, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedType = Table.TransformColumnTypes(PromotedHeaders, {
        {"road_traffic_density", type text},
        {"traffic_sort_order", Int64.Type},
        {"congestion_level", type text},
        {"sla_multiplier", type number}
    })
in
    ChangedType


// =============================================================================
// 4. QUERY: dim_weather
// Imports weather conditions dimensional lookup table (6 records)
// =============================================================================
let
    SourcePath = "E:\food_distr_analysis\powerbi\data\dim_weather.csv",
    Source = Csv.Document(File.Contents(SourcePath), [Delimiter=",", Columns=4, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedType = Table.TransformColumnTypes(PromotedHeaders, {
        {"weather_conditions", type text},
        {"weather_sort_order", Int64.Type},
        {"weather_severity", type text},
        {"safety_alert", type text}
    })
in
    ChangedType


// =============================================================================
// 5. QUERY: summary_traffic_weather
// Pre-aggregated cross-impact matrix for executive root-cause reporting
// =============================================================================
let
    SourcePath = "E:\food_distr_analysis\powerbi\data\summary_traffic_weather.csv",
    Source = Csv.Document(File.Contents(SourcePath), [Delimiter=",", Columns=7, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedType = Table.TransformColumnTypes(PromotedHeaders, {
        {"road_traffic_density", type text},
        {"weather_conditions", type text},
        {"order_count", Int64.Type},
        {"avg_time_min", type number},
        {"avg_distance_km", type number},
        {"pct_slow", type number},
        {"pct_fast", type number}
    })
in
    ChangedType


// =============================================================================
// 6. QUERY: data_quality_report
// Data quality scorecard and completeness tracking table
// =============================================================================
let
    SourcePath = "E:\food_distr_analysis\powerbi\data\data_quality_report.csv",
    Source = Csv.Document(File.Contents(SourcePath), [Delimiter=",", Columns=6, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedType = Table.TransformColumnTypes(PromotedHeaders, {
        {"column_name", type text},
        {"expected_type", type text},
        {"missing_count", Int64.Type},
        {"completeness_pct", type number},
        {"status", type text},
        {"imputation_handling", type text}
    })
in
    ChangedType
