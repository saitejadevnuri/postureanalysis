import cv2
import mediapipe as mp
import math as m
import time
from twilio.rest import Client
from globals import warnings_sent
account_sid = 'AC40bd9f8f20c5d2c4590ac8f5fe56cff0'
auth_token = '52e215bc03acf7209f70beaae16e8a55'
twilio_client = Client(account_sid, auth_token)
from_phone_number = '+18304944612'

def send_warning(phone_number):
    # Check if a warning has already been sent to the user
    if warnings_sent.get(phone_number, False):
        print("Warning already sent to this user, skipping further warnings.")
        return  # Exit if a warning has already been sent
    
    # If no warning has been sent, proceed with sending it
    message = twilio_client.messages.create(
        body="Warning: Bad posture detected!",
        from_=from_phone_number,
        to=phone_number
    )
    print(f"Warning sent to {phone_number}")
    
    # Mark that a warning has been sent to prevent further warnings
    warnings_sent[phone_number] = True


mp_pose = mp.solutions.pose
cap = cv2.VideoCapture(0)
fps= int(cap.get(cv2.CAP_PROP_FPS))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
frame_size = (width, height)
font = cv2.FONT_HERSHEY_SIMPLEX
blue = (255, 127, 0)
red = (50, 50, 255)
green = (127, 255, 0)
dark_blue = (127, 20, 0)
light_green = (127, 233, 100)
yellow = (0, 255, 255)
pink = (255, 0, 255)
def process_frame(phone_number):
    cap = cv2.VideoCapture(0)
    pose = mp_pose.Pose()
    global good_frames
    global bad_frames
    global notgood
    good_frames=0
    bad_frames=0
    notgood=0
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Could not read data")
            break

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        key_points = pose.process(image_rgb)
        image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

        image_bgr = cv2.resize(image_bgr, (640, 480))

        lm = key_points.pose_landmarks
        lmPose = mp_pose.PoseLandmark
        if lm:
            left_shoulder_x = int(lm.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x * image_bgr.shape[1])
            left_shoulder_y = int(lm.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y * image_bgr.shape[0])
            right_shoulder_x = int(lm.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x * image_bgr.shape[1])
            right_shoulder_y = int(lm.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * image_bgr.shape[0])
            left_ear_x = int(lm.landmark[mp_pose.PoseLandmark.LEFT_EAR].x * image_bgr.shape[1])
            left_ear_y = int(lm.landmark[mp_pose.PoseLandmark.LEFT_EAR].y * image_bgr.shape[0])
            left_hip_x = int(lm.landmark[mp_pose.PoseLandmark.LEFT_HIP].x * image_bgr.shape[1])
            left_hip_y = int(lm.landmark[mp_pose.PoseLandmark.LEFT_HIP].y * image_bgr.shape[0])

            neck_inclination = findAngle(left_shoulder_x, left_shoulder_y, left_ear_x, left_ear_y)
            torso_inclination = findAngle(left_hip_x, left_hip_y, left_shoulder_x, left_shoulder_y)
            
            if neck_inclination < 40 and torso_inclination < 10:
                color = (127, 233, 100)  # light green for good posture
                status_text = 'Good Posture'
                bad_frames = 0
                good_frames += 1
            else:
                color = (50, 50, 255)  # red for bad posture
                status_text = 'Bad Posture'
                good_frames = 0
                bad_frames += 1
                #send_warning(User.phone_number)


            # Drawing landmarks
            cv2.circle(image_bgr, (left_shoulder_x, left_shoulder_y), 7, color, -1)
            cv2.circle(image_bgr, (left_ear_x, left_ear_y), 7, color, -1)
            cv2.circle(image_bgr, (left_hip_x, left_hip_y), 7, color, -1)

            angle_text = f'Neck: {int(neck_inclination)} Torso: {int(torso_inclination)}'
            cv2.putText(image_bgr, angle_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            cv2.putText(image_bgr, status_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

            # Calculate distance between left shoulder and right shoulder points

            # Determine whether good posture or bad posture
    
            # Calculate the time of remaining in a particular posture
            good_time = (1 / fps) * good_frames
            bad_time = (1 / fps) * bad_frames
            # If you stay in bad posture for more than 3 minutes (180s) send an alert
            if bad_time > 3:  # Trigger warning if bad posture is held for 3 seconds
                send_warning(phone_number) # Reset bad time after sending warning

            
        ret, buffer = cv2.imencode('.jpg', image_bgr)
        frame = buffer.tobytes()

        yield frame

    cap.release()

def findDistance(x1, y1, x2, y2):
    return m.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def findAngle(x1, y1, x2, y2):
    theta = m.acos((y2 - y1) / findDistance(x1, y1, x2, y2))
    return 180 - int(180 * theta / 3.14)
