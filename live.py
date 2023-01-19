import sys
import time
import asyncio
import uvicorn

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request

from mysql_rq import test_mysql_connection
from utilities import checkExistingUID, get_balance, getBetslipLive

live = FastAPI(title="Bet4Live", description="Bet4Live API for score, users coins and users betslip",
               version="1.0.0", terms_of_service="https://bet4free.app", debug=True)

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

    if not checkExistingUID(uid):
        return {"event": "error", "timestamp": int(time.time()), "data": 9001}

    async def event_stream():
        first_load: bool = True
        try:
            while True:
                res = {}
                if first_load:
                    balance: int = get_balance(uid)
                    res["event"] = "balance"
                    res["data"] = balance
                    yield res

                    betslip: list = getBetslipLive(uid)
                    res["event"] = "betslip"
                    res["data"] = betslip
                    yield res

                    first_load = False

                with open(SSE_FILES_PATH + "balance.txt", "r") as balancefile:
                    lines = balancefile.readlines()
                    balancefile.close()

                if len(lines) > 0:
                    for line in lines:
                        line_notrail = line.strip()
                        if line_notrail == uid:
                            balance: int = get_balance(uid)

                            res = {"event": "balance", "data": balance}
                            yield res

                            # Remove the line from the file
                            lines.remove(line)
                            with open(SSE_FILES_PATH + "balance.txt", "w") as balancefile:
                                balancefile.writelines(lines)
                                balancefile.close()
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
                            res = {"event": "betslip", "data": betslip}
                            yield res

                            # Remove the line from the file
                            lines.remove(line)
                            with open(SSE_FILES_PATH + "betslip.txt", "w") as betslipfile:
                                betslipfile.writelines(lines)
                                betslipfile.close()

                            first_load = False
                            break

                await asyncio.sleep(REFRESH_TIME)

        except asyncio.CancelledError as e:
            raise e

    return EventSourceResponse(event_stream())


if __name__ == "__main__":
    test_mysql_connection()
    uvicorn.run("live:live", host="127.0.0.1", port=5002, reload=True)
