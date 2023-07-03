import socket
import pyodbc


HOST = "localhost"
SERVER_PORT = 9050
FORMAT = "utf8"

LOGIN = "login"
ORDER = "order"
HISTORY = "history"
USERID = "userid"
EXIT = "exit"
LOGOUT = "logout"

LOGIN_FAILED = "Login failed"
BEING_LOGGED_IN = "Your account is being logged in in other place!"
CHECK_ACCOUNT = "Please check your user name or password!"
ACCOUNT_BEEN_LOGIN = "Your account has been login!"
LOGIN_TO_ORDER = "Please login to order!"
CLIENT_SIDE = "CLIENT SIDE"
ERROR = "Error"
LOGIN_TO_WATCH = "Please login to watch history!"

CHECK_SYMBOL_STOCK = "Please check your symbol stock"
DONT_ENOUGH_MONEY = "You don't have enough money to buy!"
DONT_ENOUGH_STOCK = "You don't have enough stock to sell!"

userId = ""


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

def clientLogin(client):
    global userId
    account = []
    username = input("username: ")
    password = input("password: ")

    # clone input
    # username = 'buihuytu'
    # password = '123456'

    # check username and password validation
    account.append(username)
    account.append(password)

    # send account to server
    sendList(client, account)

    # receive response from server
    response = client.recv(1024).decode(FORMAT)
    if response != CHECK_ACCOUNT and response != BEING_LOGGED_IN:
        response = response.split(' - ')
        message = response[0]
        userId += response[1]
        print("Server response: " + message + ' - ' + userId)
    else:
        print("Server response: " + LOGIN_FAILED + ' - ' + response)

def clientOrder(client):
    order = []
    order_status = input('Enter Order: ').lower()
    stock_symbol = input('Enter Stock Symbol: ').lower()
    order_amount = input('Enter Amount: ')
    order_price = input('Enter Price: ')

    # clone input
    # order_status = 'sell'
    # stock_symbol = 'tcb'
    # order_amount = '10'
    # order_price = '50'

    # add info order (userId, order_status, stock_symbol, order_amount, order_price)
    order.append(userId)
    order.append(order_status)
    order.append(stock_symbol)
    order.append(order_amount)
    order.append(order_price)

    # send order request to server
    sendList(client, order)

    # receive response from server
    response = client.recv(1024).decode(FORMAT)
    print("Server response: " + response)

    if response != DONT_ENOUGH_MONEY and response != DONT_ENOUGH_STOCK and response != CHECK_SYMBOL_STOCK:
        print("Waiting to trade!")

        # receive order status from server
        response = client.recv(1024).decode(FORMAT)
        print("Server response: " + response)

def clientHistory(client):
    # send userId to server
    client.sendall(userId.encode(FORMAT))

    list_buy = []
    list_sell = []
    # receive history from server
    lenBuy = client.recv(1024).decode(FORMAT)
    for i in range(int(lenBuy)):
        list_buy.append(recvList(client))
    client.sendall("received".encode(FORMAT))

    lenBuy = client.recv(1024).decode(FORMAT)
    for i in range(int(lenBuy)):
        list_sell.append(recvList(client))
    client.sendall("received".encode(FORMAT))

    print("List buy:")
    index_buy = 0
    for x in list_buy:
        print(f"{index_buy} - {x[2]}, amount: {x[3]}, price: {x[4]}, at:{x[5]}, success at: {x[6]}")
        index_buy += 1
    print("List sell:")
    index_sell = 0
    for x in list_sell:
        print(f"{index_sell} - {x[2]}, amount: {x[3]}, price: {x[4]}, at:{x[5]}, success at: {x[6]}")
        index_sell += 1

def cilentLogout(client):
    # send userId to server
    client.sendall(userId.encode(FORMAT))

    # receive history from server
    message = client.recv(1024).decode(FORMAT)
    print("Server response: " + message)


def disconnectServer(client):
    conx = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};'
                          'Server=LAPTOP-7AIEH3G7;Database=Stock_Exchange;'
                          'Trusted_Connection=yes;')

    cursor = conx.cursor()
    cursor.execute("update tbl_user set login_status = 0 where user_id = ?", userId)
    cursor.commit()


if __name__ == "__main__":
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(CLIENT_SIDE)

    try:
        client.connect((HOST, SERVER_PORT))
        print("client address:", client.getsockname())

        msg = None
        while msg != EXIT:
            msg = input("talk: ")
            client.sendall(msg.encode(FORMAT))
            if msg == LOGIN:
                # wait response
                client.recv(1024)
                clientLogin(client)

            elif msg == ORDER:
                if userId == "":
                    client.recv(1024)
                    sendList(client, [LOGIN_TO_ORDER])
                    client.recv(1024)
                    print(LOGIN_TO_ORDER)
                else:
                    client.recv(1024)
                    clientOrder(client)

            elif msg == HISTORY:
                if userId == "":
                    client.recv(1024)
                    client.sendall("0".encode(FORMAT))
                    client.recv(1024)
                    print(LOGIN_TO_WATCH)
                else:
                    client.recv(1024)
                    print("Your transaction history:")
                    clientHistory(client)

            elif msg == USERID:
                print(userId)

            elif msg == LOGOUT:
                if userId == "":
                    client.recv(1024)
                    client.sendall("0".encode(FORMAT))
                    client.recv(1024)
                    print("You haven't login")
                else:
                    client.recv(1024)
                    cilentLogout(client)
                    userId = ""


    except ConnectionError as e:
        print(ERROR)
    finally:
        if userId != "":
            disconnectServer(client)
            userId = ""
        print("close")
        client.close()
