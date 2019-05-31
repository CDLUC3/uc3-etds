#!/bin/false
"""This script runs once daily and does these tasks:
1. retrieves ETDs from sftp site
2. deletes ETDs from sftp site after retrieval
3. unzips files, check for PQ metadata file
4. constructs submission statement for Merritt from metadata
5. submits zipfiles to Merritt
6. moves zipfiles to new subfolder (in anticipation of creating
   MARC records)
7. updates ETD database table tmp_pq_metadata (update to
   merritt_ingest uses a different script)
8. updates ETD database table pq_metadata from tmp_pq_metadata
9. logs submissions, files removed from remote sftp site and errors
"""
import ast
import logging
import logging.handlers
import optparse
import os
from poster.encode import multipart_encode
import re
import shutil
import sqlite3
import sys
import time
import zipfile
import pysftp
import requests
import sqlstatements
import lxml.etree as ET
from config import campus_configs
from config import app_configs
import constants

class IterableToFileAdapter(object):
    """Used by poster.encode to stream uploaded objects"""
    def __init__(self, iterable):
        self.iterator = iter(iterable)
        self.length = iterable.total

    def read(self, size=-1):
        return next(self.iterator, b'')

    def __len__(self):
        return self.length

def argv_options():
    """defines command line options"""
    required = "hostenv"
    parser = optparse.OptionParser()
    parser.add_option('--env', dest='hostenv', choices=['stage', 'prod'])
    options = parser.parse_args()[0]
    if options.__dict__[required] is None:
        parser.error('Usage: getetds.py '
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

def parse_sftp_config(hostenv):
    """parse yaml config files"""
    sftphostname = app_configs[hostenv]['sftphost']
    privatekey = app_configs[hostenv]['private_key']
    return(sftphostname, privatekey)

def retrieve_etds(hostenv):
    """Retrieves zip files from SFTP server.
    Uses command line options for account name"""
    etdflag = False
    srvdir = ""
    (sftphostname, privatekey) = parse_sftp_config(hostenv)
# test if any zip files already in /zipfiles directory
    for testfilename in os.listdir(app_configs[hostenv]['zip_dir']):
        if testfilename.endswith(".zip"):
            etdflag = True

    for campusabbr in app_configs['sftpETDdirs'].iterkeys():
        try:
            srv = pysftp.Connection(host=sftphostname,
                                    username=campus_configs[campusabbr]['sftp_user'],
                                    private_key=privatekey)
            with srv.cd(campus_configs[campusabbr]['sftp_retrieve_dir']):
                srvdir = srv.listdir()
            if srvdir:
#           if any ETDs at all, change flag to True
                etdflag = True
                for filename in srvdir:
                    filematch = re.search(r".*\.zip$", filename)
                    if filematch:
                        os.chdir(app_configs[hostenv]['zip_dir'])
                        with srv.cd(campus_configs[campusabbr]['sftp_retrieve_dir']):
                            try:
                                srv.get(filename)
                                logging.info('Retrieving %s', filename)
                            except pysftp.ConnectionException as conn_err:
                                logging.exception("ERROR retrieving file via SFTP %s: %s",
                                                  filename, conn_err.message)
                            except pysftp.SSHException as ssh_err:
                                logging.exception("ERROR with sftp connection: %s",
                                                  ssh_err.message)
            else:
                logging.info('No files to retrieve from %s %s',
                             sftphostname, campusabbr)
        except pysftp.ConnectionException as err:
            logging.exception("ERROR delivering via SFTP: %s", err.message)
        except pysftp.SSHException as ssh_err:
            logging.exception("ERROR connecting to SFTP server %s: %s",
                              sftphostname, ssh_err.message)
        except pysftp.AuthenticationException as auth_err:
            logging.exception("Error authenticating to SFTP server: %s: %s",
                              sftphostname, auth_err)
    return etdflag

def delete_etds(hostenv):
    """Deletes zip files on remote SFTP server, if file exists
    in zipfile directory. Checks that filesizes match on local
    and remote copies"""
    zipdir = app_configs[hostenv]['zip_dir']
    localfiledict = {}
    localfilenames = [f for f in os.listdir(zipdir) if os.path.isfile(os.path.join(zipdir, f))]
    (sftphostname, privatekey) = parse_sftp_config(hostenv)
# create dictionary of filenames, filesizes in local zipdir
    for localfn in localfilenames:
        localpathname = os.path.join(zipdir, localfn)
        localfiledict.update({localfn: os.path.getsize(localpathname)})
# go through all campuses
    for campusabbr in app_configs['sftpETDdirs'].iterkeys():
        try:
            srv = pysftp.Connection(host=sftphostname,
                                    username=campus_configs[campusabbr]['sftp_user'],
                                    private_key=privatekey)
            with srv.cd(campus_configs[campusabbr]['sftp_retrieve_dir']):
                for attr in srv.listdir_attr():
                    remote_filesize = attr.st_size
                    remote_filename = attr.filename
                    if localfiledict.get(remote_filename, None) is not None:
                        # check if filesize match for remote and local files
                        if localfiledict[remote_filename] == remote_filesize:
                            try:
                                srv.remove(remote_filename)
                                logging.info("Zipfile removed from remote sftp "
                                             "site %s", remote_filename)
                            except IOError as io_err:
                                logging.exception("ERROR removing file %s: %s",
                                                  remote_filename, io_err.message)
                        else:
                            logging.error("ERROR filesize mismatch on %s", remote_filename)
        except pysftp.ConnectionException as err:
            logging.exception("ERROR connecting to SFTP server: %s %s",
                              sftphostname, err.message)
        except pysftp.SSHException as ssh_err:
            logging.exception("ERROR SSH connection to SFTP server %s: %s",
                              sftphostname, ssh_err.message)
        except pysftp.AuthenticationException as auth_err:
            logging.exception("Error authenticating to SFTP server: %s: %s",
                              sftphostname, auth_err)

def extract_metadata(hostenv):
    """Extracts metadata in Proquest XML metadata file contained
    in zip container. Uses extracted metadata for Merritt submission,
    and to update tmp_pq_metadata table in etd.db"""
    merritt_params_list = []
    pq_metadata_rows = []
    zipdir = app_configs[hostenv]['zip_dir']
    filenames = [f for f in os.listdir(zipdir) if os.path.isfile(os.path.join(zipdir, f))]
    for zfile in filenames:
        if not zfile.startswith('.'):
            try:
                pq_zfile = zipfile.ZipFile(zipdir+zfile, 'r')
                for zxml in pq_zfile.namelist():
                    if zxml[-9:] == "_DATA.xml":
                        zfullpath = zipdir+zfile
                        pqopen = pq_zfile.open(zxml)
                        pqstring = pqopen.read()
                        dom = ET.fromstring(pqstring)
                        mrtxslt = ET.parse(app_configs[hostenv]['etd_xsl_file'])
                        pqxslt = ET.parse(constants.PQMETADATAXSL)
                        mrtransform = ET.XSLT(mrtxslt)
                        newmrt = mrtransform(dom, filename=ET.XSLT.strparam(zfullpath))
                        pqtransform = ET.XSLT(pqxslt)
                        newpq = str(pqtransform(dom))
                        escapedpq = newpq.replace("'", "\x27")
                        merritt_params_list.append(str(newmrt))
                        pq_metadata_rows.append(escapedpq)
                        logging.info("Extracting metadata for %s", zxml)
            except zipfile.BadZipfile:
                logging.exception('ERROR occured while trying to unzip file %s', zfile)
    return(merritt_params_list, pq_metadata_rows)

def get_merritt_login(hostenv):
    """Get Merritt login info from yaml file"""
    username = app_configs[hostenv]['mrtuser']
    pword = app_configs[hostenv]['mrtpw']
    merritthost = app_configs[hostenv]['mrthost']
    return(merritthost, username, pword)

def multipart_encode_for_requests(params, boundary=None, cb=None):
    """streams uploads instead of loading entire file into memory"""
    datagen, headers = multipart_encode(params, boundary, cb)
    return IterableToFileAdapter(datagen), headers


def submit_to_merritt(submission_params, hostenv):
    """Submits zip file to Merritt, with metadata extracted from
    PQ metadata file. Problem with certificates on merritt-stage;
    current sets 'Verify' to False"""
    newdirname = app_configs[hostenv]['zip_dir']+time.strftime('%Y%m%d')
    header_params = {'Content-Disposition':'form-data'}
    param_dict = ast.literal_eval(submission_params)
    pathname = param_dict['file']
    filename = (os.path.basename(pathname))
    param_dict['file'] = open(pathname, 'rb')
    datagen, headers = multipart_encode_for_requests(param_dict)
    (merritt_host, username, password) = get_merritt_login(hostenv)
    merritt_url = merritt_host + 'object/update/'
    ## problem with cert on merritt-stage requires verify be set to False
    if hostenv == 'stage':
        verify_flag = False
    else:
        verify_flag = True
    try:
        req = requests.post(merritt_url, auth=(username, password),
                            headers=headers, data=datagen,
                            verify=verify_flag)
        if req.status_code == 200:
            logging.info("Zip container submitted to Merritt %s", filename)
            if not os.path.exists(newdirname):
                os.makedirs(newdirname)
            try:
                shutil.move(pathname, newdirname+"/"+filename)
                logging.info("File %s moved to %s", filename, newdirname)
            except shutil.Error as err:
                logging.exception("ERROR: error moving file %s: %s", filename, err)
        else:
# requests will flag connection errors as exceptions; this will also raise
# HTTP response errors as exceptions
            req.raise_for_status()
    except requests.exceptions.RequestException as err:
        logging.exception("ERROR submitting to Merritt: %s", err)

def update_tmp_pq_metadata(tmp_pq_md_row, hostenv):
    """Updates tmp_pq_metadata table with metadata extracted
    from PQ metadata file"""
    conn = sqlite3.connect(app_configs[hostenv]['etddb'])
    conn.text_factory = str
    cur = conn.cursor()
    # insert row into table
    data = tmp_pq_md_row.split('\t')
    try:
        cur.execute(sqlstatements.upd_tmp_pq_metadata, data)
    except sqlite3.Error as err:
        logging.exception("ERROR writing to ETDDB tmp_pq_metadata: %s", err)
    if data[7]:
        logging.info('Writing %s to etddb', data[7])
    # Save (commit) the changes
    conn.commit()
    # convert empty values to NULL
    try:
        cur.executescript(sqlstatements.upd_tmp_pq_metadata_null)
    except sqlite3.Error as err:
        logging.exception("ERROR updating NULL values in ETDDB tmp_pq_metadata: %s", err)
#    # Save (commit) the changes
    conn.commit()
    cur.close()
    conn.close()

def update_pq_metadata(hostenv):
    """Updates pq_metadata table from info in tmp_pq_metadata"""
    conn = sqlite3.connect(app_configs[hostenv]['etddb'])
    conn.text_factory = str
    cur = conn.cursor()
    try:
        cur.execute(sqlstatements.upd_pq_metadata)
    except sqlite3.Error as err:
        logging.exception("ERROR writing to ETDDB pq_metadata: %s", err)
        # Save (commit) the changes
    conn.commit()
    cur.execute(sqlstatements.del_tmp_pq_metadata)
    conn.commit()
    cur.close()
    conn.close()

def main():
    """This script runs once daily and does these tasks:
    1. retrieves ETDs from sftp site
    2. deletes ETDs from sftp site after retrieval
    3. unzips files, check for PQ metadata file
    4. constructs submission statement for Merritt from metadata
    5. submits zipfiles to Merritt
    6. moves zipfiles to new subfolder
    7. updates ETD database table tmp_pq_metadata (update to
       merritt_ingest uses a different script)
    8. updates ETD database table pq_metadata from tmp_pq_metadata
    9. logs submissions, files removed from remote sftp site and errors
    """
    ## process command line
    hostenv = argv_options()
    #add logging
    set_logging(hostenv)
    ## retrieve zipfiles from sftp server
    etd_flag = retrieve_etds(hostenv)
    ## delete zipfiles on sftp server
    if etd_flag:
        delete_etds(hostenv)
    #extract metadata from PQ XML metadata in zipfile
        (merritt_pm_list, pq_md_list) = extract_metadata(hostenv)
    #submit zipfile to Merritt, with extracted metadata
        for merritt_param in merritt_pm_list:
            submit_to_merritt(merritt_param, hostenv)
            # interval between submissions, so as not to overload Merritt ingest
            time.sleep(15)
        #update db with extracted metadata
        for pq_md_entry in pq_md_list:
            update_tmp_pq_metadata(pq_md_entry, hostenv)
        update_pq_metadata(hostenv)

if __name__ == '__main__':
    main()
