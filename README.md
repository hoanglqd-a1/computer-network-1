# ASSIGNMENT 1: DEVELOP A NETWORK APPLICATION

Full code in [source code](https://github.com/hoanglqd-a1/computer-network-1) 

## Overview
- A centralized server keeps track of which clients are connected and storing what pieces of
files.
- Through tracker protocol, a client informs the server as to what files are contained in its local
repository but does not actually transmit file data to the server.
- When a client requires a file that does not belong to its repository, a request is sent to the
server.
- Multiple clients could be downloading different files from a target client at a given point in
time. This requires the client code to be multithreaded

## Technology Stack
- GUI: Customtkinter.
- Programming language: Python

## Installation
To use the application, you can follow the following steps:

## Clone the repository
Open a terminal at a directory of your choice and enter these commands (change the folder name if you want to):
```
  git clone https://github.com/hoanglqd-a1/computer-network-1
```
You will see several files: *tracker.py*, *client.py*, etc.

## Install dependencies
First, if you haven't installed [Python](https://www.python.org/), please visit https://www.python.org/ and download it.

Next, you will have to install the dependencies about GUI and choose suitable version python of our project
```
  pip install customtkinter
```

You have installed all the dependencies.

## Set up a server

If you want to running server, let's go to the terminal and enter this command: 

```tracker
python tracker.py
```

In the terminal, you will see these lines, indicating that the server is already running. It will also provide the IP address and port number.

![tracker](https://github.com/Qdaika22/assets/blob/main/tracker.png)

## Run the application

If you are a client want to connect to the server, let's go to the terminal and enter this command:

```client
python client.py
```

The login application will appear, and you will select your port number and enter your name. Then, click the Submit button

![login](https://github.com/Qdaika22/assets/blob/main/login.png)

The main chat application shows the settings configuration (appearance mode and screen scaling), a files frame showing files that have been uploaded or downloaded, and a command input area for using the application.

And you need to enter the correct text commands to use this app:

![main](https://github.com/Qdaika22/assets/blob/main/main.png)

## Command use in chat application

### > close
This command will close the connection to the server and terminate the program on the client side

### > upload
"In my application, you can upload one file or multiple files concurrently. To do this, type *upload* in the text entry field and click *Send Message*. You will then enter the tracker's IP address and port number provided by the server to upload to it. Next, enter the file names in the dialog that appears. 

If you download multiple files, separate them with a comma (,):

![upload](https://github.com/Qdaika22/assets/blob/main/upload.png)

In "Root/Peers/torrents", you will see the torrent file, which is the uploaded file, and the file frame in chat application will be automatically updated.

![uploaded](https://github.com/Qdaika22/assets/blob/main/updated.png)

### > download
This command retrieves the file from the server and downloads it. The .torrent file will be saved in "Root/username/torrents". To do this, type *download* in the text entry field and click *Send Message*.

The dialog will pop up, you will enter your .torrent file:

![download](https://github.com/Qdaika22/assets/blob/main/download.png)

The application will download one file or multiple files (depending on your selection). During the download, the application will show the progress of each chunk being retrieved from the peer. 

When the download is complete, it will display the time taken to download the files:

![downloaded](https://github.com/Qdaika22/assets/blob/main/downloaded.png)

### > clear
This command will clear the text box


## Contributor
This project is developed by a group of Computer Science students from Ho Chi Minh University of Technology (HCMUT). Our members of the team:
* Đặng Hoàng Khang - 2211422
* Lê Phúc Hoàng - 2211081
* Đinh Xuân Quyết - 2212854
