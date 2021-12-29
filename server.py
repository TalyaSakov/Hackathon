import socket
import time
import struct
import threading
import multiprocessing
import random
import sys
from scapy.all import get_if_addr
# from termcolor import colored

class Server:

    def __init__(self, PORT, TEST=None):
        self.final = []
        self.Port = PORT

        # if TEST:
        self.TCPIP = get_if_addr('eth1')
        # Let the Server know the game start or over
        self.gameStarted = False
        # Collecting the players into Dict
        self.players = {}
        # Initiate server UDP socket
        self.initiateUDPSockets()
        # Initiate server TCP socket
        self.initiateTCPSockets(PORT)
        # Initiate server broadcasting Thread
        print(f'Server started, listening on IP address {self.TCPIP}')
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
        self.gameServerTCP.bind((self.TCPIP, PORT))

    def broadcast(self, host, port):
        self.answerTuple = self.randomEqution()
        while self.answerTuple[0] < 0:
            self.answerTuple = self.randomEqution()
        self.rightAnswer = self.answerTuple[0]

        while True:
            BROADCAST_PORT = 13117
            message = struct.pack('IbH', 0xabcddcba, 0x2, port)
            # '172.99.255.255'
            # x.x.255.255
            self.gameServerUDP.sendto(message, ('<broadcast>', BROADCAST_PORT))
            print('Sending broadcast')
            time.sleep(1)
            if len(self.players) == 2:
                break

        self.sendWelcomeMessage()
        self.gameStarted = True
        self.gameTime = time.time() + 10

        while len(self.final) == 0 and time.time() < self.gameTime:
            continue
        self.sendGameOverMessage()
        # Reset the players dict
        self.players = {}
        # broadcasting agian
        self.broadcast(host, port)

    def sendWelcomeMessage(self):
        welcomeStr = f"Welcome to Quick Maths.\nPlayer 1: {self.players[1][1]}Player 2: {self.players[2][1]}" \
                     f"==\nPlease answer the following question as fast as you can:\n{self.answerTuple[1]} "
        for player in self.players.keys():
            try:
                self.players[player][0].sendall(welcomeStr.encode())
            except:
                break

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
        # Close the last TCP sockets.
        for player in self.players.keys():
            self.players[player][0].close()
        self.final = []
        self.TCP_Connection()

    def setPlayerAndStart(self, playerSocket, playerAddr):
        try:
            playerSocket.settimeout(3)
            playerNameDecoded = playerSocket.recv(1024).decode()
            self.sT.acquire()
            if playerNameDecoded in self.players.values():
                raise Exception('same client twice')
            playerNumber = 1 if len(self.players.keys()) == 0 else 2
            self.players[playerNumber] = [playerSocket, playerNameDecoded, playerNumber, 0]
            self.sT.release()
        except:
            return
        self.StartGame(playerNumber, playerSocket)

    def StartGame(self, playerNumber, playerSocket):

        stop_time = time.time() + 10
        # playerSocket.settimeout(1)
        while time.time() < stop_time:
            try:
                # Adding the messages to his score - in the dict
                inputByClient = playerSocket.recv(1024).decode()
                self.final.append((inputByClient, playerNumber))
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
        if len(self.final) == 0:
            gameOver = "The time is over"
        else:
            if self.rightAnswer == int(self.final[0][0]):
                # self.player[player_num][hisName]
                winner = self.players[self.final[0][1]][1]
                # Can be player number 1 or number 2.
            else:
                if self.final[0][1] == 1:
                    winner = self.players[2][1]
                else:
                    winner = self.players[1][1]

            gameOver = f'Game over!\nThe correct answer was {self.rightAnswer}!' \
                       f' Congratulations to the winner: {winner} '
        for player in self.players.keys():
            try:
                self.players[player][0].sendall(f'{gameOver}'.encode())
                self.players[player][0].close()
            except:
                pass

PORT = 2055
HOST = None

def Main():
    server = Server(2055)


if __name__ == '__main__':
    Main()
