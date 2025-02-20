import cv2
from deepface import DeepFace

# بارگذاری مدل تشخیص چهره OpenCV
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# راه‌اندازی وب‌کم
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # تبدیل به خاکستری برای تشخیص چهره
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # پیدا کردن چهره‌ها
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    for (x, y, w, h) in faces:
        # رسم مستطیل دور چهره
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # برش تصویر چهره برای تحلیل احساسات
        face_roi = frame[y:y+h, x:x+w]
        
        # تشخیص حالت چهره با DeepFace
        try:
            result = DeepFace.analyze(face_roi, actions=['emotion'], enforce_detection=False)
            mood = result[0]['dominant_emotion']
            # نمایش حالت روی تصویر
            cv2.putText(frame, f'Mood: {mood}', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
        except Exception as e:
            cv2.putText(frame, 'Mood: Unknown', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
            print(f"Error: {e}")
    
    # نمایش تصویر
    cv2.imshow('Mood Detector', frame)
    
    # خروج با 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()import cv2

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
mouth_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
    
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # ناحیه دهان
        roi_gray = gray[y:y+h, x:x+w]
        mouths = mouth_cascade.detectMultiScale(roi_gray, 1.5, 10)
        
        mood = "Neutral"
        if len(mouths) > 0:
            mood = "Happy"  # اگه لبخند تشخیص بده
        
        cv2.putText(frame, f'Mood: {mood}', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
    
    cv2.imshow('Mood Detector', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()