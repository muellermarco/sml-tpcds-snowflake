# Sigma reports on AtScale (generated from code)

`build_tpcds_store_sales_workbook.py <out.json>` writes the Sigma "workbook as code"
representation for **TPC-DS Store Sales (AtScale)**, built on the Sigma connection
*AtScale CICD PROD* (Postgres wire to prod.atscale-se-demo.com) and the AtScale model
`TPCDS-MM-Snowflake_main.DemoModel`.

Workbook: https://app.sigmacomputing.com/atscale-partner/workbook/2hy7dDYPwiJ4cU7V7Ke5sX
(workbookId 4b03b3c6-1152-4eb0-94a9-78a0db4f6c67, workspace "AtScale").

## API usage (Sigma)
Token (org is on AWS, so the host is aws-api, not api):
    curl -s -X POST https://aws-api.sigmacomputing.com/v2/auth/token \
      -d grant_type=client_credentials -d client_id=$SIGMA_CLIENT_ID -d client_secret=$SIGMA_CLIENT_SECRET
Validate without creating:  POST /v2/workbooks  {folderId, name, dryRun:true, contents}
Create:                     POST /v2/workbooks  {folderId, name, contents}
Replace contents in place:  PUT  /v2/workbooks/{workbookId}/contents  {contents}
Run an element's query:     POST /v2/workbooks/{id}/export {elementId, format:{type:"csv"}, rowLimit}
                            then GET /v2/query/{queryId}/download (204 = still running)

## Rules learned for AtScale sources
- Source path is ["<AtScale catalog>", "<model>"] on the connection, e.g. ["TPCDS-MM-Snowflake_main","DemoModel"].
- Column references must be prefixed with the model name: `[DemoModel/m_ss_net_paid_sum]`,
  `Sum([DemoModel/m_ss_net_paid_sum])`. Bare `[m_ss_net_paid_sum]` or friendly `[M Ss Net Paid Sum]` fail.
- Source each element directly from the warehouse table; child elements of a table element
  could not resolve the AtScale columns.
- An x-axis `sort` on charts and a `top-n` filter both fail on AtScale (ranking/window SQL).
  Use table `sorts` (works) and group-by instead.
- The dry run validates structure and that the warehouse table exists, not formulas; verify with export.

## Paginated report (Sigma "report" document type)
`build_tpcds_store_sales_report.py real panel <out.json>` writes the representation for
**TPC-DS Store Sales Report (AtScale)**: https://app.sigmacomputing.com/atscale-partner/report/6wYYlR0OODdoMpEnzqmqAn
(reportId d69ee540-52f0-4ef4-8dbf-312054fefc87). Same column rules as the workbook.
Endpoints: POST /v2/reports {folderId,name,dryRun?,contents}; PUT /v2/reports/{id}/contents;
export is PDF only: POST /v2/reports/{id}/export {"format":{"type":"pdf","layout":"portrait"}} then GET /v2/query/{queryId}/download.
Layout is pixel-based (816x1056 letter), header/footer are `panels`; page number is a text element with
{{CurrentPageNumber()}} / {{TotalPageCount()}} tokens.
