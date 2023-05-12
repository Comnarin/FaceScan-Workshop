from flask import Flask, jsonify,Response,render_template,send_file,request
from flask_socketio import SocketIO, emit
import face_recognition
from flask_cors import CORS
import os
from datetime import datetime
import cv2
import time
import requests


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app)
socketio = SocketIO(app)



video_capture = cv2.VideoCapture(0)
known_face_encodings = []
known_face_names = []
directory = './Server/static'
# Load the known face encodings and names from file
# Initialize variables for check-in and check-out times

check_in_times = {}
check_out_times = {}

for filename in os.listdir(directory):
    known_face_names.append(filename.replace(".jpg",""))
    f = os.path.join(directory, filename)
    person_image = face_recognition.load_image_file(f)
    person_encoding = face_recognition.face_encodings(person_image)[0]
    known_face_encodings.append(person_encoding)

def gen_frames():
    """Generate video frames."""
    while True:
        success, frame = video_capture.read()
        if not success:
            break
        else:
            # Find all the faces in the current frame of video
            face_locations = face_recognition.face_locations(frame)
            face_encodings = face_recognition.face_encodings(frame, face_locations)

            # Loop through each face in this frame of video
            for face_encoding, face_location in zip(face_encodings, face_locations):
                # See if the face is a match for the known faces
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"

                # Find the best match
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = face_distances.argmin()
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

                    # Get the current date and time
                    now = datetime.now()
                    date = now.date()

                    # Check if it's morning or afternoon
                    if now.hour < 12:
                        time_of_day = "morning"
                    else:
                        time_of_day = "afternoon"

                    # Check if it's the first time the person is checking in
                    if name not in check_in_times and time_of_day =="morning":
                        check_in_times[name] = now
                        check = 'check in this '
                        print(f"{name} checked in this {time_of_day} at {now}")
                        with open(f"/Users/comnarin/Documents/FaceScan-Workshop/Server/log/Check_in_log{date}.txt", "w") as f:
                            f.write(f"{name} checked in this {time_of_day} at {now}")
                         # Capture a screenshot of the face
                        top, right, bottom, left = face_location
                        face_img = frame[top:bottom, left:right]
                        filename="face.jpg"
                        cv2.imwrite(filename, face_img)
                        Line_post(name,check,time_of_day,now)
                        


                    if name not in check_out_times  and time_of_day =="afternoon":
                        check_out_times[name] = now
                        print(f"{name} checked out this {time_of_day} at {now}")
                        check = 'check out this '
                        with open(f"/Users/comnarin/Documents/FaceScan-Workshop/Server/log/Check_out_log{date}.txt", "w") as f:
                            f.write(f"{name} checked out this {time_of_day} at {now}")
                        top, right, bottom, left = face_location
                        face_img = frame[top:bottom, left:right]
                        filename="face.jpg"
                        cv2.imwrite(filename, face_img)
                        Line_post(name,check,time_of_day,now)
                        

                # Draw a rectangle around the face
                top, right, bottom, left = face_location
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Draw a label with the name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def Line_post(name,check,time_of_day,now):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization":"Bearer BPHAbJWJ4kxF3wc3AwfS0A5Wa1hA3ukpLp/Zo9g8bHdyZINb+AYAVesuo+Xs60sq34rsuXBJ0rEOxXWjH3snKd90Go8V2YlNxY8Y3icBR2KeiKuCyGgrdur8ZosKc52y54+Bcgohpa70+zGOC+GBmQdB04t89/1O/w1cDnyilFU=",
        "Content-Type": "application/json"
    }
    payload = {
        "to": "U30547c72a88bc771600eceadfc73fcd5",
        "messages": [
            {
                "type": "text",
                "text": f"{name} {check} {time_of_day} at {now}"
            },
            {
                "type": "image",
                "originalContentUrl": "image_path",
                "previewImageUrl": "image_path"
            }
        ]
    }
    post_response = requests.post(url, headers=headers, json=payload)
    print(post_response.status_code)
    print(post_response.json())



@app.route('/checkin')
def checkin():
    data = check_in_times
    
    return jsonify(data)

@app.route('/checkout')
def checkout():
    data=check_out_times
    
    return jsonify(data)

@app.route('/video_feed')
def video_feed():
    """Stream video frames."""
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_image')
def get_image():
    # load the image file
    image_file = open('/Users/comnarin/Documents/FaceScan-Workshop/face.jpg', 'rb')
    return send_file(image_file, mimetype='image/jpeg')


if __name__ == '__main__':
    socketio.run(app)
    

