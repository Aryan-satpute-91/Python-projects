import cv2
import numpy as np
from tensorflow.keras.models import load_model
import smtplib
from email.message import EmailMessage
from time import sleep
from Adafruit_MLX90614 import MLX90614
import RPi.GPIO as GPIO

# GPIO Setup
BUZZER_PIN = 18
SANITIZER_PIN = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(SANITIZER_PIN, GPIO.OUT)

# Load pre-trained model for mask detection
model = load_model('face_mask_detector.h5')

# Load Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Initialize temperature sensor
sensor = MLX90614()

# Email notification function
def send_alert(email, subject, message):
    try:
        msg = EmailMessage()
        msg.set_content(message)
        msg['Subject'] = subject
        msg['From'] = 'your_email@gmail.com'
        msg['To'] = email
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login('your_email@gmail.com', 'your_password')
            smtp.send_message(msg)
        print("Alert email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

# Temperature checking function
def check_temperature():
    temperature = sensor.get_object_temp()
    print(f"Temperature: {temperature:.2f}°C")
    return temperature

# Mask detection function
def detect_mask(frame):
    faces = face_cascade.detectMultiScale(frame, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
    for (x, y, w, h) in faces:
        face = frame[y:y+h, x:x+w]
        face = cv2.resize(face, (224, 224))
        face = face / 255.0
        face = np.expand_dims(face, axis=0)
        pred = model.predict(face)
        mask_label = 'Mask' if pred[0][0] > pred[0][1] else 'No Mask'
        confidence = max(pred[0])
        return mask_label, confidence, (x, y, w, h)
    return None, None, None

# Main loop
def main():
    cap = cv2.VideoCapture(0)  # Start video capture
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)  # Flip the frame horizontally
            mask_label, confidence, box = detect_mask(frame)
            
            if mask_label and confidence > 0.7:
                x, y, w, h = box
                color = (0, 255, 0) if mask_label == 'Mask' else (0, 0, 255)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(frame, f"{mask_label} ({confidence*100:.2f}%)", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                temperature = check_temperature()
                if mask_label == 'No Mask' or temperature > 37.5:
                    # Trigger alert
                    GPIO.output(BUZZER_PIN, GPIO.HIGH)
                    send_alert("admin_email@example.com", "COVID Alert", 
                               f"Alert: {mask_label}, Temp: {temperature:.2f}°C")
                    sleep(2)
                    GPIO.output(BUZZER_PIN, GPIO.LOW)
                else:
                    # Activate sanitizer
                    GPIO.output(SANITIZER_PIN, GPIO.HIGH)
                    sleep(2)
                    GPIO.output(SANITIZER_PIN, GPIO.LOW)
            
            cv2.imshow('Frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        GPIO.cleanup()

if __name__ == "__main__":
    main()
