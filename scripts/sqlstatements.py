upd_pq_metadata="""
               INSERT OR REPLACE INTO pq_metadata
               SELECT author, title, substr(accept_date,7,4) || '-' || substr(accept_date,1,2) || '-' || substr(accept_date,4,2), embargo_code, degree, dept, advisor, 'PQETD:' || SUBSTR(local_id, 1,LENGTH(local_id)-6) || SUBSTR(local_id,-5), student_agreement_date, local_embargo_period, local_IR_access_option,
               CASE when length(sales_restrict_remove)>1
               THEN substr(sales_restrict_remove,7,4) || '-' || substr(sales_restrict_remove,1,2) || '-' || substr(sales_restrict_remove,4,2)
               ELSE ""
               END,
               CASE when cc_license='none'
               THEN NULL
               WHEN cc_license=''
               THEN NULL
               ELSE cc_license
               END, pub_option, third_party_search, third_party_sales, free_publishing_flag, aux_file
               FROM tmp_pq_metadata;
               """
upd_tmp_pq_metadata="""
INSERT INTO tmp_pq_metadata (author, title, accept_date, embargo_code, degree, dept, advisor, local_id, student_agreement_date, local_embargo_period, local_IR_access_option, sales_restrict_remove, cc_license, pub_option, third_party_search, third_party_sales, free_publishing_flag, aux_file) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""
upd_tmp_pq_metadata_null="""
update tmp_pq_metadata SET cc_license=NULL where substr(cc_license,1,4)='none';
update tmp_pq_metadata SET cc_license=NULL where length(cc_license)=1;
update tmp_pq_metadata SET local_IR_access_option=NULL where local_IR_access_option='';
update tmp_pq_metadata SET sales_restrict_remove=NULL where sales_restrict_remove='';
update tmp_pq_metadata SET local_embargo_period=NULL where local_embargo_period='';
update tmp_pq_metadata SET student_agreement_date=NULL where student_agreement_date='';
update tmp_pq_metadata SET free_publishing_flag=NULL where free_publishing_flag=char(10);
update tmp_pq_metadata SET third_party_sales=NULL where third_party_sales='';
"""
retrieve_inv_merritt_ingest="""
select inv_ingests.job_id as job_id, inv_objects.ark as merritt_ark, inv_objects.erc_where as local_id, inv_objects.version_number as version, inv_ingests.filename as filename, inv_objects.erc_what as obj_title, inv_objects.erc_who as obj_creator, inv_objects.erc_when as obj_date, inv_ingests.submitted as submit_date, inv_objects.modified as complete_date
from inv_objects, inv_ingests
where inv_objects.id=inv_ingests.inv_object_id
and inv_ingests.profile IN ('uci_lib_etd_content', 'ucm_lib_etd_content', 'ucr_lib_etd_content', 'ucsb_lib_etd_content', 'ucsc_lib_etd_content', 'ucsd_lib_etd_content', 'ucsf_lib_etd_content', 'ucd_lib_etd_content', 'ucd_lib_etd_content')
and DATE(inv_ingests.submitted)=CURDATE();
"""
retrieve_inv_merritt_ingest_ucla="""
select inv_ingests.job_id as job_id, inv_objects.ark as merritt_ark, inv_objects.erc_where as local_id, inv_objects.version_number as version, inv_ingests.filename as filename, inv_objects.erc_what as obj_title, inv_objects.erc_who as obj_creator, inv_objects.erc_when as obj_date, inv_ingests.submitted as submit_date, inv_objects.modified as complete_date
from inv_objects, inv_ingests
where inv_objects.id=inv_ingests.inv_object_id
and inv_ingests.profile='ucla_lib_etd_content'
and DATE(inv_ingests.submitted)=CURDATE();
"""
upd_tmp_merritt_ingest="""
INSERT INTO tmp_merritt_ingest (job_id, merritt_ark, local_id, version, filename, obj_title, obj_creator, obj_date, submit_date, complete_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

upd_merritt_ingest="""
INSERT OR REPLACE INTO merritt_ingest
SELECT merritt_ark, replace(local_id, rtrim(local_id, replace(local_id, ' ; ', '')), ''), version, filename, obj_title, obj_creator, obj_date, substr(complete_date,1,10) from tmp_merritt_ingest
WHERE tmp_merritt_ingest.merritt_ark!='merritt_ark' OR tmp_merritt_ingest.merritt_ark!=NULL;
"""
upd_merritt_ingest_ucla="""
INSERT OR REPLACE INTO merritt_ingest
SELECT merritt_ark, ltrim(replace(local_id, rtrim(local_id, replace(local_id, '; ', '')), '')), version, filename, obj_title, obj_creator, substr(obj_date,1,4), substr(complete_date,1,10) from tmp_merritt_ingest
WHERE tmp_merritt_ingest.merritt_ark!='merritt_ark' OR tmp_merritt_ingest.merritt_ark!=NULL;
"""
upd_tmp_escholfeed="""
INSERT INTO tmp_escholfeed (title, eschol_link, local_id, merritt_submit_date, merritt_ark) VALUES (?, ?, ?, ?, ?);
"""
upd_escholfeed="""
INSERT OR REPLACE INTO escholfeed SELECT eschol_link, merritt_submit_date, substr(merritt_ark,16,LENGTH(merritt_ark)-16) from tmp_escholfeed WHERE tmp_escholfeed.eschol_link!="eScholarship Link" OR tmp_escholfeed.eschol_link!=NULL;
"""
get_merritt_ark="""
SELECT merritt_ark from merritt_ingest WHERE filename=?;
"""
get_eschol_link="""
SELECT eschol_link FROM escholfeed WHERE merritt_ark=?;
"""
upd_mrt_eschol_pq_file="""
SELECT merritt_ingest.merritt_ark, merritt_ingest.local_id, escholfeed.eschol_link FROM merritt_ingest, escholfeed WHERE merritt_ingest.merritt_ark=escholfeed.merritt_ark;
"""
upd_pq_merritt_match="""
SELECT pq_gateway.title , pq_gateway.isbn , pq_gateway.pq_id , pq_metadata.local_id, escholfeed.eschol_link , pq_metadata.embargo_code, pq_metadata.sales_restrict_remove FROM pq_gateway, pq_metadata, merritt_ingest LEFT OUTER JOIN marc_records ON ( marc_records.isbn = pq_gateway.isbn ) LEFT OUTER JOIN escholfeed ON ( escholfeed.merritt_ark = merritt_ingest.merritt_ark ) WHERE marc_records.isbn IS NULL AND pq_gateway.title = merritt_ingest.obj_title COLLATE NOCASE AND pq_metadata.local_id = merritt_ingest.local_id;
"""

report_ucla="""
SELECT LTRIM(merritt_ingest.local_id, 'PQETD:ucla') as 'Proquest ID', merritt_ingest.obj_creator AS 'Author', merritt_ingest.obj_title AS 'Title', strftime('%Y', pq_metadata.accept_date) AS 'Year Accepted', merritt_ingest.merritt_ark AS 'Merritt ARK', merritt_ingest.complete_date AS 'Submitted to Merritt', escholfeed.eschol_link AS 'eScholarship Link', IFNULL('http://search.proquest.com/docview/'|| pq_gateway.pq_id,' ') AS 'Proquest Link', embargo_codes.label AS 'Embargo Period', CASE WHEN pq_metadata.embargo_code='4' AND length(pq_metadata.local_embargo_period)<10 THEN date(pq_metadata.sales_restrict_remove) WHEN pq_metadata.embargo_code=4 and length(pq_metadata.local_embargo_period)>=10 THEN date(pq_metadata.local_embargo_period) WHEN pq_metadata.embargo_code<'4' THEN CASE WHEN strftime('%d', pq_metadata.accept_date)='01' AND strftime('%m', pq_metadata.accept_date)='01' THEN date(pq_metadata.accept_date,'' || '+' || embargo_codes.label || '', '+1 year','-1 day') ELSE date(pq_metadata.accept_date,'' || '+' || embargo_codes.label || '', '-1 day') END END AS 'Embargo End Date', date(marc_records.date_delivered) AS 'MARC Record Delivered' FROM pq_metadata, merritt_ingest, embargo_codes LEFT OUTER JOIN pq_gateway ON merritt_ingest.obj_title=pq_gateway.title COLLATE NOCASE LEFT OUTER JOIN escholfeed ON merritt_ingest.merritt_ark=escholfeed.merritt_ark LEFT OUTER JOIN marc_records ON escholfeed.eschol_link=marc_records.eschol_link WHERE pq_metadata.local_id=merritt_ingest.local_id AND SUBSTR(merritt_ingest.local_id,7,4)='ucla' AND pq_metadata.embargo_code=embargo_codes.code AND date(merritt_ingest.complete_date)>date('2017-01-01') ORDER BY merritt_ingest.local_id;
"""
report_uci="""
SELECT LTRIM(merritt_ingest.local_id, 'PQETD:uci') as 'Proquest ID', merritt_ingest.obj_creator AS 'Author', merritt_ingest.obj_title AS 'Title', strftime('%Y', pq_metadata.accept_date) AS 'Year Accepted', merritt_ingest.merritt_ark AS 'Merritt ARK', merritt_ingest.complete_date AS 'Submitted to Merritt', escholfeed.eschol_link AS 'eScholarship Link', IFNULL('http://search.proquest.com/docview/'|| pq_gateway.pq_id,' ') AS 'Proquest Link', embargo_codes.label AS 'Embargo Period', CASE WHEN pq_metadata.embargo_code='4' AND length(pq_metadata.local_embargo_period)<10 THEN date(pq_metadata.sales_restrict_remove) WHEN pq_metadata.embargo_code=4 and length(pq_metadata.local_embargo_period)>=10 THEN date(pq_metadata.local_embargo_period) WHEN pq_metadata.embargo_code<'4' THEN CASE WHEN strftime('%d', pq_metadata.accept_date)='01' AND strftime('%m', pq_metadata.accept_date)='01' THEN date(pq_metadata.accept_date,'' || '+' || embargo_codes.label || '', '+1 year','-1 day') ELSE date(pq_metadata.accept_date,'' || '+' || embargo_codes.label || '', '-1 day') END END AS 'Embargo End Date', date(marc_records.date_delivered) AS 'MARC Record Delivered' FROM pq_metadata, merritt_ingest, embargo_codes LEFT OUTER JOIN pq_gateway ON merritt_ingest.obj_title=pq_gateway.title COLLATE NOCASE LEFT OUTER JOIN escholfeed ON merritt_ingest.merritt_ark=escholfeed.merritt_ark LEFT OUTER JOIN marc_records ON escholfeed.eschol_link=marc_records.eschol_link WHERE pq_metadata.local_id=merritt_ingest.local_id AND SUBSTR(merritt_ingest.local_id,7,LENGTH(merritt_ingest.local_id)-11)='uci' AND pq_metadata.embargo_code=embargo_codes.code ORDER BY merritt_ingest.local_id;
"""
report_ucsd="""
SELECT LTRIM(merritt_ingest.local_id, 'PQETD:ucsd') as 'Proquest ID', merritt_ingest.obj_creator AS 'Author', merritt_ingest.obj_title AS 'Title', strftime('%Y', pq_metadata.accept_date) AS 'Year Accepted', merritt_ingest.merritt_ark AS 'Merritt ARK', merritt_ingest.complete_date AS 'Submitted to Merritt', escholfeed.eschol_link AS 'eScholarship Link', IFNULL('http://search.proquest.com/docview/'|| pq_gateway.pq_id,' ') AS 'Proquest Link', embargo_codes.label AS 'Embargo Period', CASE WHEN pq_metadata.embargo_code='4' AND length(pq_metadata.local_embargo_period)<10 THEN date(pq_metadata.sales_restrict_remove) WHEN pq_metadata.embargo_code=4 and length(pq_metadata.local_embargo_period)>=10 THEN date(pq_metadata.local_embargo_period) WHEN pq_metadata.embargo_code<'4' THEN CASE WHEN strftime('%d', pq_metadata.accept_date)='01' AND strftime('%m', pq_metadata.accept_date)='01' THEN date(pq_metadata.accept_date,'' || '+' || embargo_codes.label || '', '+1 year','-1 day') ELSE date(pq_metadata.accept_date,'' || '+' || embargo_codes.label || '', '-1 day') END END AS 'Embargo End Date', date(marc_records.date_delivered) AS 'MARC Record Delivered' FROM pq_metadata, merritt_ingest, embargo_codes LEFT OUTER JOIN pq_gateway ON merritt_ingest.obj_title=pq_gateway.title COLLATE NOCASE LEFT OUTER JOIN escholfeed ON merritt_ingest.merritt_ark=escholfeed.merritt_ark LEFT OUTER JOIN marc_records ON escholfeed.eschol_link=marc_records.eschol_link WHERE pq_metadata.local_id=merritt_ingest.local_id AND SUBSTR(merritt_ingest.local_id,7,4)='ucsd' AND pq_metadata.embargo_code=embargo_codes.code ORDER BY merritt_ingest.local_id;
"""
report_ucm="""
SELECT LTRIM(merritt_ingest.local_id, 'PQETD:ucmerced') as 'Proquest ID', merritt_ingest.obj_creator AS 'Author', merritt_ingest.obj_title AS 'Title', strftime('%Y', pq_metadata.accept_date) AS 'Date Submitted', merritt_ingest.merritt_ark AS 'Merritt ARK', merritt_ingest.complete_date AS 'Submitted to Merritt', escholfeed.eschol_link AS 'eScholarship Link', IFNULL('http://search.proquest.com/docview/'|| pq_gateway.pq_id,' ') AS 'Proquest Link', CASE WHEN pq_metadata.local_embargo_period IS NOT NULL AND pq_metadata.local_embargo_period <> "" AND length(pq_metadata.local_embargo_period)<10 THEN pq_metadata.local_embargo_period ELSE embargo_codes.label END AS 'Embargo Period', CASE WHEN pq_metadata.embargo_code='4' THEN date(pq_metadata.sales_restrict_remove) WHEN pq_metadata.embargo_code<'4' AND strftime('%d', pq_metadata.accept_date)='01' AND strftime('%m', pq_metadata.accept_date)='01' THEN date(pq_metadata.accept_date,'' || '+' || embargo_codes.label || '', '+1 year','-1 day') ELSE date(pq_metadata.accept_date,'' || embargo_codes.label || '', '-1 day') END AS 'Embargo End Date', date(marc_records.date_delivered) AS 'MARC Record Delivered' FROM pq_metadata, merritt_ingest, embargo_codes LEFT OUTER JOIN escholfeed ON merritt_ingest.merritt_ark=escholfeed.merritt_ark LEFT OUTER JOIN pq_gateway ON merritt_ingest.obj_title=pq_gateway.title COLLATE NOCASE LEFT OUTER JOIN marc_records ON escholfeed.eschol_link=marc_records.eschol_link WHERE pq_metadata.local_id=merritt_ingest.local_id AND SUBSTR(merritt_ingest.local_id,7,LENGTH(merritt_ingest.local_id)-11)='ucmerced' AND pq_metadata.embargo_code=embargo_codes.code GROUP BY merritt_ingest.local_id;
"""
report_ucr="""
SELECT LTRIM(merritt_ingest.local_id, 'PQETD:ucr') as 'Proquest ID', merritt_ingest.obj_creator AS 'Author', merritt_ingest.obj_title AS 'Title', strftime('%Y', pq_metadata.accept_date) AS 'Date Submitted', merritt_ingest.merritt_ark AS 'Merritt ARK', merritt_ingest.complete_date AS 'Submitted to Merritt', escholfeed.eschol_link AS 'eScholarship Link', IFNULL('http://search.proquest.com/docview/'|| pq_gateway.pq_id,' ') AS 'Proquest Link', CASE WHEN pq_metadata.local_embargo_period IS NOT NULL AND pq_metadata.local_embargo_period <> "" AND length(pq_metadata.local_embargo_period)<10 THEN pq_metadata.local_embargo_period ELSE embargo_codes.label END AS 'Embargo Period', CASE WHEN pq_metadata.embargo_code='4' THEN date(pq_metadata.sales_restrict_remove) WHEN pq_metadata.embargo_code<'4' AND strftime('%d', pq_metadata.accept_date)='01' AND strftime('%m', pq_metadata.accept_date)='01' THEN date(pq_metadata.accept_date,'' || '+' || embargo_codes.label || '', '+1 year','-1 day') ELSE date(pq_metadata.accept_date,'' || embargo_codes.label || '', '-1 day') END AS 'Embargo End Date', date(marc_records.date_delivered) AS 'MARC Record Delivered' FROM pq_metadata, merritt_ingest, embargo_codes LEFT OUTER JOIN pq_gateway ON merritt_ingest.obj_title=pq_gateway.title COLLATE NOCASE LEFT OUTER JOIN escholfeed ON merritt_ingest.merritt_ark=escholfeed.merritt_ark LEFT OUTER JOIN marc_records ON escholfeed.eschol_link=marc_records.eschol_link WHERE pq_metadata.local_id=merritt_ingest.local_id AND SUBSTR(merritt_ingest.local_id,7,LENGTH(merritt_ingest.local_id)-11)='ucr' AND pq_metadata.embargo_code=embargo_codes.code AND date(merritt_ingest.complete_date)>date('now','-7 days') ORDER BY merritt_ingest.local_id;
"""
report_ucsf="""
SELECT LTRIM(merritt_ingest.local_id, 'PQETD:ucsf') as 'Proquest ID', merritt_ingest.obj_creator AS 'Author', merritt_ingest.obj_title AS 'Title', strftime('%Y', pq_metadata.accept_date) AS 'Year Accepted', merritt_ingest.merritt_ark AS 'Merritt ARK', merritt_ingest.complete_date AS 'Submitted to Merritt', ' ' AS 'eScholarship Link', ' '  AS 'Proquest Link', embargo_codes.label AS 'Embargo Period', CASE WHEN embargo_codes.code='4' THEN date(pq_metadata.sales_restrict_remove) WHEN embargo_codes.code<'4' AND strftime('%d', pq_metadata.accept_date)='01' AND strftime('%m', pq_metadata.accept_date)='01' THEN date(pq_metadata.accept_date,'' || '+' || embargo_codes.label || '', '+1 year','-1 day') ELSE date(pq_metadata.accept_date,'' || embargo_codes.label || '', '-1 day') END AS 'Embargo End Date', ' ' AS 'MARC Record Delivered' FROM pq_metadata, merritt_ingest, embargo_codes WHERE pq_metadata.local_id=merritt_ingest.local_id AND SUBSTR(merritt_ingest.local_id,7,LENGTH(merritt_ingest.local_id)-11)='ucsf' AND pq_metadata.embargo_code=embargo_codes.code AND date(merritt_ingest.complete_date)>date('now','-7 days') ORDER BY merritt_ingest.local_id;
"""
report_ucsc="""
SELECT LTRIM(merritt_ingest.local_id, 'PQETD:ucsc') as 'Proquest ID', merritt_ingest.obj_creator AS 'Author', merritt_ingest.obj_title AS 'Title', strftime('%Y', pq_metadata.accept_date) AS 'Year Accepted', merritt_ingest.merritt_ark AS 'Merritt ARK', merritt_ingest.complete_date AS 'Submitted to Merritt', escholfeed.eschol_link AS 'eScholarship Link', IFNULL('http://search.proquest.com/docview/'|| pq_gateway.pq_id,' ') AS 'Proquest Link', embargo_codes.label AS 'Embargo Period', CASE WHEN pq_metadata.embargo_code='4' AND length(pq_metadata.local_embargo_period)<10 THEN date(pq_metadata.sales_restrict_remove) WHEN pq_metadata.embargo_code=4 and length(pq_metadata.local_embargo_period)>=10 THEN date(pq_metadata.local_embargo_period) WHEN pq_metadata.embargo_code<'4' THEN CASE WHEN strftime('%d', pq_metadata.accept_date)='01' AND strftime('%m', pq_metadata.accept_date)='01' THEN date(pq_metadata.accept_date,'' || '+' || embargo_codes.label || '', '+1 year','-1 day') ELSE date(pq_metadata.accept_date,'' || '+' || embargo_codes.label || '', '-1 day') END END AS 'Embargo End Date', date(marc_records.date_delivered) AS 'MARC Record Delivered' FROM pq_metadata, merritt_ingest, embargo_codes LEFT OUTER JOIN pq_gateway ON merritt_ingest.obj_title=pq_gateway.title COLLATE NOCASE LEFT OUTER JOIN escholfeed ON merritt_ingest.merritt_ark=escholfeed.merritt_ark LEFT OUTER JOIN marc_records ON escholfeed.eschol_link=marc_records.eschol_link WHERE pq_metadata.local_id=merritt_ingest.local_id AND SUBSTR(merritt_ingest.local_id,7,4)='ucsc' AND pq_metadata.embargo_code=embargo_codes.code ORDER BY merritt_ingest.local_id;
""" 
report_ucdavis="""
SELECT LTRIM(merritt_ingest.local_id, 'PQETD:ucdavis') as 'Proquest ID', merritt_ingest.obj_creator AS 'Author', merritt_ingest.obj_title AS 'Title', strftime('%Y', pq_metadata.accept_date) AS 'Date Submitted', merritt_ingest.merritt_ark AS 'Merritt ARK', merritt_ingest.complete_date AS 'Submitted to Merritt', escholfeed.eschol_link AS 'eScholarship Link', IFNULL('http://search.proquest.com/docview/'|| pq_gateway.pq_id,' ') AS 'Proquest Link', CASE WHEN pq_metadata.local_embargo_period IS NOT NULL AND pq_metadata.local_embargo_period <> "" AND length(pq_metadata.local_embargo_period)<10 THEN pq_metadata.local_embargo_period ELSE embargo_codes.label END AS 'Embargo Period', CASE WHEN pq_metadata.embargo_code='4' THEN date(pq_metadata.sales_restrict_remove) WHEN pq_metadata.embargo_code<'4' AND strftime('%d', pq_metadata.accept_date)='01' AND strftime('%m', pq_metadata.accept_date)='01' THEN date(pq_metadata.accept_date,'' || '+' || embargo_codes.label || '', '+1 year','-1 day') ELSE date(pq_metadata.accept_date,'' || embargo_codes.label || '', '-1 day') END AS 'Embargo End Date', date(marc_records.date_delivered) AS 'MARC Record Delivered' FROM pq_metadata, merritt_ingest, embargo_codes LEFT OUTER JOIN pq_gateway ON merritt_ingest.obj_title=pq_gateway.title COLLATE NOCASE LEFT OUTER JOIN escholfeed ON merritt_ingest.merritt_ark=escholfeed.merritt_ark LEFT OUTER JOIN marc_records ON escholfeed.eschol_link=marc_records.eschol_link WHERE pq_metadata.local_id=merritt_ingest.local_id AND SUBSTR(merritt_ingest.local_id,7,LENGTH(merritt_ingest.local_id)-11)='ucdavis' AND pq_metadata.embargo_code=embargo_codes.code AND date(merritt_ingest.complete_date)>date('now','-7 days') ORDER BY merritt_ingest.local_id;
"""

upd_tmp_marc_records="""
INSERT INTO tmp_marc (isbn, author, title, eschol_link, pq_link) VALUES (?, ?, ?, ?, ?);
"""
upd_marc_records="""
INSERT OR REPLACE INTO marc_records(eschol_link, pq_link, isbn, date_delivered) SELECT tmp_marc.eschol_link, tmp_marc.pq_link, tmp_marc.isbn, datetime('now','localtime') from tmp_marc;
"""
mrt_ingest_qry="""
SELECT * from inv_ingests WHERE filename=%s;
"""
get_campus_abbr="""
SELECT local_id FROM merritt_ingest WHERE filename=?;
"""
is_delivery_needed="""
SELECT count(*) FROM merritt_ingest WHERE complete_date=date(\'now\') AND local_id like ?;
"""

etddb_check_if_marc_record="""
SELECT marc_records.eschol_link FROM marc_records, escholfeed, merritt_ingest WHERE marc_records.eschol_link=escholfeed.eschol_link AND escholfeed.merritt_ark=merritt_ingest.merritt_ark AND merritt_ingest.filename=?;
"""

del_tmp_pq_metadata="""
DELETE FROM tmp_pq_metadata;
"""

del_tmp_marc_records="""
DELETE from tmp_marc;
"""

deltmp=("DELETE from tmp_escholfeed;","DELETE from tmp_merritt_ingest;","DELETE from tmp_pq_metadata;","DELETE from tmp_marc;","DELETE from tmp_pq_gateway;","DELETE from tmp_ucm_grad_div_pq_rpt;")

delalltmp=("DELETE from tmp_escholfeed;","DELETE from tmp_merritt_ingest;","DELETE from tmp_pq_metadata;","DELETE from tmp_marc;","DELETE from tmp_pq_gateway;","DELETE from tmp_ucm_grad_div_pq_rpt;","DELETE from tmp_merritt_ark;","VACUUM;")

retrieve_pqqry_metadata_temp="""
SELECT merritt_ingest.obj_creator, merritt_ingest.obj_title FROM merritt_ingest LEFT OUTER JOIN escholfeed on (escholfeed.merritt_ark=merritt_ingest.merritt_ark) WHERE merritt_ingest.obj_title NOT IN (SELECT title FROM pq_gateway) AND merritt_ingest.merritt_ark NOT IN (SELECT ark FROM no_pq_gateway) AND merritt_ingest.complete_date < date ('now', '-10 day');
"""

retrieve_pqqry_metadata="""
SELECT merritt_ingest.obj_creator, merritt_ingest.obj_title FROM merritt_ingest LEFT OUTER JOIN escholfeed on (escholfeed.merritt_ark=merritt_ingest.merritt_ark) WHERE merritt_ingest.obj_title NOT IN (SELECT title FROM pq_gateway) AND merritt_ingest.merritt_ark NOT IN (SELECT ark FROM no_pq_gateway) AND merritt_ingest.complete_date < date ('now', '-10 day');
"""
upd_tmp_pq_gateway="""
INSERT INTO tmp_pq_gateway(pq_id, isbn, author, title) VALUES (?, ?, ?, ?);
"""
upd_pq_gateway="""
INSERT OR IGNORE INTO pq_gateway SELECT pq_id, isbn, author, substr(title, 1, (length(title)-1)) FROM tmp_pq_gateway WHERE tmp_pq_gateway.pq_id!="Not found";
"""
retrieve_new_mrtarks="""
SELECT eschol_link, merritt_ark FROM escholfeed WHERE date(merritt_submit_date)=date('now');
"""
retrieve_new_eschol_links="""
select merritt_ingest.obj_title, merritt_ingest.obj_creator, merritt_ingest.obj_date, escholfeed.eschol_link from merritt_ingest, escholfeed where merritt_ingest.merritt_ark=escholfeed.merritt_ark and date(escholfeed.merritt_submit_date)=date('now');
"""
retrieve_new_eschol_links_ucb="""
select tmp_merritt_ark.title, tmp_merritt_ark.author, tmp_merritt_ark.date, escholfeed.eschol_link FROM tmp_merritt_ark, escholfeed WHERE escholfeed.merritt_ark=tmp_merritt_ark.merritt_ark
"""
