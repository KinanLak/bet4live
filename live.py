from utilities import checkExistingUID, get_balance, getBetslipLive
from mysql_rq import test_mysql_connection
from starlette.requests import Request
from sse_starlette.sse import EventSourceResponse
from fastapi.responses import PlainTextResponse
from fastapi import FastAPI
import asyncio
import logging
import sys
import time

import uvicorn

_log = logging.getLogger(__name__)
log_fmt = r"%(asctime)-15s %(levelname)s %(name)s %(funcName)s:%(lineno)d %(message)s"
datefmt = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(format=log_fmt, level=logging.DEBUG, datefmt=datefmt)


live = FastAPI(title="Bet4Live", description="Bet4Live API for score, users coins and users betslip",
               version="1.0.0", terms_of_service="https://bet4free.com", debug=True)

REFRESH_TIME = 1

if sys.platform == "darwin":
    SSE_FILES_PATH = ""
else:
    SSE_FILES_PATH = "/home/ubuntu/out/"


def printf(text):
    file = open(SSE_FILES_PATH + "draft.txt", "a")
    file.write(str(text)+"\n")
    file.close()


@live.get("/", response_class=PlainTextResponse)
async def index():
    prompt = """
    Welcome to Bet4Live API

    This API is used to get live data from the server to the client

    The API is divided into 2 parts:

    1. Score (Not available yet) -> /score
    2. Users coins and users betslip -> /user?uid=<user_id>
    """
    return prompt


@live.get("/user")
def sse(request: Request, uid: str = "Undefined"):

    with open(SSE_FILES_PATH + "draft.txt", "a") as draftfile:
        draftfile.write("HEY TOI LA")
        draftfile.close()

    printf("UID: " + uid)

    if not checkExistingUID(uid):
        return {"event": "error", "timestamp": int(time.time()), "data": 9001}

    async def event_stream():
        first_load: bool = True
        printf("First load: " + str(first_load))
        printf("DÉBUT DE LA BOUCLE")
        try:
            while True:
                if first_load:
                    balance: int = get_balance(uid)
                    betslip: list = getBetslipLive(uid)
                    yield "event: betslip\ndata: " + str(balance) + "\nretry: 10000\n\nevent: betslip\ndata: " + str(betslip) + "\nretry: 10000\n\n"

                    first_load = False

                with open(SSE_FILES_PATH + "balance.txt", "r") as balancefile:
                    lines = balancefile.readlines()
                    balancefile.close()

                if len(lines) > 0:
                    for line in lines:
                        line_notrail = line.strip()
                        if line_notrail == uid:
                            printf("iCI LA CONDITION EST VALIDE SALOPE")
                            balance: int = get_balance(uid)

                            printf("ICI CA YIELD FDP")
                            yield "event: balance\ndata: " + str(balance) + "\nretry: 10000\n\n"

                            # Remove the line from the file
                            lines.remove(line)
                            printf("LIGNE VA ETRE SUPPRIMÉ")
                            with open(SSE_FILES_PATH + "balance.txt", "w") as balancefile:
                                balancefile.writelines(lines)
                                balancefile.close()
                            printf("LIGNE EST SUPPRIMÉ")
                            first_load = False
                            break

                with open(SSE_FILES_PATH + "betslip.txt", "r") as betslipfile:
                    lines = betslipfile.readlines()
                    betslipfile.close()
                if len(lines) > 0:
                    for line in lines:
                        line_notrail = line.strip()

                        if line_notrail == uid:
                            betslip: list = getBetslipLive(uid)

                            # Yield in correct SSE format
                            yield "event: betslip\ndata: " + str(betslip)+"\nretry: 10000\n\n"

                            # Remove the line from the file
                            lines.remove(line)
                            with open(SSE_FILES_PATH + "betslip.txt", "w") as betslipfile:
                                betslipfile.writelines(lines)
                                betslipfile.close()

                            first_load = False
                            break

                printf("ICI CA DORT")
                await asyncio.sleep(REFRESH_TIME)

        except asyncio.CancelledError as e:
            printf(
                f"Disconnected from client (via refresh/close) {request.client}")
            printf(e)
            raise e

    return EventSourceResponse(event_stream())


if __name__ == "__main__":
    test_mysql_connection()
    uvicorn.run("live:live", host="127.0.0.1", port=5002,
                log_level="trace", log_config=None, reload=True)
