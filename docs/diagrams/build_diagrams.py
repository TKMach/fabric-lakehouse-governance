import subprocess, os
os.makedirs("../img", exist_ok=True)

FONT = "Inter"
NAVY = "#1F3A5F"
BASE = f'''
  graph [fontname="{FONT}", fontsize=11, bgcolor="white", pad=0.25, nodesep=0.35, ranksep=0.45, newrank=true];
  node  [fontname="{FONT}", fontsize=10, shape=box, style="rounded,filled", fillcolor="#FFFFFF", color="#5B6B7F", penwidth=1.1, margin="0.14,0.07"];
  edge  [fontname="{FONT}", fontsize=8.5, color="#5B6B7F", arrowsize=0.7, fontcolor="#44546A"];
'''
SRC = 'fillcolor="#E6EEF7", color="#1F3A5F"'
ORC = 'fillcolor="#E4F2F2", color="#2A7F8E"'
BRZ = 'fillcolor="#F3DFCB", color="#A0663A"'
SLV = 'fillcolor="#E8EBEF", color="#7D8792"'
GLD = 'fillcolor="#F8E9B0", color="#B8902A"'
SRV = 'fillcolor="#EDE7F6", color="#5E4B8B"'
SEC = 'fillcolor="#FFF4E5", color="#C77700"'
BAD = 'fillcolor="#FDECEC", color="#B3261E", style="rounded,filled,dashed", fontcolor="#7A1C16"'
RET = 'fillcolor="#F3F3F3", color="#9E9E9E", style="rounded,filled,dashed", fontcolor="#757575"'

def clus(name, label, fill, border, body):
    return f'''subgraph cluster_{name} {{ label=<<b>{label}</b>>; labeljust=l; style="rounded,filled"; fillcolor="{fill}"; color="{border}"; fontcolor="{border}"; fontsize=10.5; margin=10;
{body}
}}'''

D = {}

# 1. Enterprise reference architecture
D["architecture"] = f'''digraph G {{ rankdir=TB; {BASE} ranksep=0.5;
{clus("src","SOURCE SYSTEMS","#F7F9FC",NAVY, f"""
 mne [label=<<b>M&amp;E platform</b><br/><font point-size="8.5">direct API · cohorts A/B</font>>, {SRC}];
 ftp [label=<<b>Programme Portal</b><br/><font point-size="8.5">Azure SQL · OpsDB</font>>, {SRC}];
 zs [label=<<b>Zoho Survey</b><br/><font point-size="8.5">API · survey responses</font>>, {SRC}];
 crm [label=<<b>Zoho CRM</b><br/><font point-size="8.5">API · contacts</font>>, {SRC}];
""")}
{clus("orc","FABRIC DATA FACTORY","#F3FAFA","#2A7F8E", f"""
 p1 [label=<pl_mne_ingest>, {ORC}];
 p2 [label=<pl_portal_metadata_copy<br/><font point-size="8">Lookup → ForEach → Copy</font>>, {ORC}];
 p3 [label=<pl_survey_api_prod<br/><font point-size="8">scheduled</font>>, {ORC}];
 p4 [label=<CRM integration<br/><font point-size="8">API / automation</font>>, {ORC}];
""")}
{clus("lh","LAKEHOUSE · lh_analytics (Delta)","#FBFBF8","#8A6D1F", f"""
 b [label=<<b>BRONZE</b><br/><font point-size="8.5">raw landing<br/>source provenance</font>>, {BRZ}, width=1.3];
 s [label=<<b>SILVER</b><br/><font point-size="8.5">typed · conformed<br/>identity resolved</font>>, {SLV}, width=1.3];
 g [label=<<b>GOLD</b><br/><font point-size="8.5">reporting grain<br/>business rules</font>>, {GLD}, width=1.3];
 b -> s -> g [penwidth=1.6, color="#8A6D1F"];
""")}
{clus("srv","SERVING &amp; CONSUMPTION","#F8F6FC","#5E4B8B", f"""
 sm [label=<<b>Semantic models</b><br/><font point-size="8.5">governed DAX measures</font>>, {SRV}];
 xl [label=<Programme Excel extracts<br/><font point-size="8">Power Query</font>>, {SRV}];
 imp [label=<Impact Dashboard>, {SRV}];
 pbi [label=<Programme Power BI<br/><font point-size="8">in development</font>>, {SRV}];
 sm -> imp; sm -> pbi;
""")}
 kv [label=<<b>Azure Key Vault</b><br/><font point-size="8.5">API secrets</font>>, {SEC}];
 mne -> p1; ftp -> p2; zs -> p3; crm -> p4;
 p1 -> b; p2 -> b; p3 -> b; p4 -> b;
 g -> sm; g -> xl;
 kv -> p3 [style=dashed, color="#C77700", label=" secret ref", constraint=false];
 {{rank=same; mne; ftp; zs; crm; mne -> ftp -> zs -> crm [style=invis];}}
 {{rank=same; p1; p2; p3; p4; kv; p1 -> p2 -> p3 -> kv -> p4 [style=invis];}}
 {{rank=same; b; s; g;}}
 {{rank=same; imp; pbi; xl; pbi -> imp -> xl [style=invis];}}
}}'''

# 2. Programme Portal
D["portal_pipeline"] = f'''digraph G {{ rankdir=TB; {BASE}
 app [label=<<b>Programme Portal</b> (operational app)<br/><font point-size="8.5">programme · business · finance · jobs · social &amp; sustainability KPIs</font>>, {SRC}];
 sql [label=<<b>Azure SQL · OpsDB</b><br/><font point-size="8.5">base tables · legacy.vw_financials · configured views</font>>, {SRC}];
{clus("pl","Fabric pipeline · pl_portal_metadata_copy","#F3FAFA","#2A7F8E", f"""
 lk [label=<Lookup<br/><font point-size="8.5">ops.ingestion_control</font>>, {ORC}];
 fe [label=<ForEach1<br/><font point-size="8.5">one iteration per entity</font>>, {ORC}];
 cp [label=<Copy activity<br/><font point-size="8.5">source = @item().query</font>>, {ORC}];
 lk -> fe -> cp;
""")}
 br [label=<<b>BRONZE</b> · landing<br/><font point-size="8.5">bronze.legacy_financials · portal_businesses<br/>portal_business_programmes · participation metadata</font>>, {BRZ}];
 nb [label=<<b>SILVER</b> · notebooks<br/><font point-size="8.5">standardise · business_guid joins<br/>grain = business × programme × month</font>>, {SLV}];
 gd [label=<<b>GOLD</b><br/><font point-size="8.5">sustainability_monthly<br/>programme extracts (fin · jobs · SROI)</font>>, {GLD}];
 xl [label=<Programme Excel<br/><font point-size="8">validated · in use</font>>, {SRV}];
 pb [label=<Power BI dashboards<br/><font point-size="8">separate delivery stream</font>>, {SRV}];
 q [label=<<b>NOT AUTHORITATIVE</b><br/><font point-size="8.5">silver_legacy_financials · fact_financials_v0 (stale)<br/>legacy_financials_enriched (dup. business-months)</font>>, {BAD}];
 app -> sql; sql -> lk [label="  query metadata"]; cp -> br; br -> nb -> gd; gd -> xl; gd -> pb;
 br -> q [style=dashed, color="#B3261E", arrowhead=tee, label="  do not promote"];
 {{rank=same; nb; q;}}
}}'''

# 3. M&E platform
D["mne_pipeline"] = f'''digraph G {{ rankdir=TB; {BASE}
 api [label=<<b>M&amp;E platform API</b> / source reports<br/><font point-size="8.5">projNum · report_Number · rptPrdDesc · financial &amp; jobs fields</font>>, {SRC}];
 orc [label=<pl_mne_ingest<br/><font point-size="8.5">extraction workflow</font>>, {ORC}];
 subgraph cluster_b {{ label=<<b>BRONZE</b>>; style="rounded,filled"; fillcolor="#FBF3EA"; color="#A0663A"; fontcolor="#A0663A"; fontsize=10;
  rf [label=<bronze.mne_financials_raw>, {BRZ}];
  rj [label=<bronze.mne_jobs_raw>, {BRZ}]; }}
 sv [label=<<b>SILVER</b> · conform<br/><font point-size="8.5">parse "Y14 M9" → Year 2026, Month 9 (label retained)<br/>projNum → business_guid · match_status · participation_status<br/>latest accepted revision by report_Number</font>>, {SLV}];
 subgraph cluster_g {{ label=<<b>GOLD</b>>; style="rounded,filled"; fillcolor="#FCF6DC"; color="#B8902A"; fontcolor="#8A6D1F"; fontsize=10;
  gf [label=<fact_financials_monthly<br/><font point-size="8">NULL preserved</font>>, {GLD}];
  gj [label=<fact_jobs_monthly<br/><font point-size="8">6 categories · NULL → 0</font>>, {GLD}]; }}
 sm [label=<Semantic model · governed DAX<br/><font point-size="8.5">programme &amp; month slicers</font>>, {SRV}];
 dash [label=<<b>Impact Dashboard</b><br/><font point-size="8.5">turnover · expenses · net income · jobs</font>>, {SRV}];
 leg [label=<<b>Legacy path</b><br/><font point-size="8.5">legacy.vw_financials (Programme Portal)<br/>incomplete cohort coverage</font>>, {BAD}];
 api -> orc; orc -> rf; orc -> rj; rf -> sv; rj -> sv; sv -> gf; sv -> gj; gf -> sm; gj -> sm; sm -> dash;
 leg -> sm [style=dashed, color="#B3261E", arrowhead=tee, label="  never union\\n  without key/period/dup controls"];
 {{rank=same; sv; leg;}}
}}'''

# 4. Zoho Survey
D["survey_pipeline"] = f'''digraph G {{ rankdir=TB; {BASE} ranksep=0.4;
{clus("poc","RETIRED · proof of concept (not the acceptance baseline)","#FAFAFA","#9E9E9E", f"""
 r1 [label=<Zoho Survey>, {RET}]; r2 [label=<Pipedream webhook>, {RET}];
 r3 [label=<pl_survey_dev / nb_survey_dev>, {RET}]; r4 [label=<survey_responses_poc>, {RET}];
 r1 -> r2 -> r3 -> r4 [color="#9E9E9E", style=dashed]; {{rank=same; r1; r2; r3; r4;}}
""")}
{clus("prd","PRODUCTION · pl_survey_api_prod (scheduled Fabric pipeline)","#F3FAFA","#2A7F8E", f"""
 t [label=<Schedule trigger>, {ORC}];
 kv [label=<<b>Azure Key Vault</b><br/><font point-size="8">API credentials</font>>, {SEC}];
 api [label=<<b>Zoho Survey API</b><br/><font point-size="8.5">Survey responses</font>>, {SRC}];
 b [label=<<b>BRONZE</b><br/><font point-size="8.5">raw responses + source metadata</font>>, {BRZ}];
 s [label=<<b>SILVER</b><br/><font point-size="8.5">schema map · types · response identity<br/>Delta-versioned · replay-safe</font>>, {SLV}];
 g [label=<<b>GOLD</b><br/><font point-size="8.5">reporting grain · dedup · business fields<br/>Delta-versioned</font>>, {GLD}];
 rep [label=<Survey reporting<br/><font point-size="8">Power BI in development</font>>, {SRV}];
 log [label=<Run log<br/><font point-size="8">status · exceptions</font>>, fillcolor="#FFFFFF", color="#5B6B7F", style="rounded,filled,dashed"];
 t -> kv [label=" get secret"]; kv -> api [label=" authenticate"]; api -> b -> s -> g -> rep;
 {{rank=same; t; kv; api;}} {{rank=same; b; s; g;}} {{rank=same; rep; log;}}
 g -> log [style=dotted, arrowhead=none];
""")}
 r2 -> kv [style=invis];
}}'''

# 5. CRM
D["crm_pipeline"] = f'''digraph G {{ rankdir=TB; {BASE}
 forms [label=<Zoho Forms<br/><font point-size="8.5">communication preferences</font>>, {SRC}];
 crm [label=<<b>Zoho CRM</b><br/><font point-size="8.5">contacts · programme links · consent flags</font>>, {SRC}];
 orc [label=<Authorised API integration / orchestration>, {ORC}];
 b [label=<<b>BRONZE</b><br/><font point-size="8.5">raw CRM records · source contact IDs · change metadata</font>>, {BRZ}];
 subgraph cluster_s {{ label=<<b>SILVER</b> · two distinct grains>; style="rounded,filled"; fillcolor="#F4F5F7"; color="#7D8792"; fontcolor="#5B6B7F"; fontsize=10;
  c [label=<<b>Contact</b><br/><font point-size="8.5">1 row per canonical contact ID<br/>0 duplicates</font>>, {SLV}];
  a [label=<<b>Programme assignment</b><br/><font point-size="8.5">contact × programme</font>>, {SLV}];
  c -> a [arrowhead=crow, label=" 1 : N"]; }}
 rules [label=<Match &amp; dedupe · source precedence · referential checks · <b>opt-out authoritative</b>>, fillcolor="#FFFFFF", color="#5B6B7F", style="rounded,filled,dashed"];
 g [label=<<b>GOLD</b> · governed CRM datasets>, {GLD}];
 r1 [label=<Alumni / programme reporting>, {SRV}];
 r2 [label=<Communication workflows<br/><font point-size="8">opted-out contacts excluded</font>>, {SRV}];
 forms -> crm [label=" mapping + automations"]; crm -> orc -> b; b -> c; b -> a; c -> rules [style=dashed]; a -> rules [style=dashed]; rules -> g; g -> r1; g -> r2;
}}'''

# 6. Identity / conformed keys
D["identity_model"] = f'''digraph G {{ rankdir=LR; {BASE} nodesep=0.25;
 node [shape=plain, style="", fillcolor="", color=""];
 hub [label=<<table border="1" cellborder="0" cellspacing="0" cellpadding="5" color="{NAVY}" bgcolor="#E6EEF7">
   <tr><td bgcolor="{NAVY}"><font color="white"><b>business_guid</b></font></td></tr>
   <tr><td align="left"><font point-size="8.5">canonical business key</font></td></tr></table>>];
 ftp [label=<<table border="1" cellborder="0" cellspacing="0" cellpadding="4" color="#5B6B7F">
   <tr><td bgcolor="#E8EBEF"><b>portal_businesses</b></td></tr><tr><td align="left"><font point-size="8.5">business_guid (PK)</font></td></tr></table>>];
 bp [label=<<table border="1" cellborder="0" cellspacing="0" cellpadding="4" color="#5B6B7F">
   <tr><td bgcolor="#E8EBEF"><b>portal_business_programmes</b></td></tr><tr><td align="left"><font point-size="8.5">business_guid · programme_id<br/>participation_status · exit date</font></td></tr></table>>];
 px [label=<<table border="1" cellborder="0" cellspacing="0" cellpadding="4" color="#B8902A">
   <tr><td bgcolor="#F8E9B0"><b>M&amp;E Gold</b></td></tr><tr><td align="left"><font point-size="8.5">projNum → business_guid<br/>report_Number · Year/Month<br/>match_status</font></td></tr></table>>];
 ft [label=<<table border="1" cellborder="0" cellspacing="0" cellpadding="4" color="#B8902A">
   <tr><td bgcolor="#F8E9B0"><b>Portal Gold</b></td></tr><tr><td align="left"><font point-size="8.5">business_guid · programme_id<br/>business-month grain</font></td></tr></table>>];
 cr [label=<<table border="1" cellborder="0" cellspacing="0" cellpadding="4" color="#B8902A">
   <tr><td bgcolor="#F8E9B0"><b>CRM Gold</b></td></tr><tr><td align="left"><font point-size="8.5">canonical contact ID<br/>CRM IDs retained</font></td></tr></table>>];
 ys [label=<<table border="1" cellborder="0" cellspacing="0" cellpadding="4" color="#B8902A">
   <tr><td bgcolor="#F8E9B0"><b>Survey Gold</b></td></tr><tr><td align="left"><font point-size="8.5">survey + response IDs<br/>enterprise identifiers</font></td></tr></table>>];
 ftp -> hub [dir=none]; bp -> hub [arrowhead=crow, dir=back, label=" N"];
 hub -> px [label="resolve"]; hub -> ft; hub -> cr [style=dashed, label="where linked"]; hub -> ys [style=dashed, label="where linked"];
}}'''

# 7. Triage flow
D["run_triage"] = f'''digraph G {{ rankdir=TB; {BASE} ranksep=0.35;
 node [fontsize=9.5];
 st [label=<Scheduled run completes>, {ORC}];
 q1 [label=<Run succeeded?>, shape=diamond, style=filled, fillcolor="#FFFFFF", color="#5B6B7F", margin="0.05,0.03"];
 fail [label=<<b>Classify failure</b><br/><font point-size="8.5">credential/API · source availability · schema<br/>transformation · DQ · Fabric capacity</font>>, {BAD}, style="rounded,filled"];
 rr [label=<SOP-02 safe rerun<br/><font point-size="8.5">check idempotency (append/overwrite/merge)</font>>, {ORC}];
 q2 [label=<Latest business period<br/>loaded?>, shape=diamond, style=filled, fillcolor="#FFFFFF", color="#5B6B7F", margin="0.05,0.03"];
 src [label=<Investigate <b>source</b> coverage<br/><font point-size="8.5">SOP-05 · compare source preview vs landing</font>>, {SEC}];
 q3 [label=<Counts, keys &amp; sums<br/>reconcile?>, shape=diamond, style=filled, fillcolor="#FFFFFF", color="#5B6B7F", margin="0.05,0.03"];
 ex [label=<<b>SOP-04 exception triage</b><br/><font point-size="8.5">no record · all-NULL · partial<br/>genuine zero · exited / not required</font>>, {SEC}];
 ok [label=<<b>Fresh &amp; reconciled</b><br/><font point-size="8.5">log run ID · Delta version · evidence</font>>, {GLD}];
 st -> q1; q1 -> fail [label=" no"]; fail -> rr; rr -> q1 [style=dashed];
 q1 -> q2 [label=" yes"]; q2 -> src [label=" no"]; q2 -> q3 [label=" yes"];
 q3 -> ex [label=" no"]; q3 -> ok [label=" yes"]; ex -> ok [style=dashed, label=" register + owner"];
}}'''

# 8. DQ gate / publish
D["dq_gate"] = f'''digraph G {{ rankdir=LR; {BASE}
 br [label=<<b>BRONZE</b><br/><font point-size="8.5">landed + lineage</font>>, {BRZ}];
 st [label=<<b>silver_staging / gold_staging</b><br/><font point-size="8.5">same SQL as local tests</font>>, {SLV}];
 dq [label=<<b>DQ gate</b><br/><font point-size="8.5">uniqueness · reconciliation<br/>freshness · completeness</font>>, shape=diamond, style=filled, fillcolor="#FFFFFF", color="{NAVY}", margin="0.02,0.02"];
 pub [label=<<b>GOLD (reporting)</b><br/><font point-size="8.5">promoted</font>>, {GLD}];
 keep [label=<<b>Previous Gold kept</b><br/><font point-size="8.5">run fails · alert</font>>, {BAD}];
 log [label=<ops.dq_results<br/><font point-size="8">every decision audited</font>>, fillcolor="#FFFFFF", color="#5B6B7F", style="rounded,filled,dashed"];
 br -> st -> dq; dq -> pub [label=" all error checks = 0"]; dq -> keep [label=" any error > 0", color="#B3261E"]; dq -> log [style=dotted];
}}'''

for k, v in D.items():
    open(f"{k}.dot", "w").write(v)
    subprocess.run(["dot", "-Tpng", "-Gdpi=220", f"{k}.dot", "-o", f"../img/{k}.png"], check=True)
    print(k, "ok")
