#!/bin/false
# -*- coding: latin-1 -*-
"""This script runs once daily and does the following:
 1. update escholfeed table using eScholarship reports
   a. eScholarship harvests new ETDs daily at 11am
 2. update merritt_ingest table from INV
 3. crawls dirs in zipfiles, checks if zipfile has an eScholarship link
   a. if so, create MARC XML in marcdir using XSLT as appropriate
 4. crawl dirs in marcdir, check if MARC XML file exists
   a. if so, convert to MARC format
 5. update marc_record table in ETD database
 6. delete zip container
 7. generate .csv if needed
 8. deliver appropriate files via SFTP or email
 9. submit MARC records, csv reports to Merritt
10. zip db file, copy to Google Drive as backup
11. create, update EZID records
12. other clean up
"""
import codecs
import datetime
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import logging.handlers
import optparse
import os
import re
import smtplib
import sqlite3
import subprocess
import sys
import time
import zipfile
import mysql.connector
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import pymarc
import pysftp
import requests
import sqlstatements
import unicodecsv
from config import campus_configs
from config import app_configs
import constants
from ezid import process
####
def argv_options():
    """Retrieve command line options"""
    required = "hostenv"
    parser = optparse.OptionParser()
    parser.add_option('--env', dest='hostenv', choices=['stage', 'prod'])
    options = parser.parse_args()[0]
    if options.__dict__[required] is None:
        parser.error('Usage: createmarc.py --env [stage | prod]')
        sys.exit(1)
    return options.hostenv

def set_logging(hostenv):
    """Set logging levels, handlers"""
# adding line to silence warning
#    logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
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

def upd_mrt_ingest(hostenv):
    """Updates merritt_ingest table in ETD db with information from Merritt INV db"""
    for campusname in constants.RETRIEVE_QRYPARAMS:
        mrt_ingest_array = get_inv_db_query(hostenv,
                                            constants.RETRIEVE_QRYPARAMS[campusname],
                                            data=None)
        upd_merritt_ingest_table(campusname, mrt_ingest_array, hostenv)

def parse_mysql_config(hostenv):
    """Get MySQL db host, credentials from yaml file"""
    username = app_configs[hostenv]['mysqluser']
    password = app_configs[hostenv]['mysqlpw']
    hostname = app_configs[hostenv]['mysqlhost']
    dbname = app_configs[hostenv]['mysqldbname']
    ssl_cert = app_configs[hostenv]['mysql_cert']
    return(hostname, username, password, dbname, ssl_cert)

def get_inv_db_query(hostenv, sqlquery, data):
    """Get data on latest updates to INV db"""
    (hostname, username, passwd, dbname, ssl_cert) = parse_mysql_config(hostenv)
    mrt_ingest_array = []
    try:
        mysql_connect = mysql.connector.connect(user=username, password=passwd,
                                                host=hostname, database=dbname,
                                                ssl_ca=ssl_cert)
        mysql_cursor = mysql_connect.cursor()
    except mysql.connector.Error as err:
        logging.exception("ERROR connecting to INV DB: %s", err.message)
    if data:
        try:
            mysql_cursor.execute(sqlquery, (data,))
        except mysql.connector.Error as err1:
            logging.exception("ERROR executing query in Merritt INV %s", err1)
    else:
        try:
            mysql_cursor.execute(sqlquery)
        except mysql.connector.Error as err2:
            logging.exception("ERROR executing query in Merritt INV %s", err2)
    try:
        mrt_ingest_array = mysql_cursor.fetchall()
    except mysql.connector.Error as err3:
        logging.exception("ERROR fetching info from Merritt INV %s", err3)
    mysql_cursor.close()
    mysql_connect.close()
    return mrt_ingest_array

def upd_merritt_ingest_table(campusname, mrt_ingest_array, hostenv):
    """Update merritt_ingest table in ETD db, using data retrieved from INV db
       Need to run a special query for UCLA, because they have multiple local IDs"""
    sqlite_conn = sqlite3.connect(app_configs[hostenv]['etddb'])
    sqlite_conn.text_factory = str
    sqlite_cursor = sqlite_conn.cursor()
    # insert row into table
    for row in mrt_ingest_array:
        try:
            sqlite_cursor.execute(sqlstatements.upd_tmp_merritt_ingest, row)
        except sqlite3.Error as err1:
            logging.exception("ERROR getting Merritt info from INV: %s", err1)
    # Save (commit) the changes
    sqlite_conn.commit()
    try:
        sqlite_cursor.execute(constants.UPD_QRYPARAMS[campusname])
    except sqlite3.Error as err2:
        logging.exception("ERROR getting Merritt info from INV: %s", err2)
    sqlite_conn.commit()
    # delete from temporary tables
    sqlite_cursor.close()
    sqlite_conn.close()
    del_temp_tables(hostenv, sqlstatements.deltmp)

def get_eschol(campusabbr):
    """Retrieve eScholarship info, using eScholarship reports"""
    etdparams = {'affiliation': campusabbr, 'smode':'etdLinks'}
    eschol_url = 'http://escholarship.org/uc/search'
    try:
        req = requests.get(eschol_url, params=etdparams)
    except requests.exceptions.RequestException as err1:
        logging.exception("ERROR retrieving eScholarship report: %s", err1)
    if req.status_code == 200:
        logging.info("eScholfeed campus %s", campusabbr)
    else:
        logging.exception("ERROR retrieving eScholfeed for %s: %s", campusabbr, req.status_code)
    return req.text

def upd_escholfeed(campus_etds, hostenv):
    """Update escholfeed table in ETD db"""
    sqlitetmpquery = sqlstatements.upd_tmp_escholfeed
    sqliteupdquery = sqlstatements.upd_escholfeed
    sqlite_conn = sqlite3.connect(app_configs[hostenv]['etddb'])
    sqlite_cursor = sqlite_conn.cursor()
    # insert row into table
    for row in campus_etds.split('\n'):
        if ("\t" in row) and ("\t\t\t" not in row):
            data = row.split('\"\t\"')
            try:
                sqlite_cursor.execute(sqlitetmpquery, data)
            except sqlite3.Error as err1:
                logging.exception("ERROR updating tmp_eschol table: %s", err1)
                sys.exit()
    # Save (commit) the changes
    sqlite_conn.commit()
    # update escholfeed table
    try:
        sqlite_cursor.execute(sqliteupdquery)
    except sqlite3.Error as err2:
        logging.exception("ERROR updating escholfeed table: %s", err2)
        sys.exit()
    sqlite_conn.commit()
    sqlite_cursor.close()
    sqlite_conn.close()
    del_temp_tables(hostenv, sqlstatements.deltmp)

def upd_eschol_xml(hostenv):
    """Updates two XML files needed for the XSLT transform later"""
### upd mrt-eschol-pq.xml
    xmlprefix = "<?xml version=\"1.0\" encoding=\"iso-8859-1\"?>\n<results><rows>\n"
    xmlsuffix = "</rows></results>\n"
    mrt_eschol_pq_xml = open(constants.MRT_ESCHOL_PQ, 'w')
    conn = sqlite3.connect(app_configs[hostenv]['etddb'])
    mrt_cursor = conn.cursor()
    mrt_eschol_pq_xml.write(xmlprefix)
    query = sqlstatements.upd_mrt_eschol_pq_file
    try:
        mrt_cursor.execute(query)
        for (merritt_ark, local_id, eschol_link) in mrt_cursor:
            mrt_eschol_pq_xml.write("<row><value column=\"0\">{}"
                                    "</value><value column=\"1\">{}"
                                    "</value><value column=\"2\">{}"
                                    "</value></row>\n"
                                    .format(merritt_ark, local_id,
                                            eschol_link))
    except sqlite3.Error as err1:
        logging.exception("ERROR reading query for mrt-eschol-pq query: %s", err1)
    mrt_eschol_pq_xml.write(xmlsuffix)
    mrt_eschol_pq_xml.close()
    mrt_cursor.close()
### upd PQ-Merritt-match.xml
    conn.text_factory = str
    mrtmatch_cursor = conn.cursor()
    pq_merritt_match_xml = open(constants.PQ_MERRITT_MATCH, 'w')
    pq_merritt_match_xml.write(xmlprefix)
    mrtmatch_query = sqlstatements.upd_pq_merritt_match
    try:
        mrtmatch_cursor.execute(mrtmatch_query)
        for (title, isbn, pq_id, local_id, eschol_link, embargo_code,
             sales_restrict_remove) in mrtmatch_cursor:
            upd_title = re.sub(r" & ", " &amp; ", title)
            pq_merritt_match_xml.write("<row><value column=\"0\">{}"
                                       "</value><value column=\"1\">{}"
                                       "</value><value column=\"2\">{}"
                                       "</value><value column=\"3\">{}"
                                       "</value><value column=\"4\">{}"
                                       "</value><value column=\"5\">{}"
                                       "</value><value column=\"6\">{}"
                                       "</value></row>\n"
                                       .format(upd_title, isbn, pq_id, local_id,
                                               eschol_link, embargo_code,
                                               sales_restrict_remove))
    except sqlite3.Error as err2:
        logging.exception("ERROR reading query for PQ-Merritt-Match: %s", err2)
    pq_merritt_match_xml.write(xmlsuffix)
    pq_merritt_match_xml.close()
    mrtmatch_cursor.close()
    conn.close()

def create_marc_xml(hostenv):
    """Creates MARC XML files using metadata files in PQ zip containers
       in zipdir"""
    campuscount = {'ucb':0, 'ucd':0, 'uci':0, 'ucla':0, 'ucr':0,
                   'ucsd':0, 'ucsf':0, 'ucsb':0, 'ucsc':0, 'ucmerced':0}
    etdquery = sqlstatements.get_merritt_ark
    escholquery = sqlstatements.get_eschol_link
    sqlite_conn = sqlite3.connect(app_configs[hostenv]['etddb'])
    sqlite_conn.text_factory = str
    sqlite_cursor = sqlite_conn.cursor()
    for root, dirs, _ in os.walk(app_configs[hostenv]['zip_dir']):
        for dirname in dirs:
            pathname = (os.path.join(root, dirname))
            for dirfilename in os.listdir(pathname):
            # find XML files in /marc subdirectory
                if not dirfilename.startswith('.'):
                    fullpath = pathname+"/"+dirfilename
                    sqlite_cursor.execute(etdquery, (dirfilename,))
                    mrtark = sqlite_cursor.fetchone()
                    if mrtark is not None:
                        try:
                            sqlite_cursor.execute(escholquery, mrtark)
                        except sqlite3.Error as err:
                            logging.exception("ERROR retrieving eSchol_link : %s", err)
                        eschol_link = sqlite_cursor.fetchone()
                        if eschol_link is not None:
                            (campusname, pqmetadatastr) = get_pq_metadata(fullpath)
                            # need to print XML prolog for first record
                            if campus_configs[campusname]['create_marc']:
                                marcrecord = xml_saxon_transform(pqmetadatastr, constants.PQ_XSLT)
                                newcount = (campuscount[campusname])+1
                                campuscount[campusname] = newcount
                                print_marc_xml(marcrecord, campusname, newcount, hostenv)
                                logging.info("Created %s MARC record for %s",
                                             campuscount[campusname], mrtark[0])
                                update_marc_table("", eschol_link[0], "", hostenv)
                            else:
                                logging.info("No MARC record generated for %s %s",
                                             campusname, (mrtark,))
                    else:
                        logging.error("ERROR: %s not found in ETD db", fullpath)
    finish_marc_xml_files(hostenv)
    sqlite_cursor.close()
    sqlite_conn.close()

def get_pq_metadata(fullpath):
    """Extracts metadata from PQ XML file in zip container"""
    xmlstr = None
    campus = None
    try:
        pq_zfile = zipfile.ZipFile(fullpath, 'r')
        logging.info('Extracting PQ metadata from zipfile: %s', fullpath)
        for zxml in pq_zfile.namelist():
            if zxml[-9:] == '_DATA.xml':
                xmlopen = pq_zfile.open(zxml)
                xmlstr = xmlopen.read()
                campuscode = re.search(r'<DISS_inst_code>(\d+)</DISS_inst_code>', xmlstr)
                campus = (campus_configs['PQCampusCodes'][campuscode.group(1)])
    except zipfile.BadZipfile:
        logging.exception('ERROR occured while trying to unzip file %s', fullpath)
    return(campus, xmlstr)

def xml_saxon_transform(xmlstr, stylesheet):
    """Performs XSLT transform using Saxon and stylesheet passed in"""
    xmlout = None
    xmlerr = None
    xsltarg = '-xsl:'+stylesheet
    saxon_transform = subprocess.Popen(['java', '-cp', constants.SAXON,
                                        constants.TRANSFORM, '-s:-', xsltarg],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
    xmlout, xmlerr = saxon_transform.communicate(xmlstr)
    if saxon_transform.returncode != 0:
        logging.exception('ERROR with Saxon, status code %s stdout %s stderr %s',
                          saxon_transform.returncode, xmlout, xmlerr)
    return xmlout

def print_marc_xml(marcrecord, campusname, count, hostenv):
    """Write out MARC record to appropriate xml file"""
    marcnamespaces = '<marc:collection xmlns:marc=\"http://www.loc.gov/MARC21/slim\" '\
                     'xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" '\
                     'xsi:schemaLocation=\"http://www.loc.gov/MARC21/slim '\
                     'http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd\">\n'
    campusfilename = app_configs[hostenv]['marc_dir']+campusname \
                     +time.strftime("%Y%m%d")+"-orig.xml"
    marcfile = open(campusfilename, "a")
    if count == 1:
        marcfile.write(constants.XML_PROLOG)
        marcfile.write(marcnamespaces)
    marcfile.write(marcrecord)
    marcfile.write("\n")
    marcfile.close()

def finish_marc_xml_files(hostenv):
    """Add trailing </collection> tag to MARC XML file"""
    marcfileconclusion = '</marc:collection>\n'
    for campusabbr in campus_configs['PQCampusCodes'].itervalues():
        campusfilename = app_configs[hostenv]['marc_dir'] \
                         +campusabbr+time.strftime("%Y%m%d")+"-orig.xml"
        if os.path.exists(campusfilename):
            marcfile = open(campusfilename, "a")
            marcfile.write(marcfileconclusion)
            marcfile.close()
            logging.info("Created MARC XML %s", campusfilename)

def check_if_ok_to_delete(zipfilename, hostenv):
    """Check if campus should receive MARC records. If not,
       return TRUE (ok to delete). If so, check if MARC
       record has been created. If so, return TRUE (ok
       to delete). If not, return FALSE (not ok to delete)."""
    to_delete = False
    etddb_conn = sqlite3.connect(app_configs[hostenv]['etddb'])
    etddb_conn.text_factory = str
    etddb_cursor = etddb_conn.cursor()
#first check if campus should receive MARC records
    try:
        etddb_cursor.execute(sqlstatements.get_campus_abbr, (zipfilename,))
    except etddb_conn.Error as err:
        logging.exception("ERROR executing query in ETD DB %s", err)
    localid = etddb_cursor.fetchone()
    if localid is not None:
        campusabbr = re.sub(r'(^PQETD:)(.*?)(\d*$)', r'\2', localid[0])
# okay to delete if it's not one of the campuses that receive MARC records
        if campus_configs[campusabbr]['create_marc']:
# if it is one of the campuses to receive MARC records, then check if
# MARC record has been created
            try:
                etddb_cursor.execute(sqlstatements.etddb_check_if_marc_record, (zipfilename,))
            except etddb_conn.Error as err:
                logging.exception("ERROR executing query in ETD DB %s", err)
            eschollink = etddb_cursor.fetchall()
            if eschollink:
                to_delete = True
        else:
            to_delete = True
    else:
        logging.error("ERROR: no localID for %s", zipfilename)
    etddb_cursor.close()
    etddb_conn.close()
    return to_delete

def delete_dir(dir_name, hostenv):
    """Walks directory, deleting all files"""
    for dirfilename in os.listdir(app_configs[hostenv][dir_name]):
        filepathname = os.path.join(app_configs[hostenv][dir_name], dirfilename)
        if not dirfilename.startswith('.'):
            try:
                os.remove(filepathname)
                logging.info("File deleted %s", filepathname)
            except OSError as err:
                logging.exception("ERROR removing file %s: %s", filepathname, err)

def delete_working_files(hostenv):
    """Delete zipfiles that have been ingested into Merritt, and
       for which MARC records have been created (if appropriate)"""
# check in Merritt if zipfile was ingested
    for ziproot, zipdirs, _ in os.walk(app_configs[hostenv]['zip_dir']):
        for zipdirname in zipdirs:
            zippathname = (os.path.join(ziproot, zipdirname))
            for zipfilename in os.listdir(zippathname):
                zipfullpathname = os.path.join(zippathname, zipfilename)
                in_merritt = get_inv_db_query(hostenv, sqlstatements.mrt_ingest_qry, zipfilename)
                # check in ETD db if MARC record was created
                ok_to_delete = check_if_ok_to_delete(zipfilename, hostenv)
                # if both conditions are True, delete file
                if in_merritt and ok_to_delete:
                    try:
                        os.remove(zipfullpathname)
                        logging.info("File deleted %s", zipfullpathname)
                    except OSError as err1:
                        logging.exception("ERROR removing file %s: %s", zipfullpathname, err1)
                else:
                    logging.info("ERROR: File %s not deleted", zipfullpathname)
    delete_dir('rpt_dir', hostenv)
    delete_dir('tmp_dir', hostenv)
    delete_dir('marc_dir', hostenv)

def delete_empty_dirs(hostenv):
    """After deleting XML files that have been fully processed,
       delete empty directdories in zipfiles dir"""
    for root, dirs, _ in os.walk(app_configs[hostenv]['zip_dir']):
        for dirname in dirs:
            pathname = (os.path.join(root, dirname))
            if not os.listdir(pathname):
                try:
                    os.rmdir(pathname)
                except OSError as err:
                    logging.exception("ERROR removing directory %s: %s", pathname, err)

def convert_xml_to_marc(hostenv):
    """Convert MARC XML to MARC formatted .mrc file"""
    for marcfilename in os.listdir(app_configs[hostenv]['marc_dir']):
        if marcfilename[-3:] == 'xml':
            newfilename = re.sub("-orig.xml", "-marc.mrc", marcfilename)
            logging.info("Converting to MARC %s", marcfilename)
            marc_recs_out = pymarc.MARCWriter(open(app_configs[hostenv]['marc_dir'] \
                                                   +"/"+ newfilename, 'wb'))
            marc_xml_array = pymarc.parse_xml_to_array(app_configs[hostenv]['marc_dir'] \
                                                       +marcfilename)
            for rec in marc_xml_array:
                marc_recs_out.write(rec)
            marc_recs_out.close()

def convert_marc_to_xml(hostenv):
    """Proquest delivers MARC-formatted files to CDL on behalf of campuses,
       generally 6-8 weeks after ETD was delivered. We transform these using
       campus XSLT customizations, adding both eScholarship and Proquest links
       in 856 fields. Proquest files have file extension '.UNX'"""
    marc_tmpfile = os.path.join(app_configs[hostenv]['tmp_dir'], 'marctmpfile.xml')
    xmlmarcnamespace = '<collection xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' \
                        'xsi:schemaLocation="http://www.loc.gov/MARC21/slim ' \
                        'http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd">\n'
    xmlcloser = '</collection>'
    for marcfilename in os.listdir(app_configs[hostenv]['marc_dir']):
        campuscode = None
    # find *.UNX or .unx file in /marc subdirectory
        if marcfilename[-3:].upper() == 'UNX':
            # determine campus abbr
            campusabbr = re.search(r'UC\s(.*?)\sMARC.*?', marcfilename)
            if campusabbr is not None:
                campuscode = constants.PQ_CAMPUS_NAMES.get(campusabbr.group(1))
            # convert to XML
            marcpathname = os.path.join(app_configs[hostenv]['marc_dir'], marcfilename)
            try:
                reader = pymarc.MARCReader(open(marcpathname, 'rb'), to_unicode=True)
#pylint: disable=maybe-no-member
            except pymarc.exceptions.PymarcException as err:
                logging.exception("ERROR opening PQ MARC file %s: %s", marcpathname, err.message)
            writer = codecs.open(marc_tmpfile, 'w', 'utf-8')
            writer.write(constants.XML_PROLOG)
            writer.write(xmlmarcnamespace)
            for record in reader:
                record.leader = record.leader[:9] + 'a' + record.leader[10:]
                writer.write(pymarc.record_to_xml(record, namespace=False) + "\n")
            writer.write(xmlcloser)
            writer.close()
            # need to add namespaces using XSLT
            marc_tmpfilestr = open(marc_tmpfile, 'r')
            marc_tmpfileread = marc_tmpfilestr.read()
            namespace_xmlstr = xml_saxon_transform(marc_tmpfileread,
                                                   constants.NAMESPACE_XSLT)
            # test if all ISBNs are available
            test_str = xml_saxon_transform(namespace_xmlstr, constants.TEST_XSLT)
            # convert using campus customizations using XSLT
            if "ERROR" not in test_str:
                if campuscode is not None:
                    campus_stylesheet = os.path.join(app_configs[hostenv]['xsl_dir'],
                                                     campus_configs[campuscode]['pqmarcxslt'])
                    campus_xml_str = xml_saxon_transform(namespace_xmlstr, campus_stylesheet)
                    outfilename = campuscode+time.strftime("%Y%m%d")+'PQ-orig.xml'
                    outfullpath = os.path.join(app_configs[hostenv]['marc_dir'],
                                               outfilename)
                    campus_xml_file = codecs.open(outfullpath, 'wb')
                    campus_xml_file.write(campus_xml_str)
                    campus_xml_file.close()
                else:
                    logging.error("ERROR: campus code not found %s", marcfilename)
            else:
                logging.error("ERROR: UNX file %s not converted; missing %s",
                              marcfilename, test_str)

def create_csv(campusabbr, hostenv):
    """If campus received ETDs today, then generate CSV report if appropriate"""
    filename = campusabbr+time.strftime("%Y%m%d")+'.csv'
    conn = sqlite3.connect(app_configs[hostenv]['etddb'])
    conn.text_factory = str
    cur = conn.cursor()
    pathname = app_configs[hostenv]['rpt_dir']+filename
    try:
        cur.execute(constants.CSVQRYNAME[campusabbr])
        with open(pathname, 'a') as csvrpt:
            csv_writer = unicodecsv.writer(csvrpt)
            try:
                csv_writer.writerow([i[0] for i in cur.description])
            except unicodecsv.Error as err2:
                logging.exception('ERROR: failed to write csv header for %s: %s',
                                  campusabbr, err2)
            try:
                csv_writer.writerows(cur)
            except unicodecsv.Error as err3:
                logging.exception('ERROR: Failed to write csv for %s: %s',
                                  campusabbr, err3)
    except sqlite3.Error as err1:
        logging.exception("ERROR executing CSV query in ETDDB for %s: %s",
                          campusabbr, err1)
    cur.close()
    conn.close()
    logging.info("CSV written for %s", campusabbr)

def update_marc_table(isbn, eschol_link, pq_link, hostenv):
    """Update marc_records table in ETD db"""
    data = [isbn, "", "", eschol_link, pq_link]
    conn = sqlite3.connect(app_configs[hostenv]['etddb'])
    cur = conn.cursor()
    try:
        cur.execute(sqlstatements.upd_tmp_marc_records, data)
    except sqlite3.Error as err:
        logging.exception("ERROR updating tmp_marc_records table in ETDDB "
                          "for %s: %s", eschol_link, err)
    conn.commit()
    try:
        cur.execute(sqlstatements.upd_marc_records)
    except sqlite3.Error as err:
        logging.exception("ERROR updating marc_records table in ETDDB "
                          "for %s: %s", eschol_link, err)
    conn.commit()
    try:
        cur.execute(sqlstatements.del_tmp_marc_records)
    except sqlite3.Error as err:
        logging.exception("ERROR deleting entries in tmp_marc_records "
                          "table in ETDDB for %s: %s", eschol_link, err)
    conn.commit()
    cur.close()
    conn.close()

def marc_recs_received(marcfile, hostenv):
    """Determines how many MARC records are to be delivered and
       update marc_records table in ETD db"""
    count = 0
    try:
        reader = pymarc.MARCReader(open(marcfile, 'rb'))
        for record in reader:
            fields856 = []
            count += 1
            # only records delivered from Proquest include an 020 field
            if record['020'] is not None:
                isbn = record['020']['a']
                for mfield in record.get_fields('856'):
                    fields856.append(mfield['u'])
                # this updates the table for MARC records rec'd from PQ;
                # the table is also update in create_marc_xml for MARC
                # records generated from PQ XML metadata.
                update_marc_table(isbn, fields856[0], fields856[1], hostenv)
#pylint: disable=maybe-no-member
    except pymarc.exceptions.PymarcException as err:
        logging.exception("ERROR opening MARC records %s: %s", marcfile, err.message)
    return count

def etds_submitted_today(campusabbr, hostenv):
    """Queries ETD db and returns how many ETDs were submitted today"""
    int_received = 0
    local_id = 'PQETD:'+campusabbr + '%'
    conn = sqlite3.connect(app_configs[hostenv]['etddb'])
    conn.text_factory = str
    cur = conn.cursor()
    try:
        cur.execute(sqlstatements.is_delivery_needed, (local_id,))
        int_received = cur.fetchone()[0]
    except sqlite3.Error as err:
        logging.exception("ERROR executing is_delivery_needed query "
                          "in ETDDB for %s: %s", campusabbr, err)
    cur.close()
    conn.close()
    return int_received

def deliver_via_sftp(files2deliver, campusabbr, hostenv):
    """Delivers appropriate files to campus via SFTP"""
    sftphostname = app_configs[hostenv]['sftphost']
    sftpuser = campus_configs[campusabbr]['sftp_user']
    sftpdir = campus_configs[campusabbr]['sftp_delivery_dir']
    try:
        srv = pysftp.Connection(host=sftphostname, username=sftpuser,
                                private_key=app_configs[hostenv]['private_key'])
        for file2deliver in files2deliver:
            with srv.cd(sftpdir):
                try:
                    srv.put(file2deliver)
                    logging.info("File delivered via SFTP: %s %s",
                                 file2deliver, sftphostname)
                except OSError as os_err:
                    logging.exception("OS ERROR: %s", os_err)
                except IOError as io_err:
                    logging.exception("IO ERROR: %s", io_err)
    except pysftp.ConnectionException as conn_err:
        logging.exception("ERROR delivering via SFTP: %s", conn_err.message)
    except pysftp.SSHException as ssh_err:
        logging.exception("ERROR connection to SFTP server: %s", ssh_err.message)
    except pysftp.AuthenticationException as auth_err:
        logging.exception("Error authenticating to SFTP server: %s: %s",
                          sftphostname, auth_err)

def deliver_via_email(files2deliver, campusabbr, hostenv):
    """Delivers appropriate files to campus via email"""
    sig = ". Let me know if you have any questions.\n\nPerry Willett\n" \
          "California Digital Library"
    contains_marc_records = False
    etdcount = 0
    tmpcount = 0
    email_srv = smtplib.SMTP('localhost')
    to_address = campus_configs[campusabbr]['contact_email']
    from_address = "uc3@ucop.edu"
    subject = campusabbr.upper()+" ETD report : " \
            + str(email.utils.formatdate(localtime=True)[:16])
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = email.utils.COMMASPACE.join(to_address)
    msg['Date'] = email.utils.formatdate(localtime=True)
    msg['Subject'] = subject

    for campus_file in files2deliver:
        if campus_file.endswith('.mrc'):
            contains_marc_records = True
            tmpcount = marc_recs_received(campus_file, hostenv)
            etdcount += tmpcount
        part = email.mime.base.MIMEBase('application', 'octet-stream')
        part.set_payload(open(campus_file, "rb").read())
        email.encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"'
                        % os.path.basename(campus_file))
        msg.attach(part)
# check if MARC records are to be delivered
    # if ETDs received, published in eScholarship and MARC records generated
    if contains_marc_records and campus_configs[campusabbr]['delivery_marc']:
        if etdcount > 1:
            recordno = 'records'
        else:
            recordno = 'record'
        bodytext = "Here are the latest " + str(etdcount) + " MARC "+recordno \
               +" and report for "+campusabbr.upper()+" " \
               +str(email.utils.formatdate(localtime=True)[:16])
    # if ETDs received, but no MARC records generated. This could be due to a problem
    # with eScholarship harvesting.
    elif campus_configs[campusabbr]['create_marc'] and not contains_marc_records:
        etdcount = etds_submitted_today(campusabbr, hostenv)
        bodytext = "Here is the report for the latest " + str(etdcount) + " ETDs received for " \
               +campusabbr.upper()+". However, there seems to have been a problem with " \
               +"the eScholarship harvest, so no MARC records are included. The MARC records " \
               +"for these ETDs will be delivered after they've been indexed in eScholarship."
        logging.exception("There seems to have been a problem with eScholarship harvesting for %s",
                          campusabbr)
    # if ETDs received but MARC records are not generated for this campus
    else:
        etdcount = etds_submitted_today(campusabbr, hostenv)
        bodytext = "Here is the report for the latest " + str(etdcount) + " ETDs received for " \
               +campusabbr.upper()+" " \
               +str(email.utils.formatdate(localtime=True)[:16])
    text = bodytext + sig
    msg.attach(MIMEText(text))
    email_srv.sendmail(from_address, to_address, msg.as_string())
    logging.debug("Email with attachments sent to %s", campusabbr)
    email_srv.close()

def deliver_files(envhost):
    """Determines which files to deliver (MARC .mrc and/or .csv file)
       and the delivery method (SFTP or email)"""
    for campusabbr in campus_configs['PQCampusCodes'].itervalues():
        int_received = 0
        tmp_received = 0
        files2deliver = []
        # query whether ETDs have been delivered today
        deliver_csv = campus_configs[campusabbr]['delivery_csv']
        deliver_method = campus_configs[campusabbr]['delivery_method']
        # append MARC file(s) to payload if any in /marc/[campusabbr] folder
        for mrcfilename in os.listdir(app_configs[envhost]['marc_dir']):
            if mrcfilename.endswith(".mrc"):
                # need to pick only the file(s) for the campus
                ucabbr = re.search(r'(\w+)\d{8}.*?\.mrc', mrcfilename)
                if ucabbr.group(1) == campusabbr:
                    marcfullpath = os.path.join(app_configs[envhost]['marc_dir'],
                                                mrcfilename)
                    tmp_received = marc_recs_received(marcfullpath, envhost)
                    int_received += tmp_received
                    files2deliver.append(marcfullpath)
                    logging.debug("Delivering file %s", marcfullpath)
        if int_received == 0:
            int_received = etds_submitted_today(campusabbr, envhost)
        # if CSV report is to be delivered and new files have been received,
        # append CSV file to payload
        if deliver_csv and (int_received > 0):
            create_csv(campusabbr, envhost)
            for rptfilename in os.listdir(app_configs[envhost]['rpt_dir']):
                if rptfilename.startswith(campusabbr) and rptfilename.endswith(".csv"):
                    files2deliver.append(os.path.join(app_configs[envhost]['rpt_dir'],
                                                      rptfilename))
        if files2deliver:
            if deliver_method == 'sftp':
                deliver_via_sftp(files2deliver, campusabbr, envhost)
            elif deliver_method == 'email':
                deliver_via_email(files2deliver, campusabbr, envhost)
            else:
                logging.error("ERROR: Files not delivered for %s", campusabbr)
        else:
            logging.debug("No files to deliver found for %s", campusabbr)

def get_submission_params(zipfilename, hostenv):
    """This will prepare the submission parameters for Merritt submission"""
    submission_params = {}
    todaystr = str(email.utils.formatdate(localtime=True)[:16])
    todaydate = time.strftime('%Y-%m-%d')
    local_id = 'etd'+time.strftime('%Y%m%d')
    submit_title = "ETD MARC records, CSV files for " + todaystr
    mrt_coll = app_configs[hostenv]['mrt_coll']
    file_to_submit = '@'+zipfilename
    submission_params.update({'file': file_to_submit})
    submission_params.update({'type': 'container'})
    submission_params.update({'title': submit_title})
    submission_params.update({'creator': 'UC3 staff'})
    submission_params.update({'date': todaydate})
    submission_params.update({'submitter': 'etd_submitter/ETD submitter'})
    submission_params.update({'responseForm': 'xml'})
    submission_params.update({'localIdentifier': local_id})
    submission_params.update({'profile': mrt_coll})
    return submission_params

def submit_files_to_merritt(hostenv):
    """This will submit .mrc and .csv files to Merritt collection cdl_uc3_etdreports"""
    files_to_submit = []
    submit = False
    zipfilename = 'etd'+time.strftime('%Y%m%d')+'.zip'
    tmppath = app_configs[hostenv]['tmp_dir']
    zippath = os.path.join(tmppath, zipfilename)
    try:
        pq_zfile = zipfile.ZipFile(zippath, 'a')
        logging.debug("Creating zipfile: %s", zipfilename)
        for marcfilename in os.listdir(app_configs[hostenv]['marc_dir']):
            if not marcfilename.startswith('.'):
                submit = True
                files_to_submit.append(os.path.join(app_configs[hostenv]['marc_dir'],
                                                    marcfilename))
        for rptfilename in os.listdir(app_configs[hostenv]['rpt_dir']):
            if not rptfilename.startswith('.'):
                submit = True
                files_to_submit.append(os.path.join(app_configs[hostenv]['rpt_dir'],
                                                    rptfilename))
    except zipfile.BadZipfile:
        logging.exception('ERROR occured while trying to open file %s',
                          zipfilename)
    for file_to_submit in files_to_submit:
        try:
            pq_zfile.write(file_to_submit, os.path.basename(file_to_submit))
            logging.debug("Adding file %s to zip %s",
                          os.path.basename(file_to_submit), zipfilename)
        except zipfile.BadZipfile as err:
            logging.exception("ERROR adding file %s to zip %s: %s",
                              os.path.basename(file_to_submit), zipfilename, err)
    pq_zfile.close()
    submission_params = get_submission_params(zippath, hostenv)
    if submit:
        submit_to_merritt(submission_params, hostenv)

def get_merritt_login(hostenv):
    """This will return Merritt host and credentials from yaml file"""
    username = app_configs[hostenv]['mrtuser']
    pword = app_configs[hostenv]['mrtpw']
    merritthost = app_configs[hostenv]['mrthost']
    return(merritthost, username, pword)

def submit_to_merritt(submission_params, hostenv):
    """This will submit files to Merritt"""
    header_params = {'Content-Disposition':'form-data'}
    update_str = "object/update/"
    pathname = submission_params['file'].lstrip('@')
    filename = (os.path.basename(pathname))
    file_param = {'file': (filename, open(pathname, 'rb'), 'application/zip')}
    (merritt_host, username, password) = get_merritt_login(hostenv)
    merritt_url = merritt_host + update_str
    if hostenv == 'stage':
        verify_param = False
    else:
        verify_param = True
    try:
        dummy_req = requests.post(merritt_url, auth=(username, password),
                                  headers=header_params, data=submission_params,
                                  files=file_param, verify=verify_param)
        logging.info("Zip container submitted to Merritt %s", filename)
    except requests.exceptions.RequestException as err1:
        logging.exception("ERROR: Submission to Merritt failed: %s", err1)

def del_temp_tables(hostenv, sqlcommand):
    """Delete content in db temp tables"""
    conn = sqlite3.connect(app_configs[hostenv]['etddb'])
    dbcurr = conn.cursor()
    for sqlstmt in sqlcommand:
        dbcurr.execute(sqlstmt)
    conn.commit()
    dbcurr.close()
    conn.close()

def create_zipfile(hostenv):
    """Zip compress sqlite3 db to tmp directory"""
    zfilename = 'etddb.' + time.strftime('%Y%m%d') + '.zip'
    zpathname = app_configs[hostenv]['tmp_dir'] + zfilename
    dbpathname = app_configs[hostenv]['etddb']
    dbfilename = 'etd.db'
    try:
        zfile = zipfile.ZipFile(zpathname, 'w')
        zfile.write(dbpathname, dbfilename, zipfile.ZIP_DEFLATED)
        zfile.close()
    except zipfile.BadZipfile:
        logging.exception('ERROR occured while trying to unzip file %s', zfile)
    return zfilename

def auth_gdrive():
    """Authenticate to Google Drive API"""
# Define the credentials folder
    home_dir = os.path.expanduser("~")
    credential_dir = os.path.join(home_dir, ".credentials")
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, "pydrive-credentials.json")
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile(credential_path)
    if gauth.credentials is None:
    # Authenticate if they're not there
        gauth.CommandLineAuth()
    elif gauth.access_token_expired:
    # Refresh them if expired
        gauth.Refresh()
    else:
    # Initialize the saved creds
        gauth.Authorize()
# Save the current credentials to a file
    gauth.SaveCredentialsFile(credential_path)
    drive = GoogleDrive(gauth)
    return drive

def upload_to_gdrive(hostenv, drive, zfile_name):
    """Upload file to appropriate Google Drive folder, delete any zip files
       older than 7 days"""
    days_to_keep = 7
    mimetype_to_delete = 'application/zip'
    delete_date = datetime.datetime.today() - datetime.timedelta(days=days_to_keep)
    folder_id = app_configs[hostenv]['backup_gdrive_folder_id']
    zpathname = app_configs[hostenv]['tmp_dir'] + zfile_name
    file1 = drive.CreateFile({'title': zfile_name, "parents": [{"kind": "drive#fileLink",
                                                                "id": folder_id}]})
    file1.SetContentFile(zpathname)
    file1.Upload()
    file_list = drive.ListFile({'q': "'%s' in parents and trashed=false"
                                     % folder_id}).GetList()
    for file2 in file_list:
        file_creation_date_str = file2['createdDate']
        file_mimetype = file2['mimeType']
        file_creation_date = datetime.datetime.strptime(file_creation_date_str,
                                                        "%Y-%m-%dT%H:%M:%S.%fZ")
        if file_creation_date < delete_date and file_mimetype == mimetype_to_delete:
            file2.Delete()

def update_ezid_mrtarks(hostenv):
    """Update target in Merritt ARKs in EZID to point to eScholarship"""
    credentials = app_configs['ezid']['credentials']
    conn = sqlite3.connect(app_configs[hostenv]['etddb'])
    mrt_cursor = conn.cursor()
    mrt_cursor.execute(sqlstatements.retrieve_new_mrtarks)
    for (eschol_link, merritt_ark) in mrt_cursor:
        args = []
        args.extend([credentials, constants.ezid_update, merritt_ark,
                     constants.target, eschol_link])
        ezid_process(args)
    mrt_cursor.close()
    conn.close()

def create_ezid_escholarks(hostenv, sqlqry):
    """Create eScholarship ARKs"""
    credentials = app_configs['ezid']['credentials']
    conn = sqlite3.connect(app_configs[hostenv]['etddb'])
    eschol_cursor = conn.cursor()
    eschol_cursor.execute(sqlqry)
    for (title, creator, date, eschol_link) in eschol_cursor:
        args = []
        try:
            newtitle = title.decode("utf-8", "replace")
        except UnicodeEncodeError, e1:
            newtitle = title
            logging.exception("UnicodeEncodeError: %s", e1)
        except UnicodeDecodeError, e1:
            newtitle = title
            logging.exception("UnicodeDecodeError: %s", e1)
        try:
            newcreator = creator.decode("utf-8", "replace")
        except UnicodeEncodeError, e2:
            newcreator = creator
            logging.exception("UnicodeEncodeError: %s", e2)
        except UnicodeDecodeError, e2:
            newcreator = creator
            logging.exception("UnicodeDecodeError: %s", e2)
#        newtitle = re.sub("’", "'", title)
#        newcreator = re.sub("’", "'", creator)
        ark_id = ''.join([app_configs['ezid']['eschol_shoulder'], eschol_link[32:]])
        args.extend([credentials, constants.ezid_create, ark_id, constants.who,
                     newcreator, constants.what, newtitle, constants.when, date,
                     constants.target, eschol_link])
        ezid_process(args)
    eschol_cursor.close()
    conn.close()

def ezid_process(args):
    """Process EZID command"""
    # pause between requests
    time.sleep(1)
    process_response = process(args)
    if process_response.partition(' ')[0] == 'success:':
        logging.info('Successful ARK %s in EZID', args[0])
    elif process_response == '400 error: bad request - identifier already exists':
        logging.info("ERROR: %s %s", args[0], process_response)
    else:
        logging.exception('Failure ARK %s: %s', args[0], process_response)

def main():
    """This script runs once daily and does the following:
       1. update escholfeed table using eScholarship reports
           a. eScholarship harvests new ETDs daily at 11am
       2. update merritt_ingest table from INV
       3. crawls dirs in zipfiles, checks if zipfile has an eScholarship link
           a. if so, create MARC XML in marcdir using XSLT as appropriate
       4. crawl dirs in marcdir, check if MARC XML file exists
           a. if so, convert to MARC format
       5. update marc_record table in ETD database
       6. delete zip container
       7. generate .csv if needed
       8. deliver appropriate files via SFTP or email
       9. submit MARC records, csv reports to Merritt
      10. zip db file, copy to Google Drive as backup
      11. create, update EZID records
      12. other clean up
    """
    hostenv = argv_options()
# add logging
    set_logging(hostenv)
# update sqlite db with info from Merritt INV
    upd_mrt_ingest(hostenv)
# retrieve eScholarship report via API
    for campusabbr in campus_configs['PQCampusCodes'].itervalues():
        if campus_configs[campusabbr]['eschol']:
            campus_etds = get_eschol(campus_configs[campusabbr]['eschol_abbr'])
            upd_escholfeed(campus_etds, hostenv)
    upd_eschol_xml(hostenv)
# query db for Merritt ARKS, eSchol links
    create_marc_xml(hostenv)
    convert_marc_to_xml(hostenv)
    convert_xml_to_marc(hostenv)
    deliver_files(hostenv)
    submit_files_to_merritt(hostenv)
# backup db
    zfile_name = create_zipfile(hostenv)
    drive = auth_gdrive()
    upload_to_gdrive(hostenv, drive, zfile_name)
# update/create EZID records
    update_ezid_mrtarks(hostenv)
    create_ezid_escholarks(hostenv, sqlstatements.retrieve_new_eschol_links)
    create_ezid_escholarks(hostenv, sqlstatements.retrieve_new_eschol_links_ucb)
# clean up
    delete_working_files(hostenv)
    delete_empty_dirs(hostenv)
    del_temp_tables(hostenv, sqlstatements.delalltmp)
####
if __name__ == '__main__':
    main()
