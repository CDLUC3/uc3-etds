import sqlstatements

# used by getetds.py
PQMETADATAXSL = '/apps/etds/apps/uc3-etds/xsl/manifest.xsl'
# used by pq-gateway.py
PQAPIXSL = '/apps/etds/apps/uc3-etds/xsl/pqetd.xsl'
# used by createmarc.py
# A UCSB entry is not present in the following queries as UCSB 
# does not currently ask for MARC records
CSVQRYNAME = {'ucla':sqlstatements.report_ucla,
              'uci':sqlstatements.report_uci,
              'ucsd':sqlstatements.report_ucsd,
              'ucmerced':sqlstatements.report_ucm,
              'ucr':sqlstatements.report_ucr,
              'ucsf':sqlstatements.report_ucsf,
              'ucsc':sqlstatements.report_ucsc,
              'ucdavis':sqlstatements.report_ucdavis,
              'ucb':sqlstatements.report_ucb}

RETRIEVE_QRYPARAMS = {'ucla':sqlstatements.retrieve_inv_merritt_ingest_ucla,
                      'uci':sqlstatements.retrieve_inv_merritt_ingest,
                      'ucsd':sqlstatements.retrieve_inv_merritt_ingest,
                      'ucmerced':sqlstatements.retrieve_inv_merritt_ingest,
                      'ucr':sqlstatements.retrieve_inv_merritt_ingest,
                      'ucsf':sqlstatements.retrieve_inv_merritt_ingest,
                      'ucsc':sqlstatements.retrieve_inv_merritt_ingest,
                      'ucdavis':sqlstatements.retrieve_inv_merritt_ingest,
                      'ucb':sqlstatements.retrieve_inv_merritt_ingest}

# UCSB has requested MARC records in the past, hence the associated entry below
UPD_QRYPARAMS = {'ucla':sqlstatements.upd_merritt_ingest_ucla,
                 'uci':sqlstatements.upd_merritt_ingest,
                 'ucsd':sqlstatements.upd_merritt_ingest,
                 'ucmerced':sqlstatements.upd_merritt_ingest,
                 'ucr':sqlstatements.upd_merritt_ingest,
                 'ucsf':sqlstatements.upd_merritt_ingest,
                 'ucsc':sqlstatements.upd_merritt_ingest,
                 'ucsb':sqlstatements.upd_merritt_ingest,
                 'ucdavis':sqlstatements.upd_merritt_ingest}

# used to match on Proquest MARC record filenames
PQ_CAMPUS_NAMES = {'Merced': 'ucmerced',
                   'Irvine' : 'uci',
                   'Santa Cruz' : 'ucsc'}

MRT_ESCHOL_PQ = '/apps/etds/apps/uc3-etds/xsl/mrt-eschol-pq.xml'
PQ_MERRITT_MATCH = '/apps/etds/apps/uc3-etds/xsl/PQ-Merritt-match.xml'
PQ_XSLT = '/apps/etds/apps/uc3-etds/xsl/PQ2MARC.xsl'
NAMESPACE_XSLT = '/apps/etds/apps/uc3-etds/xsl/namespace.xsl'
TEST_XSLT = '/apps/etds/apps/uc3-etds/xsl/PQ-test.xsl'
SAXON = '/apps/etds/apps/uc3-etds/lib/saxon9he.jar'
TRANSFORM = 'net.sf.saxon.Transform'
XML_PROLOG = '<?xml version="1.0" encoding="iso-8859-1" ?>\n'
what = 'erc.what'
who = 'erc.who'
when = 'erc.when'
target = '_target'
ezid_create = 'create'
ezid_update = 'update'
