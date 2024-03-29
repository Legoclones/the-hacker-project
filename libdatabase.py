################################################################
#
# All functions located here relate specifically to maintaining
# and updating the local database file. 
# 
# Functions:
#  - connect_to_db - connects to local db
#  - IPDB_to_localDB - syncs local db with online IP database
#  - get_IP_attributes - returns attributes of an IP
#  - set_IP_attributes - sets attributes of an IP
#  - get_IP_list - returns a list of all IPs
#
################################################################


### IMPORTS ###
# global imports
import sqlite3

# local imports
from libbasic import get_page

# constants
VALID_COLUMN_NAMES = ["ipAddress", "name", "type", "page", "admin", "minimum_protect", "owned", "running", "files", "cpu", "memory", "bandwidth", "lastlog", "lastupdated"]


#####
# 
# Parameter(s):
#     none
# Return value(s):
#     Sqlite3 connection object that can be used for SQL queries
# Description:
#     Creates a connection to the sqlite3 database, local.db
#     and returns a connection object to allow other functions
#     to execute queries. If the servers table does not exist,
#     then it will be automatically created.
# 
#####
def connect_to_db():
    # initialize database
    conn = sqlite3.connect('local.db', isolation_level=None)

    # create table if it doesn't exist
    conn.execute('CREATE TABLE if not exists servers (ipAddress TEXT PRIMARY KEY, name TEXT, type TEXT, page TEXT, admin BOOLEAN, minimum_protect TEXT, owned BOOLEAN, running TEXT, files TEXT, cpu TEXT, memory TEXT, bandwidth TEXT, lastlog TEXT, lastupdated TEXT)')

    return conn


#####
# 
# Parameter(s):
#     IP (optional) - a specific IP can be updated instead of all IPs
# Return value(s):
#     none
# Description:
#     Extracts all the information from the local IP database and
#     inserts it into the local Sqlite3 file, local.db. If no IP is
#     specified, then all IPs are updated. This option is added in
#     to decrease update times when only specific information is
#     needed.
# 
#####
def IPDB_to_localDB(IP="none"):
    # connect to DB
    conn = connect_to_db()
    cursor = conn.cursor()

    # loops through Public, Private, and Secret servers to determine type
    exts = ['pub', 'priv', 'sec']
    for ext in exts:

        # determine type
        if ext == "pub":
            server_type = "Public"
        elif ext == "priv":
            server_type = "Private"
        else:
            server_type = "Secret"
        
        # loops through all pages
        counter = 0
        moreIPs = True

        while moreIPs:
            page = get_page("index.php?action=ip_db&a2="+ext+"&_o="+str(counter*20))

            # extra tables are added if connected
            if "Remote host web service" in page.text:
                trs = page.find_all("table")[16].find_all("tr")[::2][1:][:-1]
            else:
                trs = page.find_all("table")[9].find_all("table")[3].find_all("tr")[::2][1:][:-1]

            # no IPs on this page
            if len(trs) == 0:
                moreIPs = False

            # loop through elements and extract information
            for tr in trs:
                # get information
                ipAddress = tr.find_all("td")[0].find_all("td")[0].find_all("a")[0]["href"].split("&")[2][7:]
                name = ' '.join(tr.find_all("td")[5].get_text().split())
                admin = (tr.find_all("td")[6].get_text() == "Yes")
                owned = (tr.find_all("td")[7].get_text() == "Gateway")

                # if IP is not wanted
                if (ipAddress != IP) and (IP != "none"):
                    "Skip"

                # if IP exists already...
                elif len(cursor.execute("SELECT name FROM servers WHERE ipAddress = ?", (ipAddress,)).fetchall()) != 0:
                    # update information
                    cursor.execute("UPDATE servers SET name = ?, type = ?, page = ?, admin = ?, owned = ? WHERE ipAddress = ?", (name, server_type, str(counter), admin, owned, ipAddress))
                else:
                    # add new row to database
                    cursor.execute("INSERT INTO servers VALUES (?, ?, ?, ?, ?, '', ?, '', '', '', '', '', '', 'N/A')", (ipAddress, name, server_type, str(counter), admin, owned))

            # increase counter to see if more logs on next page
            counter += 1

    conn.close()


#####
# 
# Parameter(s):
#     IP - IP address of the desired server
#     attributes (optional) - an array of column names (or attributes) to return
# Return value(s):
#     Tuple of desired information in same order as attributes
#     -1 is returned if an error is encountered
# Description:
#     Given specific attributes/column names, a query is made to
#     the local database and the information is returned for the
#     IP address specified. If no attributes are specified, then 
#     all are returned.
# 
#####
def get_IP_attributes(IP, attributes=VALID_COLUMN_NAMES):
    # connect to DB
    conn = connect_to_db()
    cursor = conn.cursor()

    # ensure column names are correct (whitelisted)
    columns = ""
    for attribute in attributes:
        if attribute not in VALID_COLUMN_NAMES:
            print("Invalid column name")
            conn.close()
            return -1
        else:
            columns += attribute + ","

    # execute query
    results = cursor.execute("SELECT "+columns[:-1]+" FROM servers WHERE ipAddress = ?", (IP,)).fetchall()

    # ensure IP address exists and row returned
    if len(results)>0:
        conn.close()
        return results[0]
    else:
        print("Invalid IP address")
        conn.close()
        return -1


#####
# 
# Parameter(s):
#     IP - IP address of the desired server
#     attributes - an array of column names (or attributes) to update
#     values - an array of values to update the attributes with
# Return value(s):
#     0 is returned if no errors were encountered
#     -1 is returned if an error is encountered
# Description:
#     An array of attributes and values (same corresponding 
#     indexes) is passed to this function, which updates the 
#     local database with those attributes. 
# 
#####
def set_IP_attributes(IP, attributes, values):
    # connect to DB
    conn = connect_to_db()
    cursor = conn.cursor()

    if len(attributes) != len(values):
        print("Attributes and values must be same length")
        conn.close()
        return -1

    # ensure column names are correct (whitelisted)
    query = "UPDATE servers SET "
    for i in range(len(attributes)):
        if attributes[i] not in VALID_COLUMN_NAMES:
            print("Invalid column name")
            conn.close()
            return -1
        else:
            query += attributes[i] + " = '" + str(values[i]).replace("'","") + ("', " if i != len(attributes)-1 else "'")

    # execute query
    cursor.execute(query + " WHERE ipAddress = ?", (IP,))

    return 0
    

#####
# 
# Parameter(s):
#     none
# Return value(s):
#     List of all IP addresses in local.db
# Description:
#     Retrieves a list of all the IP addresses in the
#     database for mass scanning and reconnaissance.
# 
#####
def get_IP_list():
    # connect to DB
    conn = connect_to_db()
    cursor = conn.cursor()

    # execute query
    results = cursor.execute("SELECT ipAddress FROM servers").fetchall()

    # put IPs into list
    ips = []
    for row in results:
        ips.append(row[0])

    return ips


# used for testing functions above
if __name__ == "__main__":
    ""