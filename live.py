import time
import asyncio
import uvicorn

from fastapi import FastAPI, Request
from starlette.responses import StreamingResponse
from mysql_rq import test_mysql_connection
from utilities import get_balance


live = FastAPI(title="Bet4Live", description="Bet4Live API for score, users coins and users betslip",
               version="1.0.0", terms_of_service="https://bet4free.com", debug=True)


# SSE_FILES_PATH = "/home/ubuntu/out/"
SSE_FILES_PATH = ""

REFRESH_TIME = 1


@live.get("/")
async def index():
    prompt = """
    Welcome to Bet4Live API

    This API is used to get live data from the server to the client

    The API is divided into 2 parts:

    1. Score (Work in progress) -> /score
    2. Users coins and users betslip -> /user&uid=<user_id>
    """
    return prompt


@live.get("/user")
async def sse(request: Request, uid: str = "Undefined"):
    if uid == "Undefined":
        return {"error": "User ID wasn't defined"}

    async def event_stream():
        first_load: bool = True
        while True:
            if first_load:
                balance: int = get_balance(uid)
                yield '{"event":"' + "balance" + '",\n' + '"timestamp":' + str(int(time.time())) + ",\n" + '"data":' + str(balance) + "}\n\n"
                first_load = False

            with open(SSE_FILES_PATH + "balance.txt", "r") as file:
                lines = file.readlines()
                file.close()

            if len(lines) > 0:
                print(lines)
                for line in lines:
                    line_notrail = line.strip()
                    if line_notrail == uid:
                        print("heha")
                        balance: int = get_balance(uid)

                        yield '{"event":"' + "balance" + '",\n' + '"timestamp":' + str(int(time.time())) + ",\n" + '"data":' + str(balance) + "}\n\n"

                        # Remove the line from the file
                        lines.remove(line)
                        with open(SSE_FILES_PATH + "balance.txt", "w") as file:
                            file.writelines(lines)
                            file.close()

                        first_load = False
                        break

                await asyncio.sleep(REFRESH_TIME)

            disconnected = await request.is_disconnected()
            if disconnected:
                print("Client disconnected")
                break
    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    test_mysql_connection()
    uvicorn.run("live:live", host="127.0.0.1", port=5002, reload=True)
