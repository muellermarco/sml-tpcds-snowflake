import json, sys
CONN="66baa26c-c31a-4bf2-bd09-94801ec60ef6"; PATH=["TPCDS-MM-Snowflake_main","DemoModel"]; M="DemoModel"
WH={"connectionId":CONN,"kind":"warehouse-table","path":PATH}
def col(i,f,n=None):
    d={"id":i,"formula":f}
    if n: d["name"]=n
    return d
def ref(c): return f"[{M}/{c}]"
def S_(c): return f"Sum([{M}/{c}])"
dims=["Sold Calendar Year","d_store_state","I Category"]  # kept coarse: full grain on 28.8B store_sales rows exceeds the 120s connection timeout
meas=["m_ss_net_paid_sum","m_ss_net_profit_sum","m_ss_quantity_sum","m_SS Row Counter_sum"]
base_cols=[col(f"b{k:02d}",ref(c)) for k,c in enumerate(dims)]+[col(f"m{k:02d}",S_(c),n) for k,(c,n) in enumerate(zip(meas,["Net Paid","Net Profit","Units","Transactions"]))]
base={"id":"tblBaseSS01","kind":"table","title":"Store Sales by Year / State / Category (AtScale DemoModel)","source":WH,"columns":base_cols,"order":[c["id"] for c in base_cols],"groupBy":[{"columnId":"b00"},{"columnId":"b01"},{"columnId":"b02"}],"sorts":[{"columnId":"b00","direction":"ascending"}]}
header={"id":"txtHeader01","kind":"text","body":"# TPC-DS Store Sales Overview\nLive on the AtScale semantic layer · catalog **TPCDS-MM-Snowflake** · model **DemoModel** · connection *AtScale CICD PROD* (Postgres wire)"}
def kpi(i,title,m):
    return {"id":i,"kind":"kpi-chart","title":title,"source":WH,"columns":[col(i+"v",S_(m),title)],"value":{"columnId":i+"v"}}
k1=kpi("kpiNetPaid1","Net Paid (Store)","m_ss_net_paid_sum")
k2=kpi("kpiProfit01","Net Profit (Store)","m_ss_net_profit_sum")
k3=kpi("kpiQty0001","Units Sold (Store)","m_ss_quantity_sum")
k4=kpi("kpiRows0001","Store Transactions","m_SS Row Counter_sum")
line={"id":"lineMonth01","kind":"line-chart","title":"Store Net Paid by Month","source":WH,
      "columns":[col("lmx",ref("Sold Calendar Month"),"Month"),col("lmy",S_("m_ss_net_paid_sum"),"Net Paid")],
      "xAxis":{"columnId":"lmx"},"yAxis":{"columnIds":["lmy"]}}
barState={"id":"barState001","kind":"bar-chart","title":"Net Paid by Store State","source":WH,
      "columns":[col("bsx",ref("d_store_state"),"Store State"),col("bsy",S_("m_ss_net_paid_sum"),"Net Paid")],
      "xAxis":{"columnId":"bsx"},"yAxis":{"columnIds":["bsy"]}}
barCat={"id":"barCateg001","kind":"bar-chart","title":"Net Profit by Product Category","source":WH,
      "columns":[col("bcx",ref("I Category"),"Category"),col("bcy",S_("m_ss_net_profit_sum"),"Net Profit")],
      "xAxis":{"columnId":"bcx"},"yAxis":{"columnIds":["bcy"]}}
top={"id":"tblBrands01","kind":"table","title":"Brands by Net Paid (highest first)","source":WH,
      "columns":[col("tbb",ref("Product Brand"),"Brand"),col("tbc",ref("I Category"),"Category"),col("tbp",S_("m_ss_net_paid_sum"),"Net Paid"),col("tbq",S_("m_ss_quantity_sum"),"Units"),col("tbn",S_("m_ss_net_profit_sum"),"Net Profit")],
      "order":["tbb","tbc","tbp","tbq","tbn"],"groupBy":[{"columnId":"tbb"},{"columnId":"tbc"}],
      "sorts":[{"columnId":"tbp","direction":"descending"}]}
layout='''<?xml version="1.0" encoding="utf-8"?>
<Page type="grid" gridTemplateColumns="repeat(24, 1fr)" gridTemplateRows="auto" id="pgOverview1">
  <Element elementId="txtHeader01" gridColumn="1 / 25" gridRow="1 / 4"/>
  <Element elementId="kpiNetPaid1" gridColumn="1 / 7" gridRow="4 / 10"/>
  <Element elementId="kpiProfit01" gridColumn="7 / 13" gridRow="4 / 10"/>
  <Element elementId="kpiQty0001" gridColumn="13 / 19" gridRow="4 / 10"/>
  <Element elementId="kpiRows0001" gridColumn="19 / 25" gridRow="4 / 10"/>
  <Element elementId="lineMonth01" gridColumn="1 / 25" gridRow="10 / 24"/>
  <Element elementId="barState001" gridColumn="1 / 13" gridRow="24 / 38"/>
  <Element elementId="barCateg001" gridColumn="13 / 25" gridRow="24 / 38"/>
  <Element elementId="tblBrands01" gridColumn="1 / 25" gridRow="38 / 54"/>
</Page>
<Page type="grid" gridTemplateColumns="repeat(24, 1fr)" gridTemplateRows="auto" id="pgData00001">
  <Element elementId="tblBaseSS01" gridColumn="1 / 25" gridRow="1 / 41"/>
</Page>'''
contents={"schemaVersion":1,"kind":"workbook","pages":[{"id":"pgOverview1","name":"Overview"},{"id":"pgData00001","name":"Data"}],
          "elements":[header,k1,k2,k3,k4,line,barState,barCat,top,base],"layout":layout}
json.dump({"contents":contents},open(sys.argv[1],"w"),indent=1)
