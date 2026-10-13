import json, sys
CONN="66baa26c-c31a-4bf2-bd09-94801ec60ef6"; PATH=["TPCDS-MM-Snowflake_main","DemoModel"]; M="DemoModel"
WH={"connectionId":CONN,"kind":"warehouse-table","path":PATH}
def col(i,f,n=None):
    d={"id":i,"formula":f}
    if n: d["name"]=n
    return d
R=lambda c:f"[{M}/{c}]"; S_=lambda c:f"Sum([{M}/{c}])"
W,Hh=816,1056
els=[]; lay1=[]; lay2=[]
els.append({"id":"rptTitle001","kind":"text","body":"## TPC-DS Store Sales Report"})
els.append({"id":"rptIntro001","kind":"text","body":"Store channel performance for the TPC-DS benchmark data, served live by the **AtScale semantic layer** (catalog TPCDS-MM-Snowflake, model DemoModel) over the *AtScale CICD PROD* connection. All figures are governed measures: Net Paid, Net Profit, Units and Transactions from the store_sales fact."})
lay1.append(("rptIntro001",24,20,768,70))
def kpi(i,title,m):
    els.append({"id":i,"kind":"kpi-chart","title":title,"source":WH,"columns":[col(i+"v",S_(m),title)],"value":{"columnId":i+"v"}})
for k,(i,t,m) in enumerate([("rKpiNetPaid","Net Paid (Store)","m_ss_net_paid_sum"),("rKpiProfit1","Net Profit (Store)","m_ss_net_profit_sum"),("rKpiUnits01","Units Sold","m_ss_quantity_sum"),("rKpiTrans01","Transactions","m_SS Row Counter_sum")]):
    kpi(i,t,m); lay1.append((i,24+k*192,100,180,110))
els.append({"id":"rLineMonth1","kind":"line-chart","title":"Store Net Paid by Month","source":WH,
            "columns":[col("rlx",R("Sold Calendar Month"),"Month"),col("rly",S_("m_ss_net_paid_sum"),"Net Paid")],"xAxis":{"columnId":"rlx"},"yAxis":{"columnIds":["rly"]}})
lay1.append(("rLineMonth1",24,225,768,280))
els.append({"id":"rBarState01","kind":"bar-chart","title":"Net Paid by Store State","source":WH,
            "columns":[col("rsx",R("d_store_state"),"Store State"),col("rsy",S_("m_ss_net_paid_sum"),"Net Paid")],"xAxis":{"columnId":"rsx"},"yAxis":{"columnIds":["rsy"]}})
lay1.append(("rBarState01",24,515,768,390))
els.append({"id":"rBarCateg01","kind":"bar-chart","title":"Net Profit by Product Category","source":WH,
            "columns":[col("rcx",R("I Category"),"Category"),col("rcy",S_("m_ss_net_profit_sum"),"Net Profit")],"xAxis":{"columnId":"rcx"},"yAxis":{"columnIds":["rcy"]}})
lay2.append(("rBarCateg01",24,20,768,330))
els.append({"id":"rTblBrands1","kind":"table","title":"Brands by Net Paid (highest first)","source":WH,
            "columns":[col("rtb",R("Product Brand"),"Brand"),col("rtc",R("I Category"),"Category"),col("rtp",S_("m_ss_net_paid_sum"),"Net Paid"),col("rtq",S_("m_ss_quantity_sum"),"Units"),col("rtn",S_("m_ss_net_profit_sum"),"Net Profit")],
            "order":["rtb","rtc","rtp","rtq","rtn"],"groupBy":[{"columnId":"rtb","sort":{"by":"rtp","direction":"descending"}},{"columnId":"rtc","sort":{"by":"rtp","direction":"descending"}}],"sorts":[{"columnId":"rtp","direction":"descending"}]})
els.append({"id":"rTblTitle01","kind":"text","body":"### Brands by Net Paid (highest first)"})
lay2.append(("rTblTitle01",24,360,768,30)); lay2.append(("rTblBrands1",24,395,768,530))
els.append({"id":"rptPageNum1","kind":"text","body":"<p class=\"p-small\">Page {{CurrentPageNumber()}} of {{TotalPageCount()}} · Source: AtScale semantic layer, TPCDS-MM-Snowflake / DemoModel</p>"})
USE_FOOTER_PANEL = (sys.argv[2]=="panel") if len(sys.argv)>2 else True
def L(items): return "".join(f'  <Element elementId="{e}" x="{x}" y="{y}" width="{w}" height="{h}"/>\n' for e,x,y,w,h in items)
panels=[{"id":"pnlHeader01","type":"header","title":"Header","config":{"height":60,"backgroundColor":"#DCE6F2"},"pages":["rpgPage0001","rpgPage0002"]}]
if USE_FOOTER_PANEL: panels.append({"id":"pnlFooter01","type":"footer","title":"Footer","config":{"height":40,"backgroundColor":"#FFFFFF"},"pages":["rpgPage0001","rpgPage0002"]})
else:
    lay1.append(("rptPageNum1",24,1010,768,30)); lay2.append(("rptPageNum1",24,1010,768,30))
layout=('<?xml version="1.0" encoding="utf-8"?>\n'
        f'<Page id="rpgPage0001">\n{L(lay1)}</Page>\n<Page id="rpgPage0002">\n{L(lay2)}</Page>\n'
        f'<Panel id="pnlHeader01" type="header">\n  <Element elementId="rptTitle001" x="24" y="12" width="500" height="36"/>\n</Panel>\n'
        + (f'<Panel id="pnlFooter01" type="footer">\n  <Element elementId="rptPageNum1" x="24" y="8" width="768" height="26"/>\n</Panel>\n' if USE_FOOTER_PANEL else ''))
contents={"schemaVersion":1,"kind":"report","pages":[{"id":"rpgPage0001","name":"Summary"},{"id":"rpgPage0002","name":"Categories and Brands"}],
          "panels":panels,"config":{"margin":0,"pageWidth":W,"pageHeight":Hh},"elements":els,"layout":layout}
body={"folderId":"00000000-0000-0000-0000-000000000000","name":"TPC-DS Store Sales Report (AtScale)","description":"Paginated Sigma report on the AtScale TPC-DS DemoModel, generated from code.","contents":contents}
if sys.argv[1]=="dry": body["dryRun"]=True
json.dump(body,open(sys.argv[3] if len(sys.argv)>3 else "/dev/stdout","w"),indent=1)
