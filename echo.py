import zmq

import config


if __name__ == "__main__":
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(config.echo["bind"])

    while True:
        print(socket.recv().decode())
        socket.send(b"ACK")