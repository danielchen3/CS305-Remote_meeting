# CS305-Remote_meeting
This is the project of CS305 Computer Network in SUSTech.

## Introduction
The Final version of this project is in branch `Final`, which is also the default branch.

  This project builds a video meeting system containing both the server and client.

## Functionality
1. Client-server connection mode supporting audio, vidio and text.
2. Peer-to-Peer connection mode supporting audio, video and text for two clients.


## Instructions
After successfully connecting to the server, you need to enter your user name, which needs to be unique to all online users.

Here is the available instructions you may use.
| Instruction | Function |
| ------------- | ------------- |
| create | create a new meeting |
| create p2p | create a new p2p meeting and wait for the other client to connect |
| view | view all active meetings with their meeting ID |
| join x | join a meeting with ID x |
| quit | This instruction is used implicitly when client closed the meeting ui window |
| cancel | This instruction is used implicitly when conference host closed the meeting ui window and all user will be moved out|



Here is potential feedbacks given by the server.
| Feedback | Meaning |
| ------------- | ------------- |
| Meeting is full | Only occur in P2P meeting mode when user attemp to join a meeting with 2 clients |
| Connection lost | Connection lost with the server |
| Invalid username | Your username is duplicated, please change to another one|
| Meeting does not exist | The meeting you want to participate does not exist, please use `view` to check |



## How to use

Please fill in your IP information in `config.py` according to the hint given.

client

```
python client.py
```

server

```
python main_server.py
```
