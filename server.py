import socket
import threading
import pyodbc
from datetime import datetime

from BTL.models.order import order

HOST = "localhost"
SERVER_PORT = 9050
FORMAT = "utf8"

LOGIN = "login"
ORDER = "order"
HISTORY = "history"
EXIT = "exit"
LOGOUT = "logout"

LOGIN_FAILED = "Login failed"
BEING_LOGGED_IN = "Your account is being logged in in other place!"
CHECK_ACCOUNT = "Please check your user name or password!"
CHECK_SYMBOL_STOCK = "Please check your symbol stock"
ACCOUNT_BEEN_LOGIN = "Your account has been login!"
DONT_ENOUGH_MONEY = "You don't have enough money to buy!"
DONT_ENOUGH_STOCK = "You don't have enough stock to sell!"
ERROR = "Error"
LOGIN_TO_ORDER = "Please login to order!"
CLIENT_NOT_LOGGED_IN = "Client have not logged in!"
LOGIN_TO_WATCH = "Please login to watch history!"
LOGOUT_SUCCESS = "Log out success"

connection = {}

# connect to db
conx = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};'
                      'Server=LAPTOP-7AIEH3G7;Database=Stock_Exchange;'
                      'Trusted_Connection=yes;')

cursor = conx.cursor()


# get current time
def getCurrentTime():
    now = datetime.now()
    current_time = now.strftime("%Y/%m/%d %H:%M:%S")
    return current_time

# check login
def checkLoginStatus(user_id):
    loginStatus = cursor.execute("select login_status from tbl_user where user_id = ?", str(user_id)).fetchall()
    return loginStatus[0][0]

# function to check client's order (Stock's symbol, user stock amount, user surplus)
def checkSymbolStock(client_order):
    listStock = cursor.execute(f"select * from tbl_Stock where stock_symbol = ?", client_order[2]).fetchall()
    if len(listStock) != 0:
        return True
    return False

# sell
def checkAmount(client_order):
    user_amount = cursor.execute("select amount from tbl_userStock where user_id = ? and symbol_stock = ?", client_order[0], client_order[2]).fetchall()
    if user_amount[0][0] >= int(client_order[3]):
        return True
    return False

# buy
def checkUserSurplus(client_order):
    user_surplus = cursor.execute("select surplus from tbl_user where user_id = ?", client_order[0]).fetchall()
    if user_surplus[0][0] >= (int(client_order[3]) * int(client_order[4])):
        return True
    return False

# get max index in table
def maxIndex(tableName):
    querry = f'select top 1 order_id from {tableName} order by (order_id + 0) desc'
    index = cursor.execute(querry).fetchall()
    if len(index) == 0:
        return 0
    return int(index[0][0])

# handle order
def handleOrder(client_order):
    if client_order[1] == 'buy':
        cursor.execute("insert tbl_buy values(?, ?, ?, ?, ?, ?, ?)", str(maxIndex('tbl_buy') + 1), client_order[0],
                       client_order[2], client_order[3], client_order[4], getCurrentTime(), None)
        conx.commit()
        handleOrderBuy(client_order)


    elif client_order[1] == 'sell':
        cursor.execute("insert tbl_sell values(?, ?, ?, ?, ?, ?, ?)", str(maxIndex('tbl_sell') + 1), client_order[0],
                       client_order[2], client_order[3], client_order[4], getCurrentTime(), None)
        conx.commit()
        handleOrderSell(client_order)

# handle when buy
def handleOrderBuy(client_order):
    lst_sell = cursor.execute("select * from tbl_sell where time_success is null order by time_order asc").fetchall()
    for x in lst_sell:
        if x[1] != client_order[0] and x[2] == client_order[2] and x[3] == int(client_order[3]) and x[4] == int(
                client_order[4]):
            cursor.execute("update tbl_sell set time_success = ? where order_id = ?", getCurrentTime(), x[0])
            conx.commit()
            cursor.execute("update tbl_buy set time_success = ? where order_id = ?", getCurrentTime(),
                           str(maxIndex('tbl_buy')))
            conx.commit()
            changeWalletBuy(client_order[0], client_order[2], int(client_order[3]), int(client_order[4]))
            changeWalletSell(x[1], x[2], int(x[3]), int(x[4]))
            connection[client_order[0]].sendall(f"Your order: Buy: {client_order[2]} - {client_order[3]} - {client_order[4]} success at {getCurrentTime()}".encode(FORMAT))
            connection[x[1]].sendall(
                f"Your order: Sell: {x[2]} - {x[3]} - {x[4]} success at {getCurrentTime()}".encode(FORMAT))
            print("Buy success")
            return

# handle when sell
def handleOrderSell(client_order):
    lst_buy = cursor.execute("select * from tbl_buy where time_success is null order by time_order asc").fetchall()
    for x in lst_buy:
        if x[1] != client_order[0] and x[2] == client_order[2] and x[3] == int(client_order[3]) and x[4] == int(
                client_order[4]):
            cursor.execute("update tbl_buy set time_success = ? where order_id = ?", getCurrentTime(), x[0])
            conx.commit()
            cursor.execute("update tbl_sell set time_success = ? where order_id = ?", getCurrentTime(),
                           str(maxIndex('tbl_sell')))
            conx.commit()
            changeWalletSell(client_order[0], client_order[2], int(client_order[3]), int(client_order[4]))
            changeWalletBuy(x[1], x[2], int(x[3]), int(x[4]))
            connection[x[1]].sendall(f"Your order: Buy: {x[2]} - {x[3]} - {x[4]} success at {getCurrentTime()}".encode(FORMAT))
            connection[client_order[0]].sendall(f"Your order: Sell: {client_order[2]} - {client_order[3]} - {client_order[4]} success at {getCurrentTime()}".encode(FORMAT))
            print("Sell success")
            return

# trừ tiền vào số dư của client - update
# cộng số lượng chứng khoán ở ví - insert/update
def changeWalletBuy(user_id, symbol_stock, amount, price):
    user_surplus = cursor.execute("select surplus from tbl_user where user_id = ?", user_id).fetchall()
    total_price = int(amount) * int(price)
    money_earned = total_price - total_price * 0.1
    new_surplus = float(user_surplus[0][0]) + money_earned
    # change surplus
    cursor.execute("update tbl_user set surplus = ? where user_id = ?", new_surplus, user_id)
    conx.commit()
    # change amount stock
    user_amount_stock = cursor.execute("select amount from tbl_userStock where user_id = ? and symbol_stock = ?",
                                       user_id, symbol_stock).fetchall()
    new_amount = user_amount_stock[0][0] + amount
    cursor.execute("update tbl_userStock set amount = ? where user_id = ? and symbol_stock = ?", new_amount, user_id,
                   symbol_stock)
    conx.commit()

# cộng tiền vào số dư của client - update
# trừ số lượng chứng khoán ở ví - update
def changeWalletSell(user_id, symbol_stock, amount, price):
    user_surplus = cursor.execute("select surplus from tbl_user where user_id = ?", user_id).fetchall()
    total_price = int(amount) * int(price)
    new_surplus = user_surplus[0][0] - total_price
    # change surplus
    cursor.execute("update tbl_user set surplus = ? where user_id = ?", new_surplus, user_id)
    conx.commit()
    user_amount_stock = cursor.execute("select amount from tbl_userStock where user_id = ? and symbol_stock = ?",
                                       user_id, symbol_stock).fetchall()

    # change amount stock
    user_amount_stock = cursor.execute("select amount from tbl_userStock where user_id = ? and symbol_stock = ?",
                                       user_id, symbol_stock).fetchall()
    if len(user_amount_stock) != 0:
        new_amount = user_amount_stock[0][0] - amount
        cursor.execute("update tbl_userStock set amount = ? where user_id = ? and symbol_stock = ?", new_amount,
                       user_id, symbol_stock)
        conx.commit()
    else:
        cursor.execute("insert tbl_userStock values(?, ?, ?)", user_id, symbol_stock, amount)
        conx.commit()

def converRowToList(list):
    new_list = []
    for x in list:
        new_list.append([str(x[0]), str(x[1]), str(x[2]), str(x[3]), str(x[4]), str(x[5]), str(x[6])])
    return new_list

def sendList(client, lst):
    for item in lst:
        client.sendall(item.encode(FORMAT))
        # wait response
        client.recv(1024)

    msg = "end"
    client.send(msg.encode(FORMAT))

def recvList(conn):
    lst = []

    item = conn.recv(1024).decode(FORMAT)

    while item != "end":
        lst.append(item)
        # response
        conn.sendall(item.encode(FORMAT))
        item = conn.recv(1024).decode(FORMAT)

    return lst

def serverLogin(conn):
    # receive account from client
    client_account = recvList(conn)

    # query data: password
    cursor.execute("select user_id from tbl_user where user_name = ? and password = ?", client_account[0], client_account[1])
    user_id = cursor.fetchall()    # fetchall trả về kiểu list còn fetchone trả về kiểu row

    # verify login
    msg = "ok"

    if len(user_id) != 0:
        data_id = user_id[0][0]
        if checkLoginStatus(data_id) == 1:
            msg = BEING_LOGGED_IN
            print(LOGIN_FAILED)
        else:
            msg = "Login successfully - " + data_id
            print("Login successfully - User Id: " + data_id)
            connection[data_id] = conn
            cursor.execute("update tbl_user set login_status = 1 where user_id = ?", data_id)
            cursor.commit()
    else:
        msg = CHECK_ACCOUNT
        print(LOGIN_FAILED)

    conn.sendall(msg.encode(FORMAT))

def serverOrder(conn):
    # receive order from client
    client_order = recvList(conn)

    # check login
    if client_order == [LOGIN_TO_ORDER]:
        conn.sendall(LOGIN_TO_ORDER.encode(FORMAT))
        print(CLIENT_NOT_LOGGED_IN)
        return

    print("Client order: ") # ['1', 'buy', 'tcb', '10', '50']
    print(client_order)

    # check order detail (stock symbol, amount, surplus)
    msg = "Order Successfully"

    if not checkSymbolStock(client_order):
        msg = CHECK_SYMBOL_STOCK
        # send response to client
        conn.sendall(msg.encode(FORMAT))
        print("This symbol stock not exist!")
        return
    else:
        if client_order[1].lower() == 'buy':
            if not checkUserSurplus(client_order):
                msg = DONT_ENOUGH_MONEY
                # send response to client
                conn.sendall(msg.encode(FORMAT))
                print("Client don't have enough money to buy!")
                return
        else:
            if not checkAmount(client_order):
                msg = DONT_ENOUGH_STOCK
                # send response to client
                conn.sendall(msg.encode(FORMAT))
                print("Client don't have enough stock to sell!")
                return

    # send response to client
    conn.sendall(msg.encode(FORMAT))

    # handle order if all request valid
    handleOrder(client_order)

def watchHistory(conn):
    # receive userId from client
    userId = conn.recv(1024).decode(FORMAT)

    # check login
    if userId == "0":
        conn.sendall(LOGIN_TO_WATCH.encode(FORMAT))
        print(CLIENT_NOT_LOGGED_IN)
        return

    # query to get history
    # buy
    row_buy = cursor.execute("select * from tbl_buy where user_id = ? order by time_success", userId).fetchall()
    list_buy = converRowToList(row_buy)
    # sell
    row_sell = cursor.execute("select * from tbl_sell where user_id = ? order by time_success", userId).fetchall()
    list_sell = converRowToList(row_sell)

    # send history to client
    # send length of list buy
    conn.sendall(str((len(list_buy))).encode(FORMAT))
    for x in list_buy:
        sendList(conn, x)
    conn.recv(1024).decode(FORMAT)

    # send length of list sell
    conn.sendall(str(len(list_sell)).encode(FORMAT))
    for x in list_sell:
        sendList(conn, x)
    conn.recv(1024).decode(FORMAT)

def serverLogout(conn):
    # receive userId from client
    userId = conn.recv(1024).decode(FORMAT)

    # check login
    if userId == "0":
        conn.sendall("You have not logged in".encode(FORMAT))
        return

    # send message log out success to client
    cursor.execute("update tbl_user set login_status = 0 where user_id = ?", userId)
    cursor.commit()
    conn.sendall(LOGOUT_SUCCESS.encode(FORMAT))
    print("User: " + userId + " " + LOGOUT_SUCCESS)


def handleClient(conn, addr):
    print("conn:", conn.getsockname())

    msg = None
    while msg != EXIT:
        msg = conn.recv(1024).decode(FORMAT)
        print("client ", addr, "says", msg)

        if msg == LOGIN:
            # response
            conn.sendall(msg.encode(FORMAT))
            serverLogin(conn)
        elif msg == ORDER:
            # response
            conn.sendall(msg.encode(FORMAT))
            serverOrder(conn)
        elif msg == HISTORY:
            conn.sendall(msg.encode(FORMAT))
            watchHistory(conn)
        elif msg == LOGOUT:
            conn.sendall(msg.encode(FORMAT))
            serverLogout(conn)

    print("client ", addr, "finished")
    print(conn.getsockname(), "closed")
    for key, value in dict(connection).items():
        if value == conn:
            del connection[key]
    conn.close()


# main
if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.bind((HOST, SERVER_PORT))
    s.listen()

    print("SERVER SIDE")

    print("server:", HOST, SERVER_PORT)
    print("Waiting for Client")

    nClinet = 0
    while nClinet < 3:
        try:
            conn, addr = s.accept()

            thr = threading.Thread(target=handleClient, args=(conn, addr))
            thr.daemon = False   # khi main exit => kill all thread
            thr.start()

        except:
            print(ERROR)

        nClinet += 1


    print("End")
    input()

    s.close()
    conx.close()
    connection.clear()

