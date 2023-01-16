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
