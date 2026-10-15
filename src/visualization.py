"""
DashRoute Visualization Module
Generates Plotly interactive chart definitions for the frontend.
Optimized for high-contrast dark theme, perfect alignment, responsive sizing,
and elimination of text overlaps and clipped labels.
"""
from typing import Dict, Any, List, Optional

try:
    from .sqlite_layer import (
        get_traffic_breakdown,
        get_weather_breakdown,
        get_traffic_weather_matrix,
        get_distance_buckets,
        get_vehicle_performance,
        get_city_performance
    )
except ImportError:
    from sqlite_layer import (
        get_traffic_breakdown,
        get_weather_breakdown,
        get_traffic_weather_matrix,
        get_distance_buckets,
        get_vehicle_performance,
        get_city_performance
    )

# Master dark theme layout tokens
DARK_BASE_LAYOUT = {
    "paper_bgcolor": "rgba(0, 0, 0, 0)",
    "plot_bgcolor": "rgba(15, 23, 42, 0.4)",
    "font": {
        "color": "#cbd5e1",
        "family": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        "size": 12
    },
    "autosize": True,
    "hoverlabel": {
        "bgcolor": "#1e293b",
        "bordercolor": "rgba(255, 255, 255, 0.15)",
        "font": {"color": "#ffffff", "family": "'Inter', sans-serif", "size": 12}
    }
}

TRAFFIC_LOGICAL_ORDER = ["Low", "Medium", "High", "Jam"]
WEATHER_LOGICAL_ORDER = ["Sunny", "Stormy", "Sandstorms", "Windy", "Cloudy", "Fog"]

def create_traffic_chart() -> Dict[str, Any]:
    """
    Traffic density vs Average Delivery Time and Slow Order %
    - Ordered logically: Low -> Medium -> High -> Jam
    - Left axis: Delivery Time (min) with clean bar labels
    - Right axis: % Classified Slow with red line and clear bounds
    - Separate axis titles and automargins to prevent clipping
    """
    data = get_traffic_breakdown()
    data_dict = {d["road_traffic_density"]: d for d in data}
    
    # Sort logically
    ordered_items = [data_dict[t] for t in TRAFFIC_LOGICAL_ORDER if t in data_dict]
    # Add any remaining categories
    for d in data:
        if d["road_traffic_density"] not in TRAFFIC_LOGICAL_ORDER:
            ordered_items.append(d)

    categories = [d["road_traffic_density"] for d in ordered_items]
    avg_times = [d["avg_time_min"] for d in ordered_items]
    slow_pcts = [d["pct_slow"] for d in ordered_items]
    order_counts = [d["order_count"] for d in ordered_items]

    fig_dict = {
        "data": [
            {
                "x": categories,
                "y": avg_times,
                "name": "Avg Delivery Time",
                "type": "bar",
                "marker": {
                    "color": "#6366f1",
                    "line": {"color": "rgba(99, 102, 241, 0.4)", "width": 1}
                },
                "text": [f"{v:.1f}m" for v in avg_times],
                "textposition": "inside",
                "insidetextanchor": "middle",
                "textfont": {"color": "#ffffff", "size": 12, "weight": 600},
                "customdata": order_counts,
                "hovertemplate": "<b>Traffic: %{x}</b><br>Avg Duration: %{y:.1f} mins<br>Total Orders: %{customdata:,}<extra></extra>"
            },
            {
                "x": categories,
                "y": slow_pcts,
                "name": "% Slow Deliveries",
                "type": "scatter",
                "mode": "lines+markers",
                "yaxis": "y2",
                "line": {"color": "#ef4444", "width": 3},
                "marker": {"size": 8, "color": "#ef4444", "symbol": "circle"},
                "hovertemplate": "<b>Traffic: %{x}</b><br>Slow Delivery Rate: %{y:.1f}%<extra></extra>"
            }
        ],
        "layout": {
            **DARK_BASE_LAYOUT,
            "margin": {"l": 55, "r": 55, "t": 20, "b": 45},
            "xaxis": {
                "title": {"text": "Road Traffic Density", "font": {"size": 12, "color": "#94a3b8"}, "standoff": 10},
                "gridcolor": "rgba(255, 255, 255, 0.06)",
                "zeroline": False,
                "automargin": True
            },
            "yaxis": {
                "title": {"text": "Avg Duration (min)", "font": {"size": 12, "color": "#94a3b8"}},
                "gridcolor": "rgba(255, 255, 255, 0.06)",
                "zerolinecolor": "rgba(255, 255, 255, 0.1)",
                "automargin": True,
                "range": [0, max(avg_times) * 1.25]
            },
            "yaxis2": {
                "title": {"text": "% Slow Speed Rate", "font": {"size": 12, "color": "#f87171"}},
                "overlaying": "y",
                "side": "right",
                "range": [0, 100],
                "showgrid": False,
                "automargin": True,
                "tickfont": {"color": "#f87171"}
            },
            "legend": {
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1.0,
                "font": {"size": 11, "color": "#cbd5e1"},
                "bgcolor": "rgba(0,0,0,0)"
            }
        }
    }
    return fig_dict


def create_weather_chart() -> Dict[str, Any]:
    """
    Weather condition delivery time and order distribution.
    - Sorted logically by duration
    - Compact, non-overlapping data labels inside bars
    - Order counts moved to rich hover tooltip
    """
    data = get_weather_breakdown()
    # Sort by avg_time_min ascending (fastest to slowest)
    data = sorted(data, key=lambda x: x["avg_time_min"])

    conditions = [d["weather_conditions"] for d in data]
    avg_times = [d["avg_time_min"] for d in data]
    order_counts = [d["order_count"] for d in data]
    slow_pcts = [d["pct_slow"] for d in data]

    # Color palette graduating from green to coral/rose
    colors = ["#10b981", "#06b6d4", "#3b82f6", "#8b5cf6", "#f59e0b", "#ef4444"]
    bar_colors = colors[:len(conditions)]

    fig_dict = {
        "data": [
            {
                "x": conditions,
                "y": avg_times,
                "type": "bar",
                "marker": {
                    "color": bar_colors,
                    "line": {"color": "rgba(255, 255, 255, 0.1)", "width": 1}
                },
                "text": [f"{t:.1f}m" for t in avg_times],
                "textposition": "inside",
                "insidetextanchor": "middle",
                "textfont": {"color": "#ffffff", "size": 12, "weight": 600},
                "customdata": list(zip(order_counts, slow_pcts)),
                "hovertemplate": "<b>Weather: %{x}</b><br>Avg Duration: %{y:.1f} mins<br>Total Orders: %{customdata[0]:,}<br>Slow Rate: %{customdata[1]:.1f}%<extra></extra>"
            }
        ],
        "layout": {
            **DARK_BASE_LAYOUT,
            "margin": {"l": 55, "r": 20, "t": 20, "b": 45},
            "xaxis": {
                "title": {"text": "Weather Conditions", "font": {"size": 12, "color": "#94a3b8"}, "standoff": 10},
                "gridcolor": "rgba(255, 255, 255, 0.06)",
                "zeroline": False,
                "automargin": True
            },
            "yaxis": {
                "title": {"text": "Avg Duration (min)", "font": {"size": 12, "color": "#94a3b8"}},
                "gridcolor": "rgba(255, 255, 255, 0.06)",
                "zerolinecolor": "rgba(255, 255, 255, 0.1)",
                "automargin": True,
                "range": [0, max(avg_times) * 1.25]
            },
            "showlegend": False
        }
    }
    return fig_dict


def create_traffic_weather_heatmap() -> Dict[str, Any]:
    """
    Heatmap matrix cross-tabulating Traffic Density and Weather Conditions.
    - Reduced vertical height for proportional alignment
    - Left margin enlarged (l: 80) to prevent y-axis category clipping
    - Logical ordering on Y axis: Low (bottom) -> Jam (top)
    - Cell values displayed directly inside each cell
    - Missing combinations are marked None (null) and shown as N/A, never fabricated 0
    - Colorbar kept strictly within visualization bounds
    """
    raw = get_traffic_weather_matrix()

    # Determine unique categories with logical ordering
    all_traffics = list(set(r["road_traffic_density"] for r in raw))
    ordered_traffics = [t for t in ["Low", "Medium", "High", "Jam"] if t in all_traffics]
    for t in all_traffics:
        if t not in ordered_traffics:
            ordered_traffics.append(t)

    all_weathers = list(set(r["weather_conditions"] for r in raw))
    ordered_weathers = [w for w in WEATHER_LOGICAL_ORDER if w in all_weathers]
    for w in all_weathers:
        if w not in ordered_weathers:
            ordered_weathers.append(w)

    lookup_time = {(r["road_traffic_density"], r["weather_conditions"]): r["avg_time_min"] for r in raw}
    lookup_count = {(r["road_traffic_density"], r["weather_conditions"]): r["order_count"] for r in raw}

    z_matrix = []
    text_matrix = []
    custom_matrix = []

    for t in ordered_traffics:
        z_row = []
        text_row = []
        custom_row = []
        for w in ordered_weathers:
            val = lookup_time.get((t, w))
            cnt = lookup_count.get((t, w), 0)
            if val is not None:
                z_row.append(val)
                text_row.append(f"{val:.1f}m")
                custom_row.append(cnt)
            else:
                z_row.append(None)
                text_row.append("N/A")
                custom_row.append(0)
        z_matrix.append(z_row)
        text_matrix.append(text_row)
        custom_matrix.append(custom_row)

    fig_dict = {
        "data": [
            {
                "z": z_matrix,
                "x": ordered_weathers,
                "y": ordered_traffics,
                "text": text_matrix,
                "texttemplate": "%{text}",
                "textfont": {"color": "#ffffff", "size": 12, "weight": 600},
                "type": "heatmap",
                "colorscale": [
                    [0.0, "#065f46"],
                    [0.35, "#0284c7"],
                    [0.65, "#d97706"],
                    [1.0, "#dc2626"]
                ],
                "colorbar": {
                    "title": {"text": "Avg (min)", "font": {"size": 11, "color": "#cbd5e1"}},
                    "thickness": 14,
                    "len": 0.85,
                    "tickfont": {"size": 10, "color": "#cbd5e1"},
                    "outlinewidth": 0,
                    "x": 1.02
                },
                "hoverongaps": False,
                "customdata": custom_matrix,
                "hovertemplate": "<b>Traffic:</b> %{y}<br><b>Weather:</b> %{x}<br><b>Avg Duration:</b> %{z:.1f} mins<br><b>Orders:</b> %{customdata:,}<extra></extra>"
            }
        ],
        "layout": {
            **DARK_BASE_LAYOUT,
            "margin": {"l": 75, "r": 65, "t": 20, "b": 45},
            "xaxis": {
                "title": {"text": "Weather Conditions", "font": {"size": 12, "color": "#94a3b8"}, "standoff": 10},
                "automargin": True,
                "side": "bottom"
            },
            "yaxis": {
                "title": {"text": "Traffic Density", "font": {"size": 12, "color": "#94a3b8"}},
                "automargin": True,
                "autorange": True
            }
        }
    }
    return fig_dict


def create_distance_tiers_chart() -> Dict[str, Any]:
    """
    Distance tiers vs delivery time & slow order share.
    - Automargins on axes to prevent title overlap
    - Clean horizontal legend at top
    """
    data = get_distance_buckets()
    tiers = [d["distance_tier"] for d in data]
    times = [d["avg_time_min"] for d in data]
    slows = [d["pct_slow"] for d in data]
    counts = [d["order_count"] for d in data]

    fig_dict = {
        "data": [
            {
                "x": tiers,
                "y": times,
                "name": "Avg Duration (min)",
                "type": "bar",
                "marker": {"color": "#0ea5e9", "line": {"color": "rgba(14, 165, 233, 0.4)", "width": 1}},
                "text": [f"{t:.1f}m" for t in times],
                "textposition": "inside",
                "textfont": {"color": "#ffffff", "size": 11, "weight": 600},
                "customdata": counts,
                "hovertemplate": "<b>%{x}</b><br>Avg Duration: %{y:.1f} mins<br>Orders: %{customdata:,}<extra></extra>"
            },
            {
                "x": tiers,
                "y": slows,
                "name": "% Slow Orders",
                "type": "bar",
                "marker": {"color": "#f43f5e", "line": {"color": "rgba(244, 63, 94, 0.4)", "width": 1}},
                "text": [f"{s:.1f}%" for s in slows],
                "textposition": "inside",
                "textfont": {"color": "#ffffff", "size": 11, "weight": 600},
                "hovertemplate": "<b>%{x}</b><br>Slow Rate: %{y:.1f}%<extra></extra>"
            }
        ],
        "layout": {
            **DARK_BASE_LAYOUT,
            "barmode": "group",
            "bargap": 0.25,
            "bargroupgap": 0.08,
            "margin": {"l": 55, "r": 20, "t": 20, "b": 45},
            "xaxis": {
                "title": {"text": "Distance Bracket", "font": {"size": 12, "color": "#94a3b8"}, "standoff": 10},
                "automargin": True
            },
            "yaxis": {
                "title": {"text": "Duration (min) / Rate (%)", "font": {"size": 12, "color": "#94a3b8"}},
                "gridcolor": "rgba(255, 255, 255, 0.06)",
                "automargin": True,
                "range": [0, max(max(times), max(slows)) * 1.25]
            },
            "legend": {
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1.0,
                "font": {"size": 11, "color": "#cbd5e1"},
                "bgcolor": "rgba(0,0,0,0)"
            }
        }
    }
    return fig_dict


def create_vehicle_efficiency_chart() -> Dict[str, Any]:
    """
    Vehicle condition and vehicle type operational comparison.
    - Condition 0 (Poor) vs Condition 1 (Fair) vs Condition 2 (Good)
    - Automargins and clean positioning
    """
    data = get_vehicle_performance()
    types = sorted(list(set(d["type_of_vehicle"] for d in data)))
    
    traces = []
    condition_colors = {0: "#ef4444", 1: "#f59e0b", 2: "#10b981"}
    condition_labels = {0: "Condition 0 (Poor)", 1: "Condition 1 (Fair)", 2: "Condition 2 (Good)"}

    for cond in [0, 1, 2]:
        y_vals = []
        text_vals = []
        for t in types:
            match = next((d for d in data if d["type_of_vehicle"] == t and d["vehicle_condition"] == cond), None)
            if match and match["avg_time_min"] is not None:
                y_vals.append(match["avg_time_min"])
                text_vals.append(f"{match['avg_time_min']:.1f}m")
            else:
                y_vals.append(None)
                text_vals.append("")
        
        traces.append({
            "x": types,
            "y": y_vals,
            "name": condition_labels.get(cond, f"Condition {cond}"),
            "type": "bar",
            "marker": {"color": condition_colors.get(cond, "#94a3b8")},
            "text": text_vals,
            "textposition": "inside",
            "textfont": {"color": "#ffffff", "size": 11, "weight": 600},
            "hovertemplate": "<b>%{x}</b> (%{data.name})<br>Avg Duration: %{y:.1f} mins<extra></extra>"
        })

    fig_dict = {
        "data": traces,
        "layout": {
            **DARK_BASE_LAYOUT,
            "barmode": "group",
            "bargap": 0.22,
            "bargroupgap": 0.06,
            "margin": {"l": 55, "r": 20, "t": 20, "b": 45},
            "xaxis": {
                "title": {"text": "Vehicle Type", "font": {"size": 12, "color": "#94a3b8"}, "standoff": 10},
                "automargin": True
            },
            "yaxis": {
                "title": {"text": "Avg Duration (min)", "font": {"size": 12, "color": "#94a3b8"}},
                "gridcolor": "rgba(255, 255, 255, 0.06)",
                "automargin": True,
                "range": [0, 42]
            },
            "legend": {
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1.0,
                "font": {"size": 11, "color": "#cbd5e1"},
                "bgcolor": "rgba(0,0,0,0)"
            }
        }
    }
    return fig_dict


def get_all_dashboard_charts() -> Dict[str, Any]:
    """Returns all chart configurations for the frontend dashboard."""
    return {
        "traffic_chart": create_traffic_chart(),
        "weather_chart": create_weather_chart(),
        "traffic_weather_heatmap": create_traffic_weather_heatmap(),
        "distance_tiers_chart": create_distance_tiers_chart(),
        "vehicle_efficiency_chart": create_vehicle_efficiency_chart()
    }
