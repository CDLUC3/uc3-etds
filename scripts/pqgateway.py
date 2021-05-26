#!/bin/false
"""This script performs these steps:
#1. retrieve author, title info from sqlite db
#2. form CQL query
#3. send query to Proquest API
#4. retrieve results
#5. import results to tmp table in db
#6. update pq_gateway table from tmp_pq_gateway
"""
import logging
import logging.handlers
import optparse
import os
import re
import sqlite3
import sys
import unicodedata
import urllib
import constants
import lxml.etree as ET
import sqlstatements
from config import app_configs

def argv_options():
    """defines command line options"""
    required = "hostenv"
    parser = optparse.OptionParser()
    parser.add_option('--env', dest='hostenv', choices=['stage', 'prod'])
    options = parser.parse_args()[0]
    if options.__dict__[required] is None:
        parser.error('Usage: pqgateway.py '
                     '--env [stage | prod]')
        sys.exit(1)
    return options.hostenv

def set_logging(hostenv):
    """Set logging levels, handlers"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, app_configs[hostenv]['log_level']))
    formatter = logging.Formatter('%(asctime)s %(message)s')
    log2file = logging.FileHandler(app_configs[hostenv]['log_file'])
    log2email = logging.handlers.SMTPHandler(mailhost=('localhost'),
                                             fromaddr="uc3@ucop.edu",
                                             toaddrs=app_configs[hostenv]['error_notify'],
                                             subject=u"ETD Error!")
    log2file.setLevel(logging.INFO)
    log2email.setLevel(logging.ERROR)
    log2file.setFormatter(formatter)
    log2email.setFormatter(formatter)
    logger.addHandler(log2file)
    logger.addHandler(log2email)

def retrieve_metadata(hostenv):
    """retrieves author, title from db"""
    conn = sqlite3.connect(app_configs[hostenv]['etddb'])
    cur = conn.cursor()
    # insert row into table
    try:
        cur.execute(sqlstatements.retrieve_pqqry_metadata_temp)
# keep above line and retrieve_pqqry_metadata_temp query until UCSF is in eScholarship
#        cur.execute(sqlstatements.retrieve_pqqry_metadata)
    except sqlite3.Error as err:
        logging.exception("ERROR retrieving PQ info from db: %s", err)
    query_list = cur.fetchall()
    return query_list

def format_qry_params(author, title):
    """formats author title params for CQL query"""
    unaccented_author = remove_accents(author)
    trunc_author = re.match(r'^([^,]+),\s+(\w+)', unaccented_author)
    trunc_author2 = trunc_author.group(0) if trunc_author is not None else ''
    newtitle = replace_chars(title)
    unaccented_title = remove_accents(newtitle)
    filtered_title = remove_stop_words(unaccented_title)
    trunc_list = filtered_title.split()[:4]
    trunc_title = ' '.join(trunc_list)
    return trunc_author2, trunc_title

def remove_accents(input_str):
    """Normalizes accented characters by changing to unaccented chars"""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def replace_chars(input_str):
    """Removes problem characters from query string"""
#pylint: disable=anomalous-backslash-in-string
# first removes punctuation
    new_str01 = re.sub(u'[\u00a1\u0022\u0027\u201c\u201d\u2018\u2019\u00bd\u00bf\u00ef\~\?\!\:\|\,\(\)]',
                       '', input_str)
# then removes Greek chars
    new_str02 = re.sub(u'[\u03b1\u03b2\u03b3\u03b4\u03b5\u03bb\u03bc\u03c0\u03c4\u03c7\u03c8\u03c9]',
                       '', new_str01)
# replaces hyphens, en dash and em dash with space
    new_str03 = re.sub(u'[\u2010\u2011\u2013\u2014]', ' ', new_str02)
# replaces slash and hyphen with space
    new_str04 = re.sub('[/|-]', ' ', new_str03)
# substitutes some ligatures with two-char equivalents
    new_str05 = re.sub(u'\u00C6', 'AE', new_str04)
    new_str06 = re.sub(u'\u00E6', 'ae', new_str05)
    new_str07 = re.sub(u'\u00DF', 'ss', new_str06)
    return new_str07

def remove_stop_words(input_str):
    """Removes stop words from query string"""
    remove_list = ['a', 'an', 'and', 'of', 'as', 'in', 'for', 'on', 'the', 'near', 'not', 'to', 'is']
    word_list = input_str.split()
    cleaned_str = ' '.join([i for i in word_list if i.lower() not in remove_list])
    return cleaned_str

def create_cql_command(author, title):
    """Creates CQL query for Proquest XML Gateway"""
    cql_command = ''
    return_cql_command = True
    pq_gateway_url = "http://fedsearch.proquest.com/search/sru/pqdt?"
    pq_gateway_datastr_1 = "operation=searchRetrieve&version=1.2&maximumRecords=30&startRecord=1"
    pq_gateway_datastr_2 = "&query=title%3D%22"
    pq_gateway_datastr_3 = "%22%20AND%20author%3D%22"
    pq_gateway_datastr_4 = "%22"
    try:
        author_encoded = urllib.quote_plus(author)
    except KeyError as err:
        return_cql_command = False
    try:
        title_encoded = urllib.quote_plus(title)
    except KeyError as err:
        return_cql_command = False
    if return_cql_command:
        cql_command = pq_gateway_url + pq_gateway_datastr_1 + pq_gateway_datastr_2 \
                      + title_encoded + pq_gateway_datastr_3 + author_encoded \
                      + pq_gateway_datastr_4
    return cql_command

def execute_cql_query(cql_query):
    """Executes CQL query"""
    req = " "
    try:
        req = urllib.urlopen(cql_query)
    except IOError as err:
        logging.exception("ERROR connecting to Proquest XML Gateway: %s", err)
    return req.read()

def xslt_transform(xml_str):
    """Transform results of CQL query for importing into SQLite db"""
    dom = ET.fromstring(xml_str)
    pqxslt = ET.parse(constants.PQAPIXSL)
    pqtransform = ET.XSLT(pqxslt)
    newpq = str(pqtransform(dom))
    return newpq

def upd_tmp_pq_gateway(hostenv, txt_str):
    """Imports results of CQL query into SQLite tmp table"""
    conn = sqlite3.connect(app_configs[hostenv]['etddb'])
    conn.text_factory = str
    sql_cur = conn.cursor()
    if not txt_str.startswith('Not found'):
        data = txt_str.split('\t')
# insert row into table
        try:
            sql_cur.execute(sqlstatements.upd_tmp_pq_gateway, data)
        except sqlite3.Error as err:
            logging.exception("ERROR updating tmp_pq_gateway table: %s", err)
# Save (commit) the changes
    conn.commit()
    sql_cur.close()
    conn.close()

def upd_pq_gateway(hostenv):
    """Updates pq_gateway table from tmp table"""
    conn = sqlite3.connect(app_configs[hostenv]['etddb'])
    conn.text_factory = str
    sql_cur = conn.cursor()
# insert row into table
    try:
        sql_cur.execute(sqlstatements.upd_pq_gateway)
    except sqlite3.Error as err:
        logging.exception("ERROR updating pq_gateway table: %s", err)
# Save (commit) the changes
    conn.commit()
    sql_cur.close()
    conn.close()

def remove_tags(input_str):
    """Removes formatting tags, double spaces from text string"""
    new_str01 = re.sub(r'<(i|sub|sup)[^>]*?>', '', input_str)
    new_str02 = re.sub(r'</(i|sub|sup)[^>]*?>', '', new_str01)
    new_str03 = re.sub(r'  ', ' ', new_str02)
    return new_str03

def main():
    """This script queries the Proquest XML Gateway to retrieve PQ identifier and ISBN,
    updates the pq_gateway table in SQLite table with info."""
    hostenv = argv_options()
    metadata_list = retrieve_metadata(hostenv)
    for author, title in metadata_list:
        (procd_author, procd_title) = format_qry_params(author, title)
        cql_command = create_cql_command(procd_author, procd_title)
        if len(cql_command) > 0:
            pq_metadata = execute_cql_query(cql_command)
            pq_gateway_metadata = xslt_transform(pq_metadata)
            formatted_metadata = remove_tags(pq_gateway_metadata)
            upd_tmp_pq_gateway(hostenv, formatted_metadata)
    upd_pq_gateway(hostenv)

if __name__ == '__main__':
    main()
