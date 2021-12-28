import socket
import time
import struct
import threading
import multiprocessing
import random
import sys
from scapy.all import get_if_addr





class Server:

    def __init__(self, PORT, TEST = None):
        self.Port = PORT

        # if TEST:
        #     self.IP = get_if_addr('eth2')
        #     self.broadcastAddr = '172.99.255.255'
        # else:
        # self.TCPIP = get_if_addr('eth1')
        # self.TCPIP = '127.0.0.1'

        # TODO: fix the static ip
        # TODO: Use colors
        hostname = socket.gethostname()
        self.TCPIP = socket.gethostbyname(hostname)
        print(self.TCPIP)
        self.broadcastAddr = '172.1.255.255'

        # Let the Server know the game start or over
        self.gameStarted = False
        # Game Timer (10 secs) until the game will start
        self.endBroadcast = 0
        # Collecting the players into Dict
        self.players = {}
        # Lock in order to write into the dict
        self.semaphore = threading.Semaphore()
        # Initiate server UDP socket
        self.initiateUDPSockets()
        # Initiate server TCP socket
        self.initiateTCPSockets(PORT)
        self.answerTuple = self.randomEqution()
        self.rightAnswer = self.answerTuple[0]

        # Initiate server broadcasting Thread
        print('Server started, listening on IP address {}'.format(self.TCPIP))
        self.tBroadCast = threading.Thread(target=self.broadcast, args=(self.TCPIP, self.Port))

        # Initiate server players collector Thread
        self.tCollector = threading.Thread(target=self.TCP_Connection, args=())
        # Semaphore to control the flowing of clients
        self.sT = threading.Semaphore(1)
        self.tBroadCast.start()
        self.tCollector.start()

        # Waiting for the threads to end.
        self.tBroadCast.join()
        self.tCollector.join()

    def initiateUDPSockets(self):
        self.gameServerUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # Allow more then one client to connect
        self.gameServerUDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        # Enable broadcasting mode
        self.gameServerUDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def initiateTCPSockets(self, PORT):
        self.gameServerTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gameServerTCP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        # Bind to the Addr and Port
        # print(f'tct ip {self.TCPIP} and port is {PORT}')
        # self.gameServerTCP.bind(('192.168.14.3', PORT))
        self.gameServerTCP.bind(('10.100.102.193', PORT))

    def broadcast(self, host, port):

        # randEquation = self.randomEqution()

        # bind the socket
        # self.gameServerUDP.bind((host, port))

        self.endBroadcast = time.time() + 10
        while time.time() < self.endBroadcast:
            BROADCAST_PORT = 13117
            message = struct.pack('IbH', 0xabcddcba, 0x2, port)
            self.gameServerUDP.sendto(message, ('<broadcast>', BROADCAST_PORT))
            print('Sending broadcast')
            time.sleep(1)
            if len(self.players) == 2:
                break


        self.final = []
        if len(self.players) == 2:
            # self.sT.acquire()
            self.sendWelcomeMessage()
            self.gameStarted = True
            while len(self.final) == 0:
                continue
            self.sendGameOverMessage()
        else:
            print("No Players after 10 secs, Let's try agian")
            self.players = {}
        # Reset the players dict
        self.players = {}
        # self.sT.release()
        # broadcasting agian
        self.broadcast(host, port)

    def sendWelcomeMessage(self):
        try:
            welcomeStr = f"Welcome to Quick Maths.\nPlayer 1: {self.players[1][1]}Player 2: {self.players[2][1]}" \
                         f"==\nPlease answer the following question as fast as you can:\n{self.answerTuple[1]} "
            for player in self.players.keys():
                # print(f'player socket {player[0]}')
                try:
                    self.players[player][0].sendall(welcomeStr.encode())
                except:
                    pass
        except:
            pass

    def TCP_Connection(self):
        players_threads = []
        while not self.gameStarted and len(players_threads) < 2:
            self.gameServerTCP.settimeout(1.5)
            try:
                self.gameServerTCP.listen()
                client, addr = self.gameServerTCP.accept()
                print(f'TCP connection has been made')
                # Initiate Thread for each player
                t = threading.Thread(target=self.setPlayerAndStart, args=(client, addr))
                players_threads.append(t)
            except:
                pass
        players_threads[0].start()
        players_threads[1].start()

        for thread in players_threads:
            thread.join()
        # Game over
        self.gameStarted = False
        # Collection the players agian.
        # self.sT.acquire()
        self.TCP_Connection()

    def setPlayerAndStart(self, playerSocket, playerAddr):
        try:
            playerSocket.settimeout(3)
            playerNameDecoded = playerSocket.recv(1024).decode()
            self.sT.acquire()
            if playerNameDecoded  in self.players.values():
                raise Exception('same client twice')
            playerNumber = 1 if len(self.players.keys()) == 0 else 2
            self.players[playerNumber] = [playerSocket, playerNameDecoded, playerNumber, 0]
            print(f'{playerNameDecoded[:-1]} has acquired')
            self.sT.release()
        except:
            return
        self.StartGame(playerNumber, playerSocket)

    def StartGame(self, playerNumber, playerSocket):

        # After game over making sure we don't stack in loop
        while len(self.players.keys()) < 2:
            if len(self.players.keys()) == 1:
                print(f"waiting for the second player.")
                time.sleep(1)

        stop_time = time.time() + 10
        playerSocket.settimeout(1)
        while time.time() < stop_time:
            try:
                # Adding the messages to his score - in the dict
                inputByClient = playerSocket.recv(1024).decode()
                print(f'input by clint is {inputByClient}')
                self.final.append((inputByClient,playerNumber))
                break
            except:
                pass

    def randomEqution(self):
        num1 = random.randint(0, 9)
        num2 = random.randint(0, 9)
        num3 = random.randint(0, 1)
        if num3 == 0:
            return num1 + num2, str(num1) + "+" + str(num2) + "?"
        else:
            return num1 - num2, str(num1) + "-" + str(num2) + "?"

    def sendGameOverMessage(self):
        gameOver = f'Game over!\nThe correct answer was {self.final[0][0][0]}!' \
                   f' Congratulations to the winner: {self.players[self.final[0][1]][1]} '
        for player in self.players.keys():
            try:
                self.players[player][0].sendall(gameOver.encode())
            except:
                pass



PORT = 12345
HOST = None

Server(PORT, False)


def Main():
    server = Server(12345)


if __name__ == '__main__':
    Main()
