from flask import Flask, render_template, request, redirect
from datetime import datetime, timedelta
import json
import os

# ========================
# INIT APP
# ========================
app = Flask(__name__)

# ========================
# FILES
# ========================
DATA_FILE = "data.json"
GREENHOUSE_FILE = "greenhouses.json"

# ========================
# CONSTANTS
# ========================
CAPSICUM_NURSERY_DAYS = 45
CAPSICUM_TO_HARVEST_DAYS = 90
CAPSICUM_HARVEST_PERIOD_DAYS = 150

CUCUMBER_TO_HARVEST_DAYS = 45
CUCUMBER_HARVEST_PERIOD_DAYS = 120

LOCAL_CUCUMBER_TO_HARVEST_DAYS = 60
LOCAL_CUCUMBER_HARVEST_PERIOD_DAYS = 90

CS_UNIT_NAMES = {"Tharakanithi", "Meru", "Kisii"}

# ========================
# DEFAULT GREENHOUSE REGISTER
# ========================
DEFAULT_GREENHOUSES = [
    {
        "no": 1,
        "name": "Murang'a",
        "size": "8x40",
        "tank": "1000L",
        "crop": "Cucumber",
        "plants": 1000,
        "harvest": "2026-04-30",
        "end": "2026-08-30",
        "variety": "Centinela F1",
        "transplant": "2026-03-15",
        "nursery": ""
    },
    {
        "no": 2,
        "name": "Wajia",
        "size": "8x40",
        "tank": "-",
        "crop": "Capsicum",
        "plants": 1000,
        "harvest": "2026-05-14",
        "end": "2026-10-14",
        "variety": "Passarella / Ilanga",
        "transplant": "2026-02-14",
        "nursery": ""
    },
    {
        "no": 3,
        "name": "Kericho",
        "size": "8x40",
        "tank": "500L",
        "crop": "Capsicum",
        "plants": 1000,
        "harvest": "2025-07-02",
        "end": "2026-03-18",
        "variety": "Passarella / Ilanga",
        "transplant": "2025-04-18",
        "nursery": ""
    },
    {
        "no": 4,
        "name": "Homa Bay",
        "size": "16x40",
        "tank": "1000L",
        "crop": "Cucumber",
        "plants": 2000,
        "harvest": "2025-11-22",
        "end": "2026-04-26",
        "variety": "Centinela F1",
        "transplant": "2025-10-01",
        "nursery": ""
    },
    {
        "no": 5,
        "name": "Lamu",
        "size": "16x40",
        "tank": "1000L",
        "crop": "Capsicum",
        "plants": 2000,
        "harvest": "2026-02-06",
        "end": "2026-08-06",
        "variety": "Passarella / Ilanga",
        "transplant": "2025-11-15",
        "nursery": ""
    },
    {
        "no": 6,
        "name": "Tharakanithi",
        "size": "16x40",
        "tank": "1000L",
        "crop": "Asparagus",
        "plants": 1000,
        "harvest": "2026-07-07",
        "end": "2036-01-01",
        "variety": "Asparagus",
        "transplant": "2026-04-01",
        "nursery": ""
    },
    {
        "no": 7,
        "name": "Vihiga",
        "size": "16x40",
        "tank": "1000L",
        "crop": "Capsicum",
        "plants": 2000,
        "harvest": "2026-06-01",
        "end": "2026-12-02",
        "variety": "Passarella / Ilanga",
        "transplant": "2026-03-31",
        "nursery": ""
    }
]

# ========================
# YIELDS + PRICES
# ========================
yields = {
    "Cucumber_1000": 400,
    "Cucumber_2000": 700,
    "Capsicum_1000": 200,
    "Capsicum_2000": 350,
    "Asparagus": 150,
    "Local Cucumber": 600
}

prices = {
    "Cucumber": 90,
    "Capsicum": 120,
    "Asparagus": 600,
    "Local Cucumber": 90
}

# ========================
# BASIC DATE HELPERS
# ========================
def parse_date(date_string):
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except:
        return None


def to_date_string(date_obj):
    if not date_obj:
        return ""
    return date_obj.strftime("%Y-%m-%d")


def format_date_safe(date_obj, fmt="%d-%m-%Y"):
    if not date_obj:
        return "-"
    return date_obj.strftime(fmt)


def calculate_nursery_from_transplant(transplant_date):
    if not transplant_date:
        return None
    return transplant_date - timedelta(days=CAPSICUM_NURSERY_DAYS)


def calculate_transplant_from_nursery(nursery_date):
    if not nursery_date:
        return None
    return nursery_date + timedelta(days=CAPSICUM_NURSERY_DAYS)


def calculate_harvest_from_transplant(crop, transplant_date):
    if not transplant_date:
        return None

    if crop == "Capsicum":
        return transplant_date + timedelta(days=CAPSICUM_TO_HARVEST_DAYS)

    if crop == "Cucumber":
        return transplant_date + timedelta(days=CUCUMBER_TO_HARVEST_DAYS)

    if crop == "Local Cucumber":
        return transplant_date + timedelta(days=LOCAL_CUCUMBER_TO_HARVEST_DAYS)

    return None


def calculate_end_from_harvest(crop, harvest_date):
    if not harvest_date:
        return None

    if crop == "Capsicum":
        return harvest_date + timedelta(days=CAPSICUM_HARVEST_PERIOD_DAYS)

    if crop == "Cucumber":
        return harvest_date + timedelta(days=CUCUMBER_HARVEST_PERIOD_DAYS)

    if crop == "Local Cucumber":
        return harvest_date + timedelta(days=LOCAL_CUCUMBER_HARVEST_PERIOD_DAYS)

    return None

# ========================
# LOAD / SAVE HELPERS
# ========================
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def normalize_greenhouse(g):
    crop = str(g.get("crop", "")).strip()
    variety = str(g.get("variety", "")).strip()
    size = str(g.get("size", "")).strip()

    if crop == "Capsicum":
        variety = "Passarella / Ilanga"

    if crop == "Local Cucumber":
        variety = "Mydas RZ"
        size = "16x40"

    normalized = {
        "no": int(g.get("no", 0) or 0),
        "name": str(g.get("name", "")).strip(),
        "size": size,
        "tank": str(g.get("tank", "")).strip(),
        "crop": crop,
        "plants": int(g.get("plants", 0) or 0),
        "harvest": str(g.get("harvest", "")).strip(),
        "end": str(g.get("end", "")).strip(),
        "variety": variety,
        "transplant": str(g.get("transplant", "")).strip(),
        "nursery": str(g.get("nursery", "")).strip()
    }

    transplant_obj = parse_date(normalized["transplant"])
    harvest_obj = parse_date(normalized["harvest"])
    end_obj = parse_date(normalized["end"])
    nursery_obj = parse_date(normalized["nursery"])

    if crop == "Capsicum":
        if nursery_obj and not transplant_obj:
            transplant_obj = calculate_transplant_from_nursery(nursery_obj)
            normalized["transplant"] = to_date_string(transplant_obj)

        elif transplant_obj and not nursery_obj:
            nursery_obj = calculate_nursery_from_transplant(transplant_obj)
            normalized["nursery"] = to_date_string(nursery_obj)

        elif transplant_obj and nursery_obj:
            nursery_obj = calculate_nursery_from_transplant(transplant_obj)
            normalized["nursery"] = to_date_string(nursery_obj)

        if transplant_obj and not harvest_obj:
            harvest_obj = calculate_harvest_from_transplant(crop, transplant_obj)
            normalized["harvest"] = to_date_string(harvest_obj)

        if harvest_obj and not end_obj:
            end_obj = calculate_end_from_harvest(crop, harvest_obj)
            normalized["end"] = to_date_string(end_obj)

    elif crop in ["Cucumber", "Local Cucumber"]:
        normalized["nursery"] = ""

        if transplant_obj and not harvest_obj:
            harvest_obj = calculate_harvest_from_transplant(crop, transplant_obj)
            normalized["harvest"] = to_date_string(harvest_obj)

        if harvest_obj and not end_obj:
            end_obj = calculate_end_from_harvest(crop, harvest_obj)
            normalized["end"] = to_date_string(end_obj)

    else:
        normalized["nursery"] = ""

    return normalized


def load_greenhouses():
    if os.path.exists(GREENHOUSE_FILE):
        try:
            with open(GREENHOUSE_FILE, "r") as f:
                raw = json.load(f)
                clean = [normalize_greenhouse(g) for g in raw]
                return sorted(clean, key=lambda x: x["no"])
        except:
            clean = [normalize_greenhouse(g) for g in DEFAULT_GREENHOUSES]
            return sorted(clean, key=lambda x: x["no"])

    clean = [normalize_greenhouse(g) for g in DEFAULT_GREENHOUSES]
    with open(GREENHOUSE_FILE, "w") as f:
        json.dump(clean, f, indent=4)

    return sorted(clean, key=lambda x: x["no"])


def save_greenhouses(data):
    clean = [normalize_greenhouse(g) for g in data]
    clean = sorted(clean, key=lambda x: x["no"])
    with open(GREENHOUSE_FILE, "w") as f:
        json.dump(clean, f, indent=4)


actual_data = load_data()
greenhouses = load_greenhouses()

# ========================
# VENTURE HELPERS
# ========================
def get_venture_for_greenhouse_name(name):
    if name in CS_UNIT_NAMES:
        return "cs"
    return "csg"


def venture_label(venture):
    if venture == "cs":
        return "CS Units"
    if venture == "csg":
        return "CS x Griffin Units"
    return "All Units"


def filter_greenhouses_by_venture(items, venture):
    if venture == "all":
        return items
    if venture == "cs":
        return [g for g in items if get_venture_for_greenhouse_name(g["name"]) == "cs"]
    if venture == "csg":
        return [g for g in items if get_venture_for_greenhouse_name(g["name"]) == "csg"]
    return items


def filter_rows_by_venture(rows, venture):
    if venture == "all":
        return rows
    if venture == "cs":
        return [r for r in rows if get_venture_for_greenhouse_name(r["greenhouse"]) == "cs"]
    if venture == "csg":
        return [r for r in rows if get_venture_for_greenhouse_name(r["greenhouse"]) == "csg"]
    return rows

# ========================
# GENERAL HELPERS
# ========================
def get_expected(crop, plants):
    if crop == "Asparagus":
        return 150
    if crop == "Local Cucumber":
        return 600
    return yields.get(f"{crop}_{plants}", 0)


def get_price(crop):
    return prices.get(crop, 0)


def get_greenhouse_by_name(name):
    return next((g for g in greenhouses if g["name"] == name), None)


def get_greenhouse_by_no(no_value):
    return next((g for g in greenhouses if int(g.get("no", 0)) == int(no_value)), None)


def get_next_greenhouse_no():
    if not greenhouses:
        return 1
    return max(g.get("no", 0) for g in greenhouses) + 1


def get_window(g):
    harvest = parse_date(g.get("harvest", ""))
    end = parse_date(g.get("end", ""))
    return harvest, end


def get_soil_end(g):
    harvest, end = get_window(g)
    if not end:
        return None
    return end + timedelta(days=30)


def get_next_crop(current_crop):
    if current_crop in ["Cucumber", "Local Cucumber"]:
        return "Capsicum"
    elif current_crop == "Capsicum":
        return "Cucumber"
    else:
        return "Capsicum"


def get_status_for_greenhouse(g, today=None):
    if today is None:
        today = datetime.today()

    harvest, end = get_window(g)
    soil_end = get_soil_end(g)

    if not harvest or not end or not soil_end:
        return "Waiting", 0

    if harvest <= today <= end:
        return "Harvesting", get_expected(g["crop"], g["plants"])
    elif end < today <= soil_end:
        return "Soil Turning", 0
    else:
        return "Waiting", 0


def get_next_saturday(today=None):
    if today is None:
        today = datetime.today()

    days_ahead = 5 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7

    return today + timedelta(days=days_ahead)


def build_dashboard_row(g, today=None):
    if today is None:
        today = datetime.today()

    harvest, end = get_window(g)
    soil_end = get_soil_end(g)
    status, current_yield = get_status_for_greenhouse(g, today=today)

    nursery_obj = parse_date(g.get("nursery", ""))
    transplant_obj = parse_date(g.get("transplant", ""))

    if g.get("crop") == "Capsicum" and transplant_obj:
        nursery_obj = calculate_nursery_from_transplant(transplant_obj)
    else:
        nursery_obj = None

    return {
        **g,
        "yield": current_yield,
        "status": status,
        "venture": get_venture_for_greenhouse_name(g["name"]),
        "nursery_display": format_date_safe(nursery_obj),
        "transplant_display": format_date_safe(transplant_obj),
        "harvest_display": format_date_safe(harvest),
        "end_display": format_date_safe(end),
        "soil_end_display": format_date_safe(soil_end),
        "nursery_raw": to_date_string(nursery_obj),
        "transplant_raw": to_date_string(transplant_obj),
        "harvest_raw": g.get("harvest", ""),
        "end_raw": g.get("end", "")
    }


def build_forecast_week_row(week_date):
    total_yield = 0
    active_units = []

    for g in greenhouses:
        harvest, end = get_window(g)

        if not harvest or not end:
            continue

        if harvest <= week_date <= end:
            expected = get_expected(g["crop"], g["plants"])
            total_yield += expected

            active_units.append({
                "name": g["name"],
                "crop": g["crop"],
                "plants": g["plants"],
                "yield": expected
            })

    return {
        "week": week_date.strftime("%d %b %Y"),
        "yield": round(total_yield, 2),
        "active_units": active_units,
        "units_count": len(active_units)
    }


def build_monthly_summary(weekly_rows):
    monthly = {}

    for row in weekly_rows:
        try:
            month_key = datetime.strptime(row["week"], "%Y-%m-%d").strftime("%B %Y")
        except:
            continue

        if month_key not in monthly:
            monthly[month_key] = {
                "yield": 0,
                "revenue": 0,
                "records": 0
            }

        monthly[month_key]["yield"] += row["actual"]
        monthly[month_key]["revenue"] += row["revenue"]
        monthly[month_key]["records"] += 1

    return monthly


def build_summary(weekly_rows):
    return {
        "total_yield": round(sum(x["actual"] for x in weekly_rows), 2),
        "total_revenue": round(sum(x["revenue"] for x in weekly_rows), 2),
        "records": len(weekly_rows)
    }


def build_month_groups(weekly_rows):
    groups = {}

    for row in weekly_rows:
        try:
            month_key = datetime.strptime(row["week"], "%Y-%m-%d").strftime("%B %Y")
        except:
            month_key = "Other"

        if month_key not in groups:
            groups[month_key] = []

        groups[month_key].append(row)

    ordered = []
    for month_name, rows in groups.items():
        ordered.append({
            "month": month_name,
            "rows": rows,
            "total_yield": round(sum(x["actual"] for x in rows), 2),
            "total_revenue": round(sum(x["revenue"] for x in rows), 2),
            "records": len(rows)
        })

    return ordered


def get_recent_records_for_greenhouse(greenhouse_name, limit=3):
    rows = []

    for r in actual_data:
        if r.get("greenhouse") != greenhouse_name:
            continue

        d = parse_date(r.get("date", ""))
        if not d:
            continue

        try:
            y = float(r.get("yield", 0))
        except:
            y = 0

        rows.append({
            "date": d,
            "yield": y
        })

    rows = sorted(rows, key=lambda x: x["date"], reverse=True)
    return rows[:limit]


def weighted_average(values):
    if not values:
        return 0

    weights = list(range(1, len(values) + 1))
    numerator = sum(v * w for v, w in zip(values, weights))
    denominator = sum(weights)

    if denominator == 0:
        return 0

    return numerator / denominator


def build_next_harvest_projection(venture="all"):
    next_sat = get_next_saturday()
    projected_rows = []
    total_projection = 0

    selected_greenhouses = filter_greenhouses_by_venture(greenhouses, venture)

    for g in selected_greenhouses:
        harvest, end = get_window(g)

        if not harvest or not end:
            continue

        if not (harvest <= next_sat <= end):
            continue

        expected = get_expected(g["crop"], g["plants"])
        recent = get_recent_records_for_greenhouse(g["name"], limit=3)

        if recent:
            recent_values_oldest_to_newest = [x["yield"] for x in reversed(recent)]
            trend_projection = weighted_average(recent_values_oldest_to_newest)
            upper_cap = expected * 1.4 if expected > 0 else max(trend_projection, 0)
            projected = min(max(trend_projection, 0), upper_cap)
            basis = f"Based on last {len(recent)} weekly record(s)"
        else:
            projected = expected
            basis = "No recent actual data yet, using expected yield"

        projected = round(projected, 2)
        total_projection += projected

        projected_rows.append({
            "name": g["name"],
            "crop": g["crop"],
            "expected": round(expected, 2),
            "projected": projected,
            "basis": basis
        })

    return {
        "date": next_sat.strftime("%d %B %Y"),
        "total_projection": round(total_projection, 2),
        "rows": projected_rows
    }

# ========================
# DASHBOARD
# ========================
@app.route("/")
def dashboard():
    venture = request.args.get("venture", "all")
    today = datetime.today()
    all_data = []
    filtered_data = []
    total = 0

    harvesting_units = 0
    soil_turning_units = 0
    waiting_units = 0

    for g in greenhouses:
        row = build_dashboard_row(g, today=today)
        all_data.append(row)

    filtered_data = filter_greenhouses_by_venture(all_data, venture)

    for row in filtered_data:
        total += row["yield"]

        if row["status"] == "Harvesting":
            harvesting_units += 1
        elif row["status"] == "Soil Turning":
            soil_turning_units += 1
        else:
            waiting_units += 1

    summary = {
        "total_weekly_production": round(total, 2),
        "harvesting_units": harvesting_units,
        "soil_turning_units": soil_turning_units,
        "waiting_units": waiting_units
    }

    return render_template(
        "index.html",
        data=filtered_data,
        total=round(total, 2),
        summary=summary,
        current_venture=venture,
        venture_label=venture_label(venture)
    )

# ========================
# ADD GREENHOUSE
# ========================
@app.route("/add_greenhouse", methods=["POST"])
def add_greenhouse():
    name = request.form.get("name", "").strip()
    size = request.form.get("size", "").strip()
    tank = request.form.get("tank", "").strip()
    crop = request.form.get("crop", "").strip()
    variety = request.form.get("variety", "").strip()
    plants_raw = request.form.get("plants", "").strip()
    nursery_raw = request.form.get("nursery", "").strip()
    transplant_raw = request.form.get("transplant", "").strip()
    harvest_raw = request.form.get("harvest", "").strip()
    end_raw = request.form.get("end", "").strip()

    if not name or not crop or not plants_raw or not transplant_raw:
        return redirect("/")

    try:
        plants = int(plants_raw)
    except:
        plants = 0

    if plants <= 0:
        return redirect("/")

    nursery_obj = parse_date(nursery_raw)
    transplant_obj = parse_date(transplant_raw)
    harvest_obj = parse_date(harvest_raw)
    end_obj = parse_date(end_raw)

    if not transplant_obj:
        return redirect("/")

    if crop == "Capsicum":
        variety = "Passarella / Ilanga"
        nursery_obj = calculate_nursery_from_transplant(transplant_obj)
        harvest_obj = calculate_harvest_from_transplant(crop, transplant_obj)
        end_obj = calculate_end_from_harvest(crop, harvest_obj)

    elif crop == "Cucumber":
        nursery_obj = None
        harvest_obj = calculate_harvest_from_transplant(crop, transplant_obj)
        end_obj = calculate_end_from_harvest(crop, harvest_obj)

    elif crop == "Local Cucumber":
        size = "16x40"
        variety = "Mydas RZ"
        nursery_obj = None
        harvest_obj = calculate_harvest_from_transplant(crop, transplant_obj)
        end_obj = calculate_end_from_harvest(crop, harvest_obj)

    else:
        nursery_obj = None
        if not harvest_obj or not end_obj:
            return redirect("/")

    new_greenhouse = {
        "no": get_next_greenhouse_no(),
        "name": name,
        "size": size,
        "tank": tank,
        "crop": crop,
        "plants": plants,
        "harvest": to_date_string(harvest_obj),
        "end": to_date_string(end_obj),
        "variety": variety,
        "transplant": to_date_string(transplant_obj),
        "nursery": to_date_string(nursery_obj)
    }

    greenhouses.append(normalize_greenhouse(new_greenhouse))
    save_greenhouses(greenhouses)

    return redirect("/")

# ========================
# UPDATE GREENHOUSE DETAILS
# ========================
@app.route("/update_greenhouse", methods=["POST"])
def update_greenhouse():
    greenhouse_no = request.form.get("no", "").strip()
    name = request.form.get("name", "").strip()
    size = request.form.get("size", "").strip()
    tank = request.form.get("tank", "").strip()
    crop = request.form.get("crop", "").strip()
    variety = request.form.get("variety", "").strip()
    plants_raw = request.form.get("plants", "").strip()
    nursery_raw = request.form.get("nursery", "").strip()
    transplant_raw = request.form.get("transplant", "").strip()
    harvest_raw = request.form.get("harvest", "").strip()
    end_raw = request.form.get("end", "").strip()

    if not greenhouse_no or not name or not crop or not plants_raw or not transplant_raw:
        return redirect("/")

    g = get_greenhouse_by_no(greenhouse_no)
    if not g:
        return redirect("/")

    try:
        plants = int(plants_raw)
    except:
        plants = 0

    if plants <= 0:
        return redirect("/")

    nursery_obj = parse_date(nursery_raw)
    transplant_obj = parse_date(transplant_raw)
    harvest_obj = parse_date(harvest_raw)
    end_obj = parse_date(end_raw)

    if not transplant_obj:
        return redirect("/")

    if crop == "Capsicum":
        variety = "Passarella / Ilanga"
        nursery_obj = calculate_nursery_from_transplant(transplant_obj)
        harvest_obj = calculate_harvest_from_transplant(crop, transplant_obj)
        end_obj = calculate_end_from_harvest(crop, harvest_obj)

    elif crop == "Cucumber":
        nursery_obj = None
        harvest_obj = calculate_harvest_from_transplant(crop, transplant_obj)
        end_obj = calculate_end_from_harvest(crop, harvest_obj)

    elif crop == "Local Cucumber":
        size = "16x40"
        variety = "Mydas RZ"
        nursery_obj = None
        harvest_obj = calculate_harvest_from_transplant(crop, transplant_obj)
        end_obj = calculate_end_from_harvest(crop, harvest_obj)

    else:
        nursery_obj = None
        if not harvest_obj or not end_obj:
            return redirect("/")

    old_name = g["name"]

    g["name"] = name
    g["size"] = size
    g["tank"] = tank
    g["crop"] = crop
    g["plants"] = plants
    g["harvest"] = to_date_string(harvest_obj)
    g["end"] = to_date_string(end_obj)
    g["variety"] = variety
    g["transplant"] = to_date_string(transplant_obj)
    g["nursery"] = to_date_string(nursery_obj)

    normalized = normalize_greenhouse(g)
    g.update(normalized)

    if old_name != name:
        for row in actual_data:
            if row.get("greenhouse") == old_name:
                row["greenhouse"] = name
                row["crop"] = crop
        save_data(actual_data)

    save_greenhouses(greenhouses)
    return redirect("/")

# ========================
# DELETE GREENHOUSE
# ========================
@app.route("/delete_greenhouse", methods=["POST"])
def delete_greenhouse():
    greenhouse_no = request.form.get("no", "").strip()

    if not greenhouse_no:
        return redirect("/")

    g = get_greenhouse_by_no(greenhouse_no)
    if not g:
        return redirect("/")

    greenhouse_name = g["name"]

    global greenhouses
    greenhouses = [x for x in greenhouses if int(x.get("no", 0)) != int(greenhouse_no)]
    save_greenhouses(greenhouses)

    global actual_data
    actual_data = [x for x in actual_data if x.get("greenhouse") != greenhouse_name]
    save_data(actual_data)

    return redirect("/")

# ========================
# UPDATE END DATE
# ========================
@app.route("/update_end_date", methods=["POST"])
def update_end_date():
    greenhouse_name = request.form.get("greenhouse")
    new_end = request.form.get("end_date")

    if not greenhouse_name or not new_end:
        return redirect("/")

    g = get_greenhouse_by_name(greenhouse_name)
    if not g:
        return redirect("/")

    parsed_end = parse_date(new_end)
    if not parsed_end:
        return redirect("/")

    g["end"] = new_end
    save_greenhouses(greenhouses)

    return redirect("/")

# ========================
# INPUT
# ========================
@app.route("/input", methods=["GET", "POST"])
def input_data():
    message = ""
    error = ""

    if request.method == "POST":
        date = request.form.get("date")
        greenhouse_name = request.form.get("greenhouse")
        yield_value = request.form.get("yield")

        if not date or not greenhouse_name or yield_value is None:
            error = "Please fill in all required fields."
            return render_template(
                "input.html",
                greenhouses=greenhouses,
                message=message,
                error=error
            )

        try:
            yield_value = float(yield_value)
        except:
            yield_value = 0

        g = get_greenhouse_by_name(greenhouse_name)
        if not g:
            error = "Selected greenhouse was not found."
            return render_template(
                "input.html",
                greenhouses=greenhouses,
                message=message,
                error=error
            )

        crop = g["crop"]

        existing = next(
            (
                x for x in actual_data
                if x.get("date") == date and x.get("greenhouse") == greenhouse_name
            ),
            None
        )

        if existing:
            existing["yield"] = yield_value
            existing["crop"] = crop
            message = "Existing record updated successfully."
        else:
            actual_data.append({
                "date": date,
                "greenhouse": greenhouse_name,
                "crop": crop,
                "yield": yield_value
            })
            message = "Weekly harvest data added successfully."

        save_data(actual_data)
        return redirect("/performance")

    return render_template(
        "input.html",
        greenhouses=greenhouses,
        message=message,
        error=error
    )

# ========================
# UPDATE PERFORMANCE ENTRY
# ========================
@app.route("/update_performance_entry", methods=["POST"])
def update_performance_entry():
    entry_date = request.form.get("date", "").strip()
    greenhouse_name = request.form.get("greenhouse", "").strip()
    new_yield_raw = request.form.get("yield", "").strip()
    venture = request.form.get("venture", "all").strip()

    if not entry_date or not greenhouse_name or new_yield_raw == "":
        return redirect(f"/performance?venture={venture}")

    try:
        new_yield = float(new_yield_raw)
    except:
        return redirect(f"/performance?venture={venture}")

    updated = False
    for row in actual_data:
        if row.get("date") == entry_date and row.get("greenhouse") == greenhouse_name:
            row["yield"] = new_yield
            updated = True
            break

    if updated:
        save_data(actual_data)

    return redirect(f"/performance?venture={venture}")

# ========================
# PERFORMANCE
# ========================
@app.route("/performance")
def performance():
    venture = request.args.get("venture", "all")
    weekly = []

    for r in actual_data:
        greenhouse_name = r.get("greenhouse")
        g = get_greenhouse_by_name(greenhouse_name)

        if not g:
            continue

        crop = g["crop"]
        d = parse_date(r.get("date", ""))

        if not d:
            continue

        harvest, end = get_window(g)
        if not harvest or not end:
            continue

        try:
            actual = float(r.get("yield", 0))
        except:
            actual = 0

        expected = get_expected(crop, g["plants"])
        variance = actual - expected
        variance_pct = (variance / expected * 100) if expected else 0
        revenue = actual * get_price(crop)

        weekly.append({
            "week": r["date"],
            "greenhouse": greenhouse_name,
            "venture": get_venture_for_greenhouse_name(greenhouse_name),
            "crop": crop,
            "actual": round(actual, 2),
            "expected": round(expected, 2),
            "variance": round(variance, 2),
            "variance_pct": round(variance_pct, 2),
            "revenue": round(revenue, 2)
        })

    weekly = sorted(weekly, key=lambda x: x["week"])
    weekly = filter_rows_by_venture(weekly, venture)

    monthly = build_monthly_summary(weekly)
    monthly_groups = build_month_groups(weekly)
    summary = build_summary(weekly)
    next_harvest_projection = build_next_harvest_projection(venture=venture)

    return render_template(
        "performance.html",
        weekly=weekly,
        monthly=monthly,
        monthly_groups=monthly_groups,
        summary=summary,
        greenhouses=greenhouses,
        next_harvest_projection=next_harvest_projection,
        current_venture=venture,
        venture_label=venture_label(venture)
    )

# ========================
# FORECAST
# ========================
@app.route("/forecast")
def forecast():
    today = datetime.today()

    forecast_data = []
    recommendations = []

    active_units_now = 0
    soil_turning_units_now = 0
    waiting_units_now = 0

    for g in greenhouses:
        status, _ = get_status_for_greenhouse(g, today=today)

        if status == "Harvesting":
            active_units_now += 1
        elif status == "Soil Turning":
            soil_turning_units_now += 1
        else:
            waiting_units_now += 1

    for week in range(8):
        week_date = today + timedelta(days=7 * week)
        week_row = build_forecast_week_row(week_date)
        forecast_data.append(week_row)

    for g in greenhouses:
        harvest, end = get_window(g)
        soil_end = get_soil_end(g)

        if not harvest or not end or not soil_end:
            continue

        if end < today <= soil_end:
            current_crop = g["crop"]
            next_crop = get_next_crop(current_crop)

            recommendations.append({
                "name": g["name"],
                "current_crop": current_crop,
                "crop": next_crop,
                "date": soil_end.strftime("%d %B %Y"),
                "reason": f"{current_crop} finished. Plant {next_crop} after soil recovery.",
                "soil_recovery_ends": soil_end.strftime("%d %B %Y")
            })

        elif today < harvest:
            recommendations.append({
                "name": g["name"],
                "current_crop": g["crop"],
                "crop": g["crop"],
                "date": harvest.strftime("%d %B %Y"),
                "reason": "Greenhouse is waiting for harvest cycle to begin.",
                "soil_recovery_ends": "-"
            })

    recommendations = sorted(recommendations, key=lambda x: x["name"])

    summary = {
        "active_units": active_units_now,
        "soil_turning_units": soil_turning_units_now,
        "idle_units": waiting_units_now,
        "next_8_weeks_total": round(sum(x["yield"] for x in forecast_data), 2),
        "highest_week_yield": max([x["yield"] for x in forecast_data], default=0),
        "forecast_weeks": len(forecast_data)
    }

    return render_template(
        "forecast.html",
        forecast=forecast_data,
        recommendations=recommendations,
        summary=summary
    )

# ========================
# RUN
# ========================
if __name__ == "__main__":
    app.run(debug=True)