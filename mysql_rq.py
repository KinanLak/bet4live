import json
import platform
import mysql.connector

DEBUG = False


def get_mysql_args() -> dict:
    # Open the secrets.json file and return the mysql_args dict
    # The pats change depending on the OS (MacOS or Linux)
    if platform.system() == "Darwin":
        path = "/Users/kinanlakhdar/secrets.json"
    elif platform.system() == "Linux":
        path = "/home/ubuntu/const/secrets.json"
    else:
        raise OSError("Unknown OS")
    with open(path, "r") as f:
        mysql_args = json.load(f)
    return mysql_args


mysql_args = get_mysql_args()


class MySQL_Error(Exception):
    """Expended Exception class for MySQL errors."""
    pass


def test_mysql_connection():
    print("\nAttemption connection to database",
          mysql_args['database'], "with user", mysql_args['user'])
    con = mysql.connector.connect(**mysql_args)
    print("Connected to:", con.get_server_info(), "\n")
    con.close()


def selectRequest(rq: str, args: tuple | None = None, amount: str | int = 1) -> tuple:
    """
    Returns a tuple with the result of the request and the number of entry.

    `rq` : The request to execute (str) (ex: "SELECT * FROM user_main WHERE username = %s").\n
    `args` : The arguments to pass to the request (tuple) (ex: ("nathan",)) [Optional].\n
    `amount` : The number of entry to return (int) or "all" [Optional].
    """
    con = mysql.connector.connect(**mysql_args)
    with con as db:
        db.autocommit = True
        with db.cursor(buffered=True) as cur:
            if DEBUG:
                print("REQUEST = ", rq, "ARGS = ", args,
                      "AMOUNT =", amount, sep="\n")
            cur.execute(rq, args)
            nb = cur.rowcount
            if amount == "all":
                res = cur.fetchall()
            elif type(amount) == int:
                res = cur.fetchmany(int(amount))
            else:
                raise MySQL_Error("Amount must be an integer or 'all'")
            cur.close()
            con.close()
    return res, nb


def insertRequest(rq: str, args: tuple | None = None) -> bool:
    con = mysql.connector.connect(**mysql_args)
    with con as db:
        db.autocommit = True
        with db.cursor(buffered=True) as cur:
            try:
                if DEBUG:
                    print("REQUEST = ", rq, "ARGS = ", args, sep="\n")
                cur.execute(rq, args)
                cur.close()
                con.close()
                return True
            except Exception:
                cur.close()
                con.close()
                raise MySQL_Error("Insertion failed")


def deleteRequest(rq, args=None) -> bool:
    con = mysql.connector.connect(**mysql_args)
    with con as db:
        db.autocommit = True
        with db.cursor(buffered=True) as cur:
            try:
                if DEBUG:
                    print("REQUEST = ", rq, "ARGS = ", args)
                cur.execute(rq, args)
                cur.close()
                con.close()
                return True
            except Exception:
                cur.close()
                con.close()
                raise MySQL_Error("Deletion failed")
