# This is a sample Python script.
import collections
import os
import shutil

from errno import errorcode
import socket
from urllib3.connection import HTTPConnection
import requests
from getpass import getpass
import mysql.connector
from requests import exceptions
import pysftp
import collections


# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings

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


def init() -> mysql.connector:
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


def main():
    HTTPConnection.default_socket_options = (HTTPConnection.default_socket_options + [
        (socket.SOL_SOCKET, socket.SO_SNDBUF, 1000000),
        (socket.SOL_SOCKET, socket.SO_RCVBUF, 1000000)
    ])
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
    conn = init()
    cursor = conn.cursor(buffered=True, dictionary=True)
    cursor.execute(sql)
    queryResult = cursor.fetchall()
    print(queryResult[0])
    for dict_ in queryResult:
        # print(dict_)
        for key, val in dict_.items():

            if key == "ExternalID":
                link = dict_["OutputValue"]
                testCode = dict_["TestCode"]
                urlMap[val].append((link, testCode))
    print(urlMap)

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
            name = name.replace(name[frm:to+1], "")
            fName = str(test_code) + name
            print(fName)
            # File name has junk in it. Like " []". Needs a tif extension instead.
            downloadFileUrl = base_url.replace("api/v0/", "webgateway/archived_files/download/")
            downloadFileUrl = downloadFileUrl + str(omeroId)
            print(downloadFileUrl)

            #path = key
            path = "/Users/chent/Desktop/KOMP_Project/download_from_omero/Omero_Files"

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

        for file in fileList:
            with pysftp.Connection(host="bhjlk01.jax.org", username="jlkinternal",
                                   password="t1m3st4mp!", cnopts=cnopts) as sftp:
                sftp.cwd("/srv/ftp/images/"+key)
                sftp.put(file)
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
        

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
