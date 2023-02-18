import asyncio
import uvicorn
import json
import datetime

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request

from mysql_rq import test_mysql_connection, selectRequest, insertRequest
from utilities import checkExistingUID, get_balance, getBetslipLive

live = FastAPI(title="Bet4Live", description="Bet4Live API for score, users coins and users betslip",
               version="1.0.0", terms_of_service="https://bet4free.app", debug=True)

REFRESH_TIME = 1


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
        return dict(event="close", data="9001", id=datetime.datetime.now())

    async def event_stream():

        sse_betslip_id: int = 0
        sse_balance_id: int = 0

        first_load: bool = True
        balance_has_changed: bool = False
        betslip_has_changed: bool = False
        close_has_changed: bool = False
        try:
            while True:
                res = {}
                if first_load:
                    balance: int = get_balance(uid)
                    res["data"] = balance
                    res["id"] = sse_balance_id
                    yield dict(event="balance", data=json.dumps(res))
                    sse_balance_id += 1

                    betslip: list = getBetslipLive(uid)
                    res["data"] = betslip
                    res["id"] = sse_betslip_id
                    yield dict(event="betslip", data=json.dumps(res))
                    sse_betslip_id += 1

                    first_load = False

                rq = "SELECT (event) FROM user_live WHERE uid = %s AND yielded = 0"
                res, nb = selectRequest(rq, (uid,))
                if nb > 0:
                    for event in res:
                        if event[0] == "balance":
                            balance: int = get_balance(uid)
                            res = {"data": balance, "id": sse_balance_id}
                            yield dict(event="balance", data=json.dumps(res))
                            sse_balance_id += 1

                            balance_has_changed = True

                        if event[0] == "betslip":
                            betslip: list = getBetslipLive(uid)
                            res = {"data": betslip, "id": sse_betslip_id}
                            yield dict(event="betslip", data=json.dumps(res))
                            sse_betslip_id += 1

                            betslip_has_changed = True

                        if event[0] == "close":
                            yield dict(event="close", data="9001", id=None)
                            sse_betslip_id = 0
                            sse_balance_id = 0
                            close_has_changed = True

                        if balance_has_changed:
                            # Change the yielded value to 1
                            rq = "UPDATE user_live SET yielded = 1 WHERE uid = %s AND event = 'balance'"
                            insertRequest(rq, (uid,))

                        if betslip_has_changed:
                            # Change the yielded value to 1
                            rq = "UPDATE user_live SET yielded = 1 WHERE uid = %s AND event = 'betslip'"
                            insertRequest(rq, (uid,))

                        if close_has_changed:
                            # Change the yielded value to 1
                            rq = "UPDATE user_live SET yielded = 1 WHERE uid = %s AND event = 'close'"
                            insertRequest(rq, (uid,))

                await asyncio.sleep(REFRESH_TIME)

        except asyncio.CancelledError as e:
            yield dict(event="close", data="9001")
            raise e

    return EventSourceResponse(event_stream())


if __name__ == "__main__":
    test_mysql_connection()
    uvicorn.run("live:live", host="0.0.0.0", port=5002, reload=True)
