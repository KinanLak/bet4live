from mysql_rq import selectRequest


def get_balance(user_id: str) -> int:
    """Get the balance of the user"""

    # Check if the user exists
    query = "SELECT COUNT(*) FROM user_main WHERE uid = %s"
    check_user, _ = selectRequest(query, (user_id,))
    check_user = check_user[0][0]

    if check_user == 0:
        return -1

    # Get the current balance
    query = "SELECT balance FROM user_main WHERE uid = %s"
    current_balance = selectRequest(query, (user_id,))[0][0][0]

    return current_balance


def getBetslipLive(uid: str) -> list[dict[str, str] | None]:
    """Get the betslip of the user, if the betslip is empty, return an empty list"""

    rq_current_betslip = "SELECT * FROM bets_selected WHERE uid = %s"
    current_betslip = selectRequest(rq_current_betslip, (uid,))
    if current_betslip[1] == 0:
        return []
    else:
        current_betslip = current_betslip[0][0]
    selected_bid = []
    selected_side = []
    for i in range(1, 25, 2):
        selected_bid.append(current_betslip[i])
        selected_side.append(current_betslip[i + 1])

    res = []
    for i in range(12):
        if selected_bid[i] is not None:
            res.append({"bid": selected_bid[i], "side": selected_side[i]})

    return res


def checkExistingUID(uid: str) -> bool:
    """Check if the uid exists in the database, if it doesn't, return False"""

    if uid == "Undefined":
        return False

    rq_check_uid = "SELECT COUNT(*) FROM user_main WHERE uid = %s"
    check_uid = selectRequest(rq_check_uid, (uid,))[0][0][0]
    if check_uid == 0:
        return False

    else:
        return True
