import sqlite3
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("maji-ndogo-water")
DB_PATH = "maji_ndogo.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@mcp.tool()
def get_province_statistics(province_name: str) -> dict:
    """
    Get water source statistics for one Maji Ndogo province.

    Args:
        province_name: One of Kilimani, Akatsi, Sokoto, Amanzi, Hawassa.

    Returns:
        A dictionary with total sources, total people served, and a
        breakdown by water source type (well, tap_in_home,
        tap_in_home_broken, shared_tap, river).
    """
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT ws.type_of_water_source AS source_type,
               COUNT(*) AS source_count,
               SUM(ws.number_of_people_served) AS people_served
        FROM water_source ws
        WHERE ws.source_id IN (
            SELECT DISTINCT v.source_id
            FROM visits v
            JOIN location l ON v.location_id = l.location_id
            WHERE l.province_name = ?
        )
        GROUP BY ws.type_of_water_source
        ORDER BY source_count DESC
    """
    rows = cur.execute(query, (province_name,)).fetchall()
    conn.close()

    if not rows:
        return {"province": province_name, "error": "No data found for this province name."}

    breakdown = [dict(row) for row in rows]
    total_sources = sum(r["source_count"] for r in breakdown)
    total_people = sum(r["people_served"] or 0 for r in breakdown)

    return {
        "province": province_name,
        "total_sources": total_sources,
        "total_people_served": total_people,
        "breakdown_by_type": breakdown,
    }


@mcp.tool()
def get_water_source_details(source_id: str) -> dict:
    """
    Get full details for one specific water source, including its
    location and (if it's a well) pollution test results.

    Args:
        source_id: The exact source_id, e.g. 'AkHa00001'.

    Returns:
        A dictionary with source type, people served, location info,
        and pollution details if applicable.
    """
    conn = get_connection()
    cur = conn.cursor()

    source = cur.execute(
        "SELECT source_id, type_of_water_source, number_of_people_served "
        "FROM water_source WHERE source_id = ?",
        (source_id,),
    ).fetchone()

    if not source:
        conn.close()
        return {"error": f"No water source found with id '{source_id}'."}

    result = dict(source)

    location = cur.execute(
        """
        SELECT l.province_name, l.town_name, l.address, l.location_type
        FROM visits v
        JOIN location l ON v.location_id = l.location_id
        WHERE v.source_id = ?
        LIMIT 1
        """,
        (source_id,),
    ).fetchone()
    if location:
        result["location"] = dict(location)

    pollution = cur.execute(
        "SELECT date, description, pollutant_ppm, biological, results "
        "FROM well_pollution WHERE source_id = ?",
        (source_id,),
    ).fetchone()
    if pollution:
        result["pollution"] = dict(pollution)

    conn.close()
    return result


@mcp.tool()
def compare_provinces(province_a: str, province_b: str) -> dict:
    """
    Compare water source statistics between two Maji Ndogo provinces.

    Args:
        province_a: First province name (e.g. Kilimani).
        province_b: Second province name (e.g. Akatsi).

    Returns:
        A dictionary with each province's totals and a broken-water
        percentage, so they can be compared directly.
    """
    conn = get_connection()
    cur = conn.cursor()

    def province_summary(province_name: str) -> dict:
        query = """
            SELECT ws.type_of_water_source AS source_type,
                   COUNT(*) AS source_count,
                   SUM(ws.number_of_people_served) AS people_served
            FROM water_source ws
            WHERE ws.source_id IN (
                SELECT DISTINCT v.source_id
                FROM visits v
                JOIN location l ON v.location_id = l.location_id
                WHERE l.province_name = ?
            )
            GROUP BY ws.type_of_water_source
        """
        rows = cur.execute(query, (province_name,)).fetchall()
        breakdown = {r["source_type"]: r["source_count"] for r in rows}
        total_sources = sum(breakdown.values())
        broken = breakdown.get("tap_in_home_broken", 0)
        broken_pct = round((broken / total_sources) * 100, 1) if total_sources else 0

        return {
            "province": province_name,
            "total_sources": total_sources,
            "total_people_served": sum(r["people_served"] or 0 for r in rows),
            "breakdown_by_type": breakdown,
            "broken_tap_percentage": broken_pct,
        }

    result_a = province_summary(province_a)
    result_b = province_summary(province_b)
    conn.close()

    return {province_a: result_a, province_b: result_b}


@mcp.tool()
def get_problem_areas(limit: int = 10) -> dict:
    """
    Find the towns with the most people affected by broken taps or
    contaminated wells, ranked worst first.

    Args:
        limit: How many towns to return (default 10).

    Returns:
        A dictionary with a ranked list of towns, each showing the
        number of people affected by broken taps, contaminated wells,
        and the combined total.
    """
    conn = get_connection()
    cur = conn.cursor()

    query = """
        WITH source_location AS (
            SELECT DISTINCT ws.source_id, ws.type_of_water_source,
                   ws.number_of_people_served, l.province_name, l.town_name
            FROM water_source ws
            JOIN visits v ON v.source_id = ws.source_id
            JOIN location l ON v.location_id = l.location_id
        )
        SELECT sl.province_name,
               sl.town_name,
               SUM(CASE WHEN sl.type_of_water_source = 'tap_in_home_broken'
                        THEN sl.number_of_people_served ELSE 0 END) AS broken_tap_people,
               SUM(CASE WHEN wp.results IN ('Contaminated: Chemical', 'Contaminated: Biological')
                        THEN sl.number_of_people_served ELSE 0 END) AS contaminated_well_people
        FROM source_location sl
        LEFT JOIN well_pollution wp ON wp.source_id = sl.source_id
        GROUP BY sl.province_name, sl.town_name
        ORDER BY (broken_tap_people + contaminated_well_people) DESC
        LIMIT ?
    """
    rows = cur.execute(query, (limit,)).fetchall()
    conn.close()

    towns = []
    for r in rows:
        broken = r["broken_tap_people"] or 0
        contaminated = r["contaminated_well_people"] or 0
        towns.append({
            "province": r["province_name"],
            "town": r["town_name"],
            "broken_tap_people": broken,
            "contaminated_well_people": contaminated,
            "total_affected": broken + contaminated,
        })

    return {"top_problem_towns": towns}


@mcp.tool()
def search_water_data(
    province_name: str = None,
    town_name: str = None,
    source_type: str = None,
    limit: int = 20,
) -> dict:
    """
    Search water sources by any combination of province, town, and
    source type. All filters are optional — omit any you don't need.

    Args:
        province_name: Filter by province (e.g. Kilimani). Optional.
        town_name: Filter by town (e.g. Harare). Optional.
        source_type: One of well, tap_in_home, tap_in_home_broken,
            shared_tap, river. Optional.
        limit: Max results to return (default 20).

    Returns:
        A dictionary with the matching sources and how many were found.
    """
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT DISTINCT ws.source_id, ws.type_of_water_source,
               ws.number_of_people_served, l.province_name, l.town_name
        FROM water_source ws
        JOIN visits v ON v.source_id = ws.source_id
        JOIN location l ON v.location_id = l.location_id
        WHERE 1=1
    """
    params = []

    if province_name:
        query += " AND l.province_name = ?"
        params.append(province_name)
    if town_name:
        query += " AND l.town_name = ?"
        params.append(town_name)
    if source_type:
        query += " AND ws.type_of_water_source = ?"
        params.append(source_type)

    query += " LIMIT ?"
    params.append(limit)

    rows = cur.execute(query, params).fetchall()
    conn.close()

    return {
        "count": len(rows),
        "results": [dict(r) for r in rows],
    }


@mcp.tool()
def analyze_water_access(province_name: str = None) -> dict:
    """
    Summarize water access levels: what percentage of the surveyed
    population is served by each source type, nationwide or for one
    province.

    Args:
        province_name: Limit to one province. Omit for all of Maji Ndogo.

    Returns:
        A dictionary with total people covered and a percentage
        breakdown by source type.
    """
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT DISTINCT ws.source_id, ws.type_of_water_source,
               ws.number_of_people_served, l.province_name
        FROM water_source ws
        JOIN visits v ON v.source_id = ws.source_id
        JOIN location l ON v.location_id = l.location_id
    """
    params = []
    if province_name:
        query += " WHERE l.province_name = ?"
        params.append(province_name)

    rows = cur.execute(query, params).fetchall()
    conn.close()

    totals = {}
    for r in rows:
        t = r["type_of_water_source"]
        totals[t] = totals.get(t, 0) + (r["number_of_people_served"] or 0)

    grand_total = sum(totals.values())
    if grand_total == 0:
        return {"scope": province_name or "all of Maji Ndogo", "error": "No data found."}

    breakdown_pct = {
        t: round((count / grand_total) * 100, 1) for t, count in totals.items()
    }

    return {
        "scope": province_name or "all of Maji Ndogo",
        "total_people_covered": grand_total,
        "people_by_type": totals,
        "percentage_by_type": breakdown_pct,
    }


if __name__ == "__main__":
    mcp.run()