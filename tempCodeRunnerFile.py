
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
