# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings

# This is a sample Python script.
import json
import os
import shutil
import sys
from collections import defaultdict

from errno import errorcode
import socket
from typing import Any

from urllib3.connection import HTTPConnection
import requests
from getpass import getpass
import mysql.connector
from requests import exceptions
import pysftp
import collections
import logging
from logging.handlers import RotatingFileHandler

import paramiko
from gevent import monkey

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings


"""Setup logger"""

logger = logging.getLogger(__name__)
FORMAT = "[%(asctime)s->%(filename)s->%(funcName)s():%(lineno)s]%(levelname)s: %(message)s"
logging.basicConfig(format=FORMAT, filemode="w", level=logging.DEBUG, force=True)
logging_filename = 'App.log'
handler = RotatingFileHandler(logging_filename, maxBytes=10000000000000, backupCount=10)
handler.setFormatter(logging.Formatter(FORMAT))
logger.addHandler(handler)


def getDbServer():
    return 'rslims.jax.org'


def getDbUsername():
    return 'dba'


def getDbPassword():
    return 'rsdba'


def getDbSchema():
    return 'rslims'


"""
Function to connect to database schema
@:param:
    schema: Name of schema to connect
"""


def db_init() -> mysql.connector:
    user = getDbUsername()
    pwd = getDbPassword()
    server = getDbServer()
    schema = getDbSchema()

    try:
        conn = mysql.connector.connect(host=server, user=user, password=pwd, database=schema)
        return conn

    except mysql.connector.Error as err1:
        if err1.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Wrong user name or password passed")

        elif err1.errno == errorcode.ER_BAD_DB_ERROR:
            print("No such schema")

        else:
            error = str(err1.__dict__["orig"])
            print(error)

    except ConnectionError as err2:
        print(err2)

    return None


def push_to_Server(source: str,
                   to: str,
                   localDir: str,
                   dirName: str) -> None:
    if not source or to:
        raise ValueError("No source file or destination")

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with pysftp.Connection(host="bhjlk01.jax.org", username="jlkinternal",
                           password="t1m3st4mp!", cnopts=cnopts) as sftp:
        sftp.cwd("/srv/ftp/images/" + dirName)
        # localPath = path + "/" + file
        remotePath = "/srv/ftp/images/" + dirName + source.split("/")[-1]
        logger.info(f"Target path is{remotePath}")
        try:
            logger.info("Downloading")
            shutil.copy(source, to)
            sftp.put(localDir + "/" + source.split("/")[-1], remotepath=remotePath)
            os.remove(download_to + "/" + loc)

        except FileNotFoundError as e:
            logger.error(e)

        sftp.close()


def parseQueryResult(conn: mysql.connector.connection,
                     sql: str,
                     target: str) -> defaultdict[Any, list]:
    if not conn:
        raise ConnectionError("Not connect to database")

    # fileLocations = []
    try:
        os.mkdir(target)

    except FileExistsError as e:
        print(e)

    '''Query database'''
    cursor = conn.cursor(buffered=True, dictionary=True)
    cursor.execute(sql)
    queryResult = cursor.fetchall()
    print(len(queryResult))

    # Parse the data returned by query
    fileLocationDict = collections.defaultdict(list)
    for dict_ in queryResult[:100]:
        procedureDef = dict_["ProcedureDefinition"]
        externalId = dict_["ExternalID"]
        pathToImage = dict_["OutputValue"].split("\\")

        dest = target + "/" + externalId
        try:
            os.mkdir(dest)

        except FileExistsError as e:
            print(e)

        """
        Handle different scenario of file path:
        1) Full path is entered, but there are some minor mistakes such as character, spelling etc
        2) Only file name is entered, which requires to form the path to the file in the drive 
        """

        # Case 1)
        if len(pathToImage) > 1:

            if "Phenotype" in pathToImage:
                # print(pathToImage)
                startIndex = pathToImage.index("Phenotype")
                imageLocation = pathToImage[startIndex:]
                logger.debug(f"Case 1) location :{imageLocation}")
                # Use this line if you are on a Mac/Linux machine
                fileLocationDict[externalId].append(os.path.join(*imageLocation))

                # Use this line if you are on a windows machine
                # fileLocationDict[externalId].append(os.path.join(*imageLocation).replace("\\", "/"))

            if "phenotype" in pathToImage:
                # print(pathToImage)
                startIndex = pathToImage.index("phenotype")
                imageLocation = pathToImage[startIndex:]
                logger.debug(f"Case 1) location :{imageLocation}")
                # Use this line if you are on a Mac/Linux machine
                fileLocationDict[externalId].append(os.path.join(*imageLocation))

                # Use this line if you are on a windows machine
                # fileLocationDict[externalId].append(os.path.join(*imageLocation).replace("\\", "/"))
            else:
                print(pathToImage)
        # Case 2)
        else:
            imageLocation = os.path.join("phenotype", procedureDef, "KOMP",
                                         "images", dict_["OutputValue"])

            logger.debug(f"Case 2) location :{imageLocation}")
            # If you are on Mac/Linux
            fileLocationDict[externalId].append(imageLocation)

            # If you are on windows
            # fileLocationDict[externalId].append(imageLocation).replace("\\", "/")

    # print(len(fileLocations))
    return fileLocationDict


"""
Function for images from Phenotype drive and upload them into server
"""


def download_from_drive(fileLocationDict: defaultdict[list],
                        source: str,
                        target: str) -> None:
    if not fileLocationDict or not source \
            or not target:
        raise ValueError()

    for externalId, locations in fileLocationDict.items():
        for loc in locations:
            print(loc)
            download_from = source + loc
            logger.info(f"Download source is {download_from}")
            download_to = target + "/" + externalId
            logger.info(f"Download to {download_to}")

            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
            with pysftp.Connection(host="bhjlk01.jax.org", username="jlkinternal",
                                   password="t1m3st4mp!", cnopts=cnopts) as sftp:
                sftp.cwd("/srv/ftp/images/" + externalId)
                # localPath = path + "/" + file
                remotePath = "/srv/ftp/images/" + externalId + loc.split("/")[-1]
                try:
                    logger.info("Downloading")
                    shutil.copy(download_from, download_to)
                    sftp.put(download_to + "/" + loc, remotepath=remotePath)
                    os.remove(download_to + "/" + loc)

                except FileNotFoundError as e:
                    logger.error(e)

                sftp.close()
                # shutil.copy(download_from, download_to)


"""
if argv[1] == "-o" -> download from omero web
if argv[1] == "-p" -> download from shared drive
"""


def main():
    """Set a higher timeout tolerance"""
    HTTPConnection.default_socket_options = (HTTPConnection.default_socket_options + [
        (socket.SOL_SOCKET, socket.SO_SNDBUF, 1000000),
        (socket.SOL_SOCKET, socket.SO_RCVBUF, 1000000)
    ])

    if sys.argv[1] == "-o":
        # file = sys.argv[1]
        session = requests.Session()
        url = "https://omeroweb.jax.org/api/"
        response = session.get(url, verify=True)

        content = response.json()['data']
        print(content)
        forms = content[-1]

        base_url = forms['url:base']
        r = session.get(base_url)
        print(base_url)
        print(r.content)
        urls = r.json()
        servers_url = urls['url:servers']

        """Get CSRF Token"""
        token_url = urls["url:token"]
        csrf = session.get(token_url).json()["data"]

        """List the servers available to connect to"""
        servers = session.get(servers_url).json()['data']
        servers = [s for s in servers if s['server'] == 'omero']
        if len(servers) < 1:
            raise Exception("Found no server called 'omero'")
        server = servers[0]
        print('server')
        print(server)

        """Log In To Omero"""
        login_url = urls['url:login']
        print(login_url)
        session.headers.update({'X-CSRFToken': csrf,
                                'Referer': login_url})
        payload = {'username': input("Username: "),
                   'password': getpass("Password: "),
                   'server': server['id']
                   }
        r = session.post(login_url, data=payload)
        print(r.content)
        login_rsp = r.json()

        try:
            r.raise_for_status()
        except exceptions.HTTPError as e:
            # Whoops it wasn't a 200
            print("Error {}".format(e))
            raise
        assert login_rsp['success']

        print(f'login response: {login_rsp}')

        # Query the database
        urlMap = collections.defaultdict(list)
        here = os.path.dirname(os.path.abspath(__file__))
        sqlfile = os.path.join(here, 'omeros.sql')
        fptr = open(sqlfile, "r")
        sql = fptr.read()
        conn = db_init()

        path = "C:/Program Files/KOMP/ImageDownload/KOMP_image_uploader/Omeros"
        for key, val in urlMap.items():
            dest = path + "/" + key
            try:
                os.mkdir(dest)

            except FileExistsError as e:
                print(e)

            for pair in val:
                link, test_code = pair[0], pair[1]
                print(link)
                omeroId = link.split("/")[-1].strip()
                images_url = urls['url:images'] + str(omeroId)
                print(images_url)
                # get the filename from OMERO GET https://omeroweb.jax.org/api/v0/m/images/nnn - then get the "Name"
                # attribute of the response.
                resp = session.get(images_url)
                j = resp.json()
                name = j["data"]["Name"].strip()
                print(name)
                frm, to = name.find("["), name.find("]")
                name = name.replace(name[frm:to + 1], "")
                name = name.strip()
                fName = str(test_code) + name
                print(fName)
                # File name has junk in it. Like " []". Needs a tif extension instead.
                downloadFileUrl = base_url.replace("api/v0/", "webgateway/archived_files/download/")
                downloadFileUrl = downloadFileUrl + str(omeroId)
                print(downloadFileUrl)

                """Starting to download files"""
                with session.get(downloadFileUrl, stream=True) as r:
                    r.raise_for_status()
                    with open(dest + "/" + fName, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            # If you have chunk encoded response uncomment if
                            # and set chunk_size parameter to None.
                            # if chunk:
                            f.write(chunk)
                    f.close()

            """Send images to SFTP server"""
            fileList = os.listdir(path)
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
            monkey.patch_all()

            for file in fileList:
                with pysftp.Connection(host="bhjlk01.jax.org", username="jlkinternal",
                                       password="t1m3st4mp!", cnopts=cnopts) as sftp:
                    sftp.cwd("/srv/ftp/images/" + key)
                    localPath = path + "/" + file
                    remotePath = "/srv/ftp/images/" + key + "/" + file
                    sftp.put(localPath, remotePath)

                    sftp.close()

            """Empty directory after send all files related to one procedure key"""
            for filename in os.listdir(path):
                file_path = os.path.join(path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))

        conn.close()

    '''Download files from drive'''
    if sys.argv[1] == "-p":
        urlMap = collections.defaultdict(list)
        here = os.path.dirname(os.path.abspath(__file__))
        sqlfile = os.path.join(here, 'phenotype_drive.sql')
        fptr = open(sqlfile, "r")
        sql = fptr.read()
        conn = db_init()

        # targetPath = "C:/Program Files/KOMP/ImageDownload/KOMP_image_uploader/"
        targetPath = "/Users/chent/Desktop/KOMP_Project/KOMP_image_uploader/Phenotype"
        fileLocationMap = parseQueryResult(conn, sql, target=targetPath)
        # print(fileLocations)
        # print(fileLocationMap)

        # srcPath = "//bht2stor.jax.org/"
        monkey.patch_all()
        srcPath = "/Volumes/"
        download_from_drive(fileLocationMap, source=srcPath, target=targetPath)
        '''
        fileLocationsMap = download_from_drive(conn)
        cursor = conn.cursor(buffered=True, dictionary=True)
        cursor.execute(sql)
        queryResult = cursor.fetchall()
        print(queryResult[0]["ProcedureDefinition"])
        for dict_ in queryResult:
            for key, val in dict_.items():
                if key == "ExternalID":
                    imgName = dict_["OutputValue"].split("\\")[-1]
                    #print(imgName)
                    subDir = dict_["OutputValue"].split("\\")[-2]
                    print(subDir)
                    #Directory in drive -> dict_["ProcedureDefinition"]
                    urlMap[val].append((dict_["ProcedureDefinition"], subDir, imgName))

        #print(list(urlMap)[0])
        # path = "C:/Program Files/KOMP/ImageDownload/KOMP_image_uploader/Phenotype"
        

        targetPath = "/Users/chent/Desktop/KOMP_Project/KOMP_image_uploader/Phenotype"



        for externalId, pairs in fileLocationsMap.items():
            print(type(pairs))
            dest = path + "/" + externalId
            try:
                os.mkdir(dest)

            except FileExistsError as e:
                print(e)

            """Start to download files from drive"""
            for pair in pairs: 
                Dir, subDir, image = pair[0].strip(), pair[1], pair[2]
                rootDir = f"/Volumes/phenotype/{Dir}"
                print(os.listdir(rootDir))
    '''


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
