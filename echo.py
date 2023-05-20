import zmq

import config


if __name__ == "__main__":
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(config.echo["bind"])

    while True:
        message = socket.recv().decode()
        if message == "__close__":
            socket.close()
            print("Socket closed, program exiting.")
            break
        
        print(message)
        socket.send(b"ACK")