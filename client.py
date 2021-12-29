import select
import socket
import time
import struct
import multiprocessing
import random
from getch import getch, pause
import string
from termcolor import colored
import sys

class GameClient:

    def __init__(self, TEST):
        self.teamName = random.choice(["Maya","Yoni","Talya","Daphne"])
        self.gameClientUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.gameClientUDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.gameClientUDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.gameClientUDP.bind(('', 13117))
        self.gameClientTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # if TEST:
        #     self.gameClientUDP.bind(('172.99.255.255', 13117))
        # else:

        print(colored("Client started, listening for offer requests...", 'yellow'))
        self.LookingForGame()



    def LookingForGame(self):
        while True:
            self.gameClientUDP.settimeout(2)
            try:
                data, addr = self.gameClientUDP.recvfrom(8)
                packet = struct.unpack('IbH', data)
                serverPort = packet[2]
                if packet[0] != 0xabcddcba:
                    continue
                print(colored(f"Received offer from {addr[0]}, attempting to connect...",'yellow'))
                self.ConnectingToGame(addr[0], int(serverPort))
            except:
                pass

    def ConnectingToGame(self, addr, gamePort):
        try:
            self.gameClientTCP.settimeout(10)
            # Connecting to the TCP Game Server
            print(colored(f'trying to connect tcp, the address is {addr} and the port is {gamePort}','yellow'))
            self.gameClientTCP.connect((addr, gamePort))
            # Sending to the Server our Team Name
            self.gameClientTCP.sendall((self.teamName + '\n').encode())
            # Waiting for openning message
            data = None
            try:
                data = self.gameClientTCP.recv(1024)
            except:
                pass
            if data is None:
                print(colored(f'No Welcome Message has been received. Lets find new Server','red'))
            else:
                print(data.decode())
            self.playGame()
            print(colored('Server disconnected, listening for offer requests...','yellow'))
        except:
            pass
        self.gameClientTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def playGame(self):

        exit_while = False
        while True:
            input = [self.gameClientTCP, sys.stdin]
            inputready, outputready, exceptready = select.select(input, [], [])
            for s in inputready:
                if s == self.gameClientTCP:
                    data = s.recv(1024).decode()
                    print(colored(data,'magenta','on_white'))
                    exit_while = True
                    break

                elif s == sys.stdin:
                    ans = sys.stdin.readline()
                    self.gameClientTCP.sendall(ans.encode())
            if exit_while:
                break


def Main():
    GameClient(False)

if __name__ == '__main__':
    Main()
