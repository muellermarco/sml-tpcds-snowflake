# Sigma reports on AtScale

Two Python scripts that build a Sigma workbook and a Sigma paginated report on the AtScale model `DemoModel`, as code.

Sigma can store a workbook or a report as a JSON document ("workbook as code") and create it through its REST API. These scripts write that JSON for the TPC-DS store sales content. Sigma reads the data live from the AtScale SQL interface, so every figure comes from the governed measures of the semantic model. The main readers are SE colleagues who want to rebuild or adapt the reports.

## Technologies

- Python 3, standard library only (`json`, `sys`)
- Sigma REST API v2
- AtScale SQL interface (PostgreSQL wire protocol) as the Sigma data source, catalog `TPCDS-MM-Snowflake_main`, model `DemoModel`
- `curl` for the API calls

## Files

| File | What it is |
|---|---|
| `build_tpcds_store_sales_workbook.py` | Writes the workbook JSON: KPIs, line and bar charts, a brand table, and a data page |
| `build_tpcds_store_sales_report.py` | Writes the paginated report JSON: two letter-size pages with header and footer panels |
| `tpcds_store_sales_workbook.contents.json` | Output of the workbook script |
| `tpcds_store_sales_report.contents.json` | Output of the report script |
| `tpcds_store_sales_report.pdf` | PDF export of the report |

## Before you start

- A Sigma connection to the AtScale SQL interface, with access to the catalog `TPCDS-MM-Snowflake_main`.
- A Sigma API client ID and secret in the environment variables `SIGMA_CLIENT_ID` and `SIGMA_CLIENT_SECRET`.
- The ID of the Sigma folder for the new document.
- The API host of your Sigma organization (`<sigma-api-host>` below). It depends on the cloud that hosts the organization. An organization on AWS uses the `aws-api` host, not the `api` host. See the Sigma API documentation.

**Caution:** both scripts contain a fixed Sigma `connectionId` (constant `CONN`). Replace it with the ID of your own connection before you run them.

## Build the workbook

1. Get an API token:

   ```sh
   curl -s -X POST https://<sigma-api-host>/v2/auth/token \
     -d grant_type=client_credentials \
     -d client_id=$SIGMA_CLIENT_ID -d client_secret=$SIGMA_CLIENT_SECRET
   ```

   Result: the response contains `access_token`.
2. Run `python3 build_tpcds_store_sales_workbook.py workbook.json`.
   Result: `workbook.json` contains only `{"contents": ...}`.
3. Add `folderId` and `name` to the top level of `workbook.json`.
4. To check the structure first, add `"dryRun": true` and send `POST /v2/workbooks` with the file as body.
   Result: Sigma accepts the document and creates nothing.
5. Remove `dryRun` and send `POST /v2/workbooks` again.
   Result: the response contains the new `workbookId`.
6. To update an existing workbook, send `PUT /v2/workbooks/{workbookId}/contents` with `{"contents": ...}`.
7. Send `POST /v2/workbooks/{workbookId}/export` with `{"elementId": "<id>", "format": {"type": "csv"}, "rowLimit": 100}`.
8. Send `GET /v2/query/{queryId}/download` with the `queryId` from step 7.
   Result: the CSV contains data. HTTP 204 means that the query still runs. Send the request again.

The dry run checks only the structure and that the source table exists. It does not check formulas. Steps 7 and 8 prove that the AtScale columns resolve.

## Build the paginated report

The report script takes three arguments: `<mode> <footer> [out.json]`.

| Argument | Values | Effect |
|---|---|---|
| `mode` | `dry` or `real` | `dry` adds `"dryRun": true` to the body |
| `footer` | `panel` or any other value | `panel` puts the page number in a footer panel. Any other value puts it on each page. |
| `out.json` | File path | Output file. Without it, the script writes to standard output. |

1. Get an API token, as in [Build the workbook](#build-the-workbook), step 1.
2. Run `python3 build_tpcds_store_sales_report.py dry panel report.json`.
3. In `report.json`, replace the all-zero `folderId` with your folder ID.
4. Send `POST /v2/reports` with `report.json` as body.
   Result: Sigma accepts the document and creates nothing.
5. Run `python3 build_tpcds_store_sales_report.py real panel report.json`.
6. Replace the all-zero `folderId` again.
7. Send `POST /v2/reports` with `report.json` as body.
   Result: the response contains the new report ID.
8. To update an existing report, send `PUT /v2/reports/{reportId}/contents` with `{"contents": ...}`.
9. Send `POST /v2/reports/{reportId}/export` with `{"format": {"type": "pdf", "layout": "portrait"}}`.
10. Send `GET /v2/query/{queryId}/download` with the `queryId` from step 9.
    Result: you get a PDF like `tpcds_store_sales_report.pdf`.

The report layout uses pixels on a letter-size page (816 x 1056). Header and footer are `panels`. The page number is a text element with the tokens `{{CurrentPageNumber()}}` and `{{TotalPageCount()}}`.

## Known limits on AtScale sources

- The source path is `["<AtScale catalog>", "<model>"]` on the connection, for example `["TPCDS-MM-Snowflake_main", "DemoModel"]`.
- Prefix every column reference with the model name: `[DemoModel/m_ss_net_paid_sum]` or `Sum([DemoModel/m_ss_net_paid_sum])`. A bare `[m_ss_net_paid_sum]` or a friendly name such as `[M Ss Net Paid Sum]` fails.
- Source each element directly from the warehouse table. Child elements of a table element did not resolve the AtScale columns.
- An x-axis `sort` on a chart and a `top-n` filter both fail on AtScale, because they need ranking or window SQL. Use table `sorts` and group-by instead.
- Keep the grain coarse. A full-grain query on `store_sales` (about 28.8 billion rows) exceeds the 120-second timeout of the Sigma connection.
