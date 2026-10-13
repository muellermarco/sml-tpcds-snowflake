"""Generate the 'TPCDS Overview' Power BI project (PBIP / PBIR) next to the Seed project.

The connection (modelReference.json), theme and report settings are copied from
'Seed/TPCDS Seed'. Every field binding uses the CSDL ReferenceNames of the DemoModel
cube in catalog TPCDS-MM-Snowflake_main (DISCOVER_CSDL_METADATA, 2026-10-13).

Run:  python3 generate_tpcds_overview.py            (from Reports/Power BI)
"""
import json, os, random, shutil, sys, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = os.path.join(HERE, "Seed")
NAME = "TPCDS Overview"
OUT = os.path.join(HERE, NAME)
REP = os.path.join(OUT, NAME + ".Report")
SM = os.path.join(OUT, NAME + ".SemanticModel")
PAGES = os.path.join(REP, "definition", "pages")
S = "https://developer.microsoft.com/json-schemas/fabric/"
random.seed(20261013)


def hid(): return "".join(random.choice("0123456789abcdef") for _ in range(20))


def w(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def rj(path):
    with open(path) as f:
        return json.load(f)


# ---------- fields (CSDL ReferenceNames) ----------
def M(name): return {"Measure": {"Expression": {"SourceRef": {"Entity": "CubeMeasures"}}, "Property": name}}
def HL(entity, hier, level): return {"HierarchyLevel": {"Expression": {"Hierarchy": {"Expression": {"SourceRef": {"Entity": entity}}, "Hierarchy": hier}}, "Level": level}}
def COL(entity, prop): return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def proj(field, display=None, active=None):
    if "Measure" in field:
        p = field["Measure"]["Property"]; qr = f"CubeMeasures.{p}"; nq = p
    elif "HierarchyLevel" in field:
        h = field["HierarchyLevel"]; e = h["Expression"]["Hierarchy"]["Expression"]["SourceRef"]["Entity"]
        hn = h["Expression"]["Hierarchy"]["Hierarchy"]; l = h["Level"]
        qr = f"{e}.{hn}.{l}"; nq = f"{hn} {l}"
    else:
        e = field["Column"]["Expression"]["SourceRef"]["Entity"]; p = field["Column"]["Property"]; qr = f"{e}.{p}"; nq = p
    d = {"field": field, "queryRef": qr, "nativeQueryRef": nq}
    if display: d["displayName"] = display
    if active is not None: d["active"] = active
    return d


# Dates (role-played: Sold / Ship)
SOLD = "Sold Date Dimension"
S_YEAR, S_QTR, S_MONTH, S_DAY = (HL(SOLD, SOLD, l) for l in ("Sold Calendar Year", "Sold Calendar Quarter", "Sold Calendar Month", "Sold Time Dimension"))
S_MOY = COL(SOLD, "Sold d_month_of_year")
SHIP = "Ship Date Dimension"
SH_YEAR, SH_QTR, SH_MONTH = (HL(SHIP, SHIP, l) for l in ("Ship Calendar Year", "Ship Calendar Quarter", "Ship Calendar Month"))
# Product
PROD = "Product Dimension"
P_CAT, P_CLASS, P_BRAND, P_ITEM = (HL(PROD, PROD, l) for l in ("I Category", "Product Class", "Product Brand", "Product Dimension"))
P_COLOR, P_SIZE = COL(PROD, "d_i_color"), COL(PROD, "d_i_size")
# Store
STORE = "Store Dimension"
ST_COUNTRY, ST_STATE, ST_COUNTY, ST_CITY, ST_NUM = (HL(STORE, STORE, l) for l in ("d_store_country", "d_store_state", "d_store_county", "d_store_city", "Store Dimension"))
ST_NAME, ST_FLOOR, ST_EMPL = COL(STORE, "d_store_name"), COL(STORE, "d_s_floor_space"), COL(STORE, "d_s_number_employees")
# Customer
CUST = "Customer Dimension"
C_COUNTRY, C_STATE, C_COUNTY, C_CITY, C_NUM = (HL(CUST, CUST, l) for l in ("Customer Country", "Customer State", "Customer County", "Customer City", "Customer Number"))
C_PREF = COL(CUST, "Preferred Customer Ind")
CDEMO = "Customer Demographics"
C_GENDER, C_CREDIT = COL(CDEMO, "d_cd_gender"), COL(CDEMO, "d_cd_credit_rating")
# Fulfilment
WH = "Fulfilling Warehouse"
W_COUNTRY, W_STATE, W_COUNTY, W_CITY, W_ID = (HL(WH, WH, l) for l in ("Warehouse Country", "Warehouse State", "Warehouse County", "Warehouse City", "W Ware House ID"))
W_NAME = COL(WH, "d_warehouse_name")
SHIPM = "Ship Mode"
SM_MODE, SM_TYPE, SM_CARRIER = (HL(SHIPM, SHIPM, l) for l in ("Ship Mode_1", "Ship Mode Type", "Carrier"))
# Promotions
PROMO = "Promotions"
PR_ACTIVE, PR_SK = HL(PROMO, PROMO, "Promo Active Indicator"), HL(PROMO, PROMO, "Promotions")
PR_NAME = COL(PROMO, "d_promo_name")
PR_TV, PR_EMAIL, PR_DMAIL, PR_CATALOG, PR_EVENT = (COL(PROMO, c) for c in ("d_channel_tv", "d_channel_email", "d_channel_direct_mail", "d_channel_catalog", "d_channel_event"))

# ---------- helpers ----------
def lit(v): return {"expr": {"Literal": {"Value": v}}}


def title_obj(text, size="12pt"):
    return {"title": [{"properties": {"show": lit("true"), "text": lit("'" + text.replace("'", "''") + "'"), "fontSize": lit(f"'{size}'")}}]}


def sort(field, direction="Descending"): return {"sort": [{"field": field, "direction": direction}], "isDefaultSort": True}


_z = [0]
def nz(): _z[0] += 1; return _z[0]


def visual(vtype, roles, x, y, wd, ht, ttl=None, sortdef=None, objects=None, vfilters=None):
    z = nz()
    v = {"$schema": S + "item/report/definition/visualContainer/2.13.0/schema.json", "name": hid(),
         "position": {"x": x, "y": y, "z": z, "height": ht, "width": wd, "tabOrder": z},
         "visual": {"visualType": vtype, "query": {"queryState": {r: {"projections": ps} for r, ps in roles.items()}}, "drillFilterOtherVisuals": True}}
    if sortdef: v["visual"]["query"]["sortDefinition"] = sortdef
    if "Category" in roles and vtype not in ("donutChart", "pieChart"):
        # Force a categorical axis. Year (Double) and Month (DateTime) levels would otherwise get a
        # continuous axis, and for line charts Power BI then emits SAMPLECARTESIANPOINTSBYCOVER /
        # SAMPLEAXISWITHLOCALMINMAX, which AtScale's DAX parser rejects ("Failed to parse input ...").
        objects = {**(objects or {}), "categoryAxis": [{"properties": {"axisType": lit("'Categorical'")}}]}
    if objects: v["visual"]["objects"] = objects
    if ttl: v["visual"]["visualContainerObjects"] = title_obj(ttl)
    if vfilters: v["filterConfig"] = {"filters": vfilters}
    return v


def textbox(runs, x, y, wd, ht):
    z = nz(); paras = []
    for r in runs:
        if isinstance(r, str): r = {"value": r}
        style = {"fontSize": r.get("size", "11pt")}
        if r.get("bold"): style["fontWeight"] = "bold"
        paras.append({"textRuns": [{"value": r["value"], "textStyle": style}]})
    return {"$schema": S + "item/report/definition/visualContainer/2.13.0/schema.json", "name": hid(),
            "position": {"x": x, "y": y, "z": z, "height": ht, "width": wd, "tabOrder": z},
            "visual": {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": paras}}]}, "drillFilterOtherVisuals": True}}


CARD_OBJ = {"labels": [{"properties": {"fontSize": lit("'26'")}}], "categoryLabels": [{"properties": {"show": lit("true"), "fontSize": lit("'11'")}}]}
def card(measure, x, y, wd, ht, label, vfilters=None):
    return visual("card", {"Values": [proj(M(measure), display=label)]}, x, y, wd, ht, objects=CARD_OBJ, vfilters=vfilters)


def slicer(field, x, y, wd, ht, ttl, dropdown=True):
    objs = {"header": [{"properties": {"show": lit("false")}}]}
    if dropdown: objs["general"] = [{"properties": {"orientation": lit("1")}}]
    return visual("slicer", {"Values": [proj(field, active=True)]}, x, y, wd, ht, ttl, objects=objs)


LABELS_ON = {"labels": [{"properties": {"show": lit("true")}}]}
LEGEND_TOP = {"legend": [{"properties": {"show": lit("true"), "position": lit("'Top'")}}]}
PCT_LABELS = {"labels": [{"properties": {"show": lit("true"), "labelStyle": lit("'Category, percent of total'")}}]}
def drill(*levels): return [proj(l, active=(i == 0)) for i, l in enumerate(levels)]


# ---------- layout constants (1920 x 1080) ----------
X0, W = 40, 1840
HDR_Y, HDR_H = 20, 90
CARD_Y, CARD_H = 120, 125
ROW1_Y, ROW2_Y, ROW_H = 265, 665, 380


def cards_row(specs, y=CARD_Y, x0=X0, width=W):
    n = len(specs); gap = 16; cw = (width - gap * (n - 1)) / n; out = []
    for i, sp in enumerate(specs):
        measure, label = sp[0], sp[1]; vf = sp[2] if len(sp) > 2 else None
        out.append(card(measure, round(x0 + i * (cw + gap)), y, round(cw), CARD_H, label, vfilters=vf))
    return out


def cols(n, gap=20):
    cw = (W - gap * (n - 1)) / n
    return [(round(X0 + i * (cw + gap)), round(cw)) for i in range(n)]


pages = []
def page(display, visuals, filters=None):
    pid = hid(); _z[0] = 0
    p = {"$schema": S + "item/report/definition/page/2.1.0/schema.json", "name": pid, "displayName": display,
         "displayOption": "FitToPage", "height": 1080, "width": 1920}
    if filters: p["filterConfig"] = {"filters": filters}
    pages.append((pid, p, visuals))


def header(title, sub): return textbox([{"value": title, "size": "20pt", "bold": True}, {"value": sub, "size": "11pt"}], X0, HDR_Y, W, HDR_H)
def reading(paras, x, y, wd, ht): return textbox([{"value": "Reading the page", "size": "13pt", "bold": True}, *paras], x, y, wd, ht)


c2, c3, c4 = cols(2), cols(3), cols(4)
NET_SW = [proj(M("m_ss_net_profit_sum"), "Store net profit"), proj(M("m_ws_net_profit_sum"), "Web net profit")]
SALES_SW = [proj(M("m_ss_net_paid_sum"), "Store net paid"), proj(M("m_ws_net_paid_sum"), "Web net paid")]
QTY_SW = [proj(M("m_ss_quantity_sum"), "Store quantity"), proj(M("m_ws_quantity_sum"), "Web quantity")]

# ================= 1. Overview =================
page("Overview", [
    header("TPC-DS on Snowflake: store and web sales through one AtScale model",
           "DemoModel joins two TPC-DS fact tables, store_sales and web_sales, to conformed Product, Customer, Customer Demographics, Promotions and a role-played Date dimension (Sold and Ship). Every chart here is a live query against Snowflake through the semantic layer; the 'Total' measures add the two channels so a single figure covers both."),
    *cards_row([("Total Net Profit", "Total net profit (store + web)"), ("m_ss_net_profit_sum", "Store net profit"), ("m_ws_net_profit_sum", "Web net profit"),
                ("Total Quantity Sold", "Units sold, both channels"), ("Store and Web Purchased Amount", "Purchased amount, both channels"), ("Customer Count", "Customer rows (store + web)")]),
    visual("clusteredColumnChart", {"Category": drill(S_YEAR, S_QTR, S_MONTH), "Y": NET_SW}, c3[0][0], ROW1_Y, c3[0][1], ROW_H,
           "Net profit by sold year, store against web (drill to quarter and month)", sort(S_YEAR, "Ascending"), objects=LEGEND_TOP),
    visual("clusteredBarChart", {"Category": drill(P_CAT, P_CLASS, P_BRAND), "Y": [proj(M("Store and Web Purchased Amount"), "Purchased amount")]}, c3[1][0], ROW1_Y, c3[1][1], ROW_H,
           "Purchased amount by product category (drill to class and brand)", sort(M("Store and Web Purchased Amount")), objects=LABELS_ON),
    visual("lineChart", {"Category": [proj(S_MONTH)], "Y": QTY_SW}, c3[2][0], ROW1_Y, c3[2][1], ROW_H,
           "Units sold per month, store against web", sort(S_MONTH, "Ascending"), objects=LEGEND_TOP),
    visual("pivotTable", {"Rows": drill(P_CAT, P_CLASS), "Columns": [proj(S_YEAR)], "Values": [proj(M("Total Net Profit"), "Total net profit")]}, c3[0][0], ROW2_Y, c3[0][1] + c3[1][1] + 20, ROW_H,
           "Total net profit by product category and sold year (the two facts are summed through conformed dimensions)"),
    reading(["Six sold years are loaded, 1998 to 2003, and 2003 holds only the first weeks, so the trend charts fall off a cliff at the end. The TPC-DS generator produces negative net profit by design (wholesale cost exceeds the discounted sales price on most lines), so every profit figure is a loss; the shape across years, categories and channels is still meaningful. Store sales dominate: the store channel carries about four times the units and purchased amount of the web channel and about twelve times its net loss, because the loss per unit is 16.4 in store against 5.1 on the web. The ten product categories each take ten percent of sales to within a fraction of a point, so the category bars are a test of the drill (class and brand differ) rather than a ranking. The fact tables are large (28.8 billion store rows, 7.2 billion web rows), so a cold cut takes minutes until the aggregate for it exists.",
             "Model capabilities on this page: two fact tables behind one measure set, calculated metrics that add store and web (Total Net Profit, Total Quantity Sold, Store and Web Purchased Amount), a role-played Sold Date hierarchy with drill from year to month, and a Product hierarchy shared by both facts."],
            c3[2][0], ROW2_Y, c3[2][1], ROW_H),
])

# ================= 2. Store sales =================
page("Store Sales", [
    header("Store channel: where and what the stores sell",
           "store_sales joins Store Dimension (Country > State > County > City > Store), Product, Customer, Customer Demographics, Promotions and the Sold Date. Pick a sold year in the slicer to focus every visual; the Store Sales Increase line compares each period with the previous member of the Sold Date hierarchy, so at month grain it is month over month."),
    slicer(S_YEAR, X0, CARD_Y, 260, CARD_H, "Sold calendar year"),
    *cards_row([("m_ss_net_paid_sum", "Store net paid (revenue)"), ("m_ss_net_profit_sum", "Store net profit"), ("m_ss_quantity_sum", "Store units sold"),
                ("Avg Store Unit Net Profit", "Net profit per unit"), ("m_store_coupon_amt_sum", "Coupon amount"), ("m_ss_sales_price_avg", "Average line sales price")], x0=X0 + 280, width=W - 280),
    visual("clusteredBarChart", {"Category": drill(ST_STATE, ST_COUNTY, ST_CITY, ST_NAME), "Y": [proj(M("m_ss_net_paid_sum"), "Store net paid")]}, c3[0][0], ROW1_Y, c3[0][1], ROW_H,
           "Store net paid by state (drill to county, city and store)", sort(M("m_ss_net_paid_sum")), objects=LABELS_ON),
    visual("lineClusteredColumnComboChart", {"Category": drill(S_YEAR, S_QTR, S_MONTH), "Y": [proj(M("m_store_sales_price"), "Store sales price (sum)")], "Y2": [proj(M("Store Sales Increase"), "Ratio to previous period")]}, c3[1][0], ROW1_Y, c3[1][1], ROW_H,
           "Store Sales Price per period (columns) and Store Sales Increase, its ratio to the previous period (line)", sort(S_YEAR, "Ascending"), objects=LEGEND_TOP),
    visual("clusteredBarChart", {"Category": drill(P_CAT, P_CLASS), "Y": [proj(M("Store Revenue Ratio by Product Class"), "Share of store sales")]}, c3[2][0], ROW1_Y, c3[2][1], ROW_H,
           "Share of store sales by product category (drill to class): a ratio against the All product member", sort(M("Store Revenue Ratio by Product Class")), objects=LABELS_ON),
    visual("pivotTable", {"Rows": drill(ST_STATE, ST_CITY), "Columns": [proj(P_CAT)], "Values": [proj(M("m_ss_net_profit_sum"), "Store net profit")]}, c3[0][0], ROW2_Y, c3[0][1] + c3[1][1] + 20, ROW_H,
           "Store net profit by state and product category"),
    reading(["Store Sales Price sums the unit sales price of every line, so it is a price total rather than revenue; Store Net Paid is what the customer paid and is the revenue measure on the cards and bars. Stores sit in 36 US states and the volume follows how many stores the generator placed in each: Georgia carries about nine percent of store sales, then Texas, Michigan, New Mexico and Nebraska, while a dozen states carry under one percent. Net profit per unit is 16.4 below zero in every state to within a few cents, so the ranking by net paid and by net loss is the same. Store Revenue Ratio by Product Class divides each product member's sales by the All member, so the bars sum to one at category level and the drill to class shows the share inside each category.",
             "Model capabilities: a five-level geographic hierarchy with the store name as a secondary attribute, a previous-member calc (Store Sales Increase) that follows the drill grain, a ratio-to-All calc that stays correct at every cut, and a page slicer the model honours."],
            c3[2][0], ROW2_Y, c3[2][1], ROW_H),
])

# ================= 3. Web sales =================
WEB_COST = [proj(M("m_ws_net_paid_sum"), "Web net paid"), proj(M("m_ws_ext_wholesale_cost_sum"), "Wholesale cost"), proj(M("m_ws_ext_discount_amt_sum"), "Discount"),
            proj(M("m_ws_ext_ship_cost_sum"), "Ship cost"), proj(M("m_ws_net_paid_inc_ship_tax_sum"), "Net paid incl. tax and ship"), proj(M("m_ws_net_profit_sum"), "Web net profit")]
page("Web Sales", [
    header("Web channel: fulfilment, shipping and the cost stack",
           "web_sales is the only fact that joins Fulfilling Warehouse and Ship Mode, and it carries two dates: the Sold Date and the Ship Date are the same Date Dimension role-played twice. Warehouse and ship-mode cuts therefore only ever show web figures; store measures return blank there, which is the model's unrelated-dimension handling at work."),
    slicer(S_YEAR, X0, CARD_Y, 260, CARD_H, "Sold calendar year"),
    *cards_row([("m_ws_net_paid_sum", "Web net paid (revenue)"), ("m_ws_net_profit_sum", "Web net profit"), ("m_ws_quantity_sum", "Web units sold"),
                ("Average Web Unit Net Profit", "Net profit per unit"), ("m_ws_ext_ship_cost_sum", "Shipping cost"), ("m_ws_ext_discount_amt_sum", "Discount given")], x0=X0 + 280, width=W - 280),
    visual("clusteredColumnChart", {"Category": drill(S_YEAR, S_QTR, S_MONTH), "Y": [proj(M("m_ws_net_paid_sum"), "Web net paid")]}, c3[0][0], ROW1_Y, c3[0][1], ROW_H,
           "Web net paid by sold year (drill to quarter and month)", sort(S_YEAR, "Ascending"), objects=LABELS_ON),
    visual("clusteredBarChart", {"Category": drill(SM_TYPE, SM_CARRIER), "Y": [proj(M("m_ws_net_paid_sum"), "Web net paid"), proj(M("m_ws_ext_ship_cost_sum"), "Ship cost")]}, c3[1][0], ROW1_Y, c3[1][1], ROW_H,
           "Web net paid and shipping cost by ship mode type (drill to carrier)", sort(M("m_ws_net_paid_sum")), objects=LEGEND_TOP),
    visual("clusteredBarChart", {"Category": drill(W_STATE, W_CITY, W_NAME), "Y": [proj(M("m_ws_net_paid_sum"), "Web net paid")]}, c3[2][0], ROW1_Y, c3[2][1], ROW_H,
           "Web net paid by fulfilling warehouse state (drill to city and warehouse)", sort(M("m_ws_net_paid_sum")), objects=LABELS_ON),
    visual("tableEx", {"Values": [proj(S_YEAR, "Sold year")] + WEB_COST}, c3[0][0], ROW2_Y, c3[0][1] + c3[1][1] + 20, ROW_H,
           "The web cost stack per sold year: net paid, wholesale cost, discount, shipping, net paid incl. tax and ship, net profit", sort(S_YEAR, "Ascending")),
    reading(["The web channel is about a quarter of the store channel by units and purchased amount, loses a third as much per unit (5.1 against 16.4), and carries costs the store channel does not record: shipping and a separate discount line. The Web Sales measure is left off this page on purpose: its column multiplies the extended sales price by quantity a second time, so it runs about a thousand times the comparable store figure; Web Net Paid is the revenue measure here. Ship mode types split web sales almost evenly, because the generator assigns modes at random; the point of the chart is that the Ship Mode and Warehouse dimensions resolve only through web_sales. Switch the trend chart to the Ship Date hierarchy in the field list to see the same sales shifted by the shipping lag.",
             "Model capabilities: a role-played date (Sold and Ship) from one dimension, dimensions reachable from one fact only, per-unit calcs (Average Web Unit Net Profit), and a table that lines up the base measures the calculations are built from."],
            c3[2][0], ROW2_Y, c3[2][1], ROW_H),
])

# ================= 4. Customers and promotions =================
page("Customers & Promotions", [
    header("Who buys, and what the promotions do",
           "Customer Dimension is snowflaked over customer and customer_address (Country > State > County > City > Customer), Customer Demographics carries gender and credit rating as secondary attributes, and both facts join both. Promotions exposes the channel flags and the discount-active indicator. Use the two slicers to cut every visual by gender and credit rating."),
    slicer(C_GENDER, X0, CARD_Y, 260, CARD_H, "Gender"),
    slicer(C_CREDIT, X0 + 280, CARD_Y, 260, CARD_H, "Credit rating"),
    *cards_row([("Customer Count", "Customer rows, both channels"), ("m_SS_CUSTOMER_SK_count", "Store customer rows"), ("m_WS_BILL_CUSTOMER_SK_count", "Web customer rows"),
                ("Total Net Profit", "Total net profit"), ("Store and Web Purchased Amount", "Purchased amount")], x0=X0 + 560, width=W - 560),
    visual("clusteredBarChart", {"Category": [proj(C_CREDIT, "Credit rating")], "Y": [proj(M("Store and Web Purchased Amount"), "Purchased amount")]}, c4[0][0], ROW1_Y, c4[0][1], ROW_H,
           "Purchased amount by credit rating", sort(M("Store and Web Purchased Amount")), objects=LABELS_ON),
    visual("donutChart", {"Category": [proj(C_GENDER, "Gender")], "Y": [proj(M("Total Quantity Sold"), "Units sold")]}, c4[1][0], ROW1_Y, c4[1][1], ROW_H,
           "Units sold by gender", objects=PCT_LABELS),
    visual("clusteredBarChart", {"Category": drill(C_STATE, C_COUNTY, C_CITY), "Y": [proj(M("Store and Web Purchased Amount"), "Purchased amount")]}, c4[2][0], ROW1_Y, c4[2][1], ROW_H,
           "Purchased amount by customer state (drill to county and city)", sort(M("Store and Web Purchased Amount")), objects=LABELS_ON),
    visual("clusteredColumnChart", {"Category": [proj(C_PREF, "Preferred customer")], "Y": NET_SW}, c4[3][0], ROW1_Y, c4[3][1], ROW_H,
           "Net profit by preferred-customer flag, store against web", objects=LEGEND_TOP),
    visual("clusteredBarChart", {"Category": [proj(PR_ACTIVE, "Discount active")], "Y": SALES_SW}, c4[0][0], ROW2_Y, c4[0][1], ROW_H,
           "Net paid by promotion discount-active flag (no promotion in the data has it set)", objects=LEGEND_TOP),
    visual("pivotTable", {"Rows": [proj(PR_NAME, "Promotion")], "Columns": [proj(PR_TV, "TV")], "Values": [proj(M("m_store_sales_price"), "Store sales"), proj(M("m_web_sales_sum"), "Web sales"), proj(M("m_store_coupon_amt_sum"), "Coupons")]},
           c4[1][0], ROW2_Y, c4[1][1] + c4[2][1] + 20, ROW_H, "Promotions by name, split by the TV channel flag", sort(M("m_store_sales_price"))),
    reading(["Customer Count is the sum of two row counts, store and web, not a distinct count of people; it is a counting measure for row volume and the card label says so. Gender and credit rating split sales almost evenly, again by construction of the generator, which makes them good slicers for checking that every visual re-queries consistently. Promotions are keyed by surrogate; the name and channel flags are secondary attributes on the leaf level. No promotion in this dataset has the discount-active flag set to Y, so the flag chart shows one N bar plus a blank member for the 1.4 percent of lines whose promotion key matches nothing: that blank member is how the model surfaces referential gaps rather than dropping the rows.",
             "Model capabilities: a snowflaked customer dimension, secondary attributes bound directly as columns (gender, credit rating, preferred flag, promotion name and channel flags), slicers on a non-hierarchy attribute, and a matrix that pivots one attribute against another."],
            c4[3][0], ROW2_Y, c4[3][1], ROW_H),
])

# ================= 5. About the model =================
page("About the Model", [
    header("How DemoModel is built: SML, a shared package and CI/CD to Snowflake",
           "This page describes the model behind the report. It is maintained as Semantic Modeling Language (SML) YAML in the sml-tpcds-snowflake repository, pulls shared objects from the sml-tpcds-common package at a pinned commit, and is deployed to the TPCDS-MM-Snowflake catalog by the AtScale CI/CD pipeline. The two charts show the same web net paid once by Sold Date and once by Ship Date."),
    textbox([{"value": "Facts and grain", "size": "13pt", "bold": True},
             "store_sales: one row per store sales line (SS_*), joined to Store, Product, Customer, Customer Demographics, Promotions and the Sold Date. web_sales: one row per web sales line (WS_*), joined to Product, Customer, Customer Demographics, Promotions, Ship Mode, Fulfilling Warehouse and both Sold and Ship dates. Both datasets add calculated columns in SQL: Purchased Amount, a row counter and price tiers.",
             {"value": "Dimensions", "size": "13pt", "bold": True},
             "Date Dimension (Year > Quarter > Month > Date, with Month of Year and Month Sequence) is role-played as Sold and Ship. Product (Category > Class > Brand > Item, plus color and size). Store (Country > State > County > City > Store, plus name, floor space, employees). Customer (Country > State > County > City > Customer, snowflaked over customer_address, plus the preferred flag). Customer Demographics (gender, credit rating). Promotions (Discount Active > Promotion, plus name and five channel flags). Ship Mode (Mode > Type > Carrier). Fulfilling Warehouse (Country > State > County > City > ID > Warehouse)."],
            c3[0][0], CARD_Y, c3[0][1], ROW_H + 145),
    textbox([{"value": "Metrics and calculations", "size": "13pt", "bold": True},
             "Store Sales Measures: Store Sales Price, Store Net Profit, Store Quantity Sold, Store Net Paid (with and without tax), Average List and Sales Price, Coupon Amount, Purchased Amount In Store, Row Counter. Web Sales Measures: Web Sales, Web Net Profit, Web Quantity Sold, Net Paid (four variants), Discount, Ship Cost, Wholesale Cost, Purchased Amount On Web, Row Counter. Customer Information: Store and Web customer counts.",
             "Calculated metrics (MDX): Total Net Profit, Total Quantity Sold and Store and Web Purchased Amount add the two channels; Avg Store Unit Net Profit and Average Web Unit Net Profit divide profit by quantity; Store Revenue Ratio by Product Class divides by the All product member; Store Sales Increase uses the previous member of the Sold Date hierarchy; Web Sales Increase uses ParallelPeriod on Sold Month of Year; Customer Count adds the two row counts.",
             {"value": "Shared package and pipeline", "size": "13pt", "bold": True},
             "Date, Product and Customer dimensions, the quantity, net paid and net profit base metrics and the four Total/Avg calculations come from sml-tpcds-common (package.yml pins the commit). The repository is registered on the AtScale CI/CD pipeline as tpcds-snowflake; a merge to main validates with sml-cli and deploys the catalog, and this report binds to the deployed cube through the XMLA endpoint in the Seed project's connection."],
            c3[1][0], CARD_Y, c3[1][1], ROW_H + 145),
    textbox([{"value": "Aggregates and performance", "size": "13pt", "bold": True},
             "The model declares one user-defined aggregate, 'customer sales' (Customer Demographics by Store Quantity Sold). Speculative aggregates and aggressive promotion are off in catalog.yml, so the engine builds system aggregates from the query log; the first query against a new cut goes to Snowflake and later ones hit the aggregate. The row-count limit for the aggregate store is ten million rows.",
             {"value": "Things to know when reading the numbers", "size": "13pt", "bold": True},
             "TPC-DS is a synthetic benchmark: distributions are deliberately uniform, net profit is negative and the last year (2003) is partial. Measures use 'unrelated dimensions handling: empty', so a store measure on a warehouse axis is blank rather than repeated. Customer Count and the row counters count fact rows, not distinct customers. Store Sales Price sums unit prices and Web Sales multiplies the extended price by quantity a second time, so neither is a revenue figure; compare channels with Net Paid or Purchased Amount, which are defined the same way on both facts."],
            c3[2][0], CARD_Y, c3[2][1], ROW_H + 145),
    visual("clusteredColumnChart", {"Category": drill(S_YEAR, S_QTR, S_MONTH), "Y": [proj(M("m_ws_net_paid_sum"), "Web net paid")]}, c2[0][0], ROW2_Y, c2[0][1], ROW_H,
           "Web net paid by Sold Date (drill to quarter and month)", sort(S_YEAR, "Ascending"), objects=LABELS_ON),
    visual("clusteredColumnChart", {"Category": drill(SH_YEAR, SH_QTR, SH_MONTH), "Y": [proj(M("m_ws_net_paid_sum"), "Web net paid")]}, c2[1][0], ROW2_Y, c2[1][1], ROW_H,
           "The same web net paid by Ship Date: the role-played copy of the Date dimension", sort(SH_YEAR, "Ascending"), objects=LABELS_ON),
])

# ---------- write the project ----------
# First run: scaffold the whole project from the Seed. Later runs: only definition/pages is
# regenerated, so files Power BI Desktop writes on save (.pbi/, theme, report.json) are kept.
# Pass --full to rebuild from scratch.
FULL = "--full" in sys.argv or not os.path.isdir(OUT)
if FULL and os.path.isdir(OUT):
    shutil.rmtree(OUT)
seed_rep = os.path.join(SEED, "TPCDS Seed.Report")
seed_sm = os.path.join(SEED, "TPCDS Seed.SemanticModel")

def scaffold():
    os.makedirs(OUT, exist_ok=True)
    pbip = rj(os.path.join(SEED, "TPCDS Seed.pbip"))
    pbip["artifacts"] = [{"report": {"path": NAME + ".Report"}}]
    w(os.path.join(OUT, NAME + ".pbip"), pbip)

    # SemanticModel: connection copied from the seed, new logicalId
    w(os.path.join(SM, "modelReference.json"), rj(os.path.join(seed_sm, "modelReference.json")))
    w(os.path.join(SM, "definition.pbism"), rj(os.path.join(seed_sm, "definition.pbism")))
    plat = rj(os.path.join(seed_sm, ".platform")); plat["metadata"]["displayName"] = NAME; plat["config"]["logicalId"] = str(uuid.uuid4())
    w(os.path.join(SM, ".platform"), plat)
    # Report: pbir, platform, report.json, version.json, theme
    pbir = rj(os.path.join(seed_rep, "definition.pbir")); pbir["datasetReference"] = {"byPath": {"path": "../" + NAME + ".SemanticModel"}}
    w(os.path.join(REP, "definition.pbir"), pbir)
    plat = rj(os.path.join(seed_rep, ".platform")); plat["metadata"]["displayName"] = NAME; plat["config"]["logicalId"] = str(uuid.uuid4())
    w(os.path.join(REP, ".platform"), plat)
    w(os.path.join(REP, "definition", "report.json"), rj(os.path.join(seed_rep, "definition", "report.json")))
    w(os.path.join(REP, "definition", "version.json"), rj(os.path.join(seed_rep, "definition", "version.json")))
    shutil.copytree(os.path.join(seed_rep, "StaticResources"), os.path.join(REP, "StaticResources"))


if FULL:
    scaffold()

# pages (always regenerated)
if os.path.isdir(PAGES):
    shutil.rmtree(PAGES)
for pid, p, vs in pages:
    w(os.path.join(PAGES, pid, "page.json"), p)
    for v in vs:
        w(os.path.join(PAGES, pid, "visuals", v["name"], "visual.json"), v)
w(os.path.join(PAGES, "pages.json"), {"$schema": S + "item/report/definition/pagesMetadata/1.1.0/schema.json", "pageOrder": [p[0] for p in pages], "activePageName": pages[0][0]})
print("wrote", "whole project" if FULL else "definition/pages only", "->", OUT)
print("pages:", [(p[1]["displayName"], len(p[2])) for p in pages])
