from flask import Flask, render_template, request, session
import pytesseract
from PIL import Image
import os
import requests
import threading
import time

# Initializing the Flask app
app = Flask(__name__)

# Required for using session variables
app.secret_key = 'your_secret_key'  

# Path to the Tesseract executable file
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Creating a directory to upload the images
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initializing the Roboflow API parameters
API_KEY = "FyMcDUhNlUME6DDfYaml"
MODEL_ID = "boarding-pass-text-extraction/1"
CONFIDENCE_THRESHOLD = 0.11    #To match as per the training model detection threashold

def extract_text_from_image(image_path):
    """Extract text using Tesseract OCR."""
    try:
        with Image.open(image_path) as img:
            text = pytesseract.image_to_string(img)
            print(f"Extracted text: {text}")                    # Line to print OCR output
            return text.strip()                                 # Strip any leading/trailing whitespace
    except Exception as e:
        print(f"Error during OCR: {e}")
        return None

def get_character_images(text):
    """Fetch corresponding character images for extracted text."""
    image_files = []
    for char in text:
        if char == ' ':
            continue  # Skip spaces
        if char.isalpha():
            filename = f"{char.upper()}.jpg"                    # Convert to uppercase for filename
        elif char.isdigit():
            filename = f"{char}.jpg"
        else:
            continue                                            # Skip any other characters

        image_files.append(filename)
    print(f"Character images: {image_files}")                   # Debugging line to check image file paths
    return image_files

def crop_image_with_bounding_box(image_path, bbox):
    """Crop image using bounding box coordinates."""
    try:
        with Image.open(image_path) as img:
            left = max(bbox['x'] - bbox['width'] / 2, 0)                # Ensure left is not negative
            top = max(bbox['y'] - bbox['height'] / 2, 0)                # Ensure top is not negative
            right = min(bbox['x'] + bbox['width'] / 2, img.width)       # Ensure right is within image width
            bottom = min(bbox['y'] + bbox['height'] / 2, img.height)    # Ensure bottom is within image height

            cropped_img = img.crop((left, top, right, bottom))
            cropped_img_path = os.path.join(app.config['UPLOAD_FOLDER'], 'cropped_image.jpg')
            cropped_img.save(cropped_img_path)
            
            print(f"Cropped image dimensions: {cropped_img.size}")      # Log dimensions
            return cropped_img_path
    except Exception as e:
        print(f"Error while cropping image: {e}")
        return None

def delete_file_after_delay(file_path, delay=300):
    """Delete the file after a specified delay (default is 300 seconds or 5 minutes)."""
    time.sleep(delay)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"File {file_path} deleted after {delay} seconds.")
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

@app.route('/', methods=['GET'])
def index():
    """Render the index page for uploading images."""
    return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_and_display():
    extracted_data = {}
    image_frames = {}
    error_message = None
    original_image_path = None
    cropped_image_path = None

    if request.method == 'POST':
        try:
            # Get the uploaded file
            file = request.files['image']
            if file:
                # Save the original uploaded file to the uploads folder
                original_image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(original_image_path)
                
                # Store the original image path in the session
                session['original_image_path'] = original_image_path

                print(f"File saved to {original_image_path}")           # Log file save confirmation

                # --- Module 1: Object Detection and Cropping ---
                api_url = f"https://detect.roboflow.com/{MODEL_ID}?confidence={CONFIDENCE_THRESHOLD}&api_key={API_KEY}"
                
                # Open the original uploaded image file and send the request
                with open(original_image_path, "rb") as image_file:
                    response = requests.post(api_url, files={"file": image_file})

                # Parse the response JSON
                result = response.json()

                # Log the entire result for debugging
                print("API Response:", result)

                if result and 'predictions' in result:
                    if len(result['predictions']) > 0:
                        prediction = result['predictions'][0]
                        print(f"Bounding box found: {prediction}")

                        # Use the original uploaded file for cropping
                        cropped_image_path = crop_image_with_bounding_box(original_image_path, prediction)
                        
                        # Store the cropped image path in the session
                        session['cropped_image_path'] = cropped_image_path

                        # --- Perform OCR on the cropped image ---
                        if cropped_image_path:
                            extracted_text = extract_text_from_image(cropped_image_path)

                            # Split the extracted text into lines
                            lines = extracted_text.splitlines()

                            # Check if we have at least two lines
                            if len(lines) >= 2:
                                # Split the second line into words
                                values = lines[1].strip().split()

                                # Assign values to respective fields
                                if len(values) >= 6:                                        # Ensure there are enough values
                                    extracted_data = {
                                        "Passenger Name": ' '.join(values[0:2]),            # First two words for name
                                        "Boarding Time": values[2],                         # Assuming boarding time is the third word
                                        "Flight": values[3],                                # Flight number
                                        "Gate": values[4],                                  # Gate number
                                        "Seat": values[5] + ' ' + ' '.join(values[6:]),     # Combine seat number and additional info if needed
                                    }

                                    # Fetch character images for the respective fields
                                    image_frames = {
                                        "Passenger Name": get_character_images(extracted_data["Passenger Name"]),
                                        "Boarding Time": get_character_images(extracted_data["Boarding Time"]),
                                        "Flight": get_character_images(extracted_data["Flight"]),
                                        "Gate": get_character_images(extracted_data["Gate"]),
                                        "Seat": get_character_images(extracted_data["Seat"]),
                                    }
                                else:
                                    error_message = "Extracted values do not contain enough information."
                            else:
                                error_message = "Extracted text does not contain enough lines."

                        else:
                            error_message = "Could not crop image using detected bounding box."
                    else:
                        error_message = "No bounding box detected."
                else:
                    error_message = "Error in object detection with Roboflow."

                # Start background cleanup threads for both original and cropped images
                if original_image_path:
                    threading.Thread(target=delete_file_after_delay, args=(original_image_path,)).start()
                if cropped_image_path:
                    threading.Thread(target=delete_file_after_delay, args=(cropped_image_path,)).start()

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"

    return render_template('display_table.html', data=extracted_data, images=image_frames, error=error_message)

@app.route('/cleanup')
def cleanup():
    """Endpoint to manually trigger cleanup of images from the current session."""
    # Delete the original image if it exists in the session
    if 'original_image_path' in session and os.path.exists(session['original_image_path']):
        os.remove(session['original_image_path'])
        print(f"Deleted original image: {session['original_image_path']}")
        session.pop('original_image_path', None)

    # Delete the cropped image if it exists in the session
    if 'cropped_image_path' in session and os.path.exists(session['cropped_image_path']):
        os.remove(session['cropped_image_path'])
        print(f"Deleted cropped image: {session['cropped_image_path']}")
        session.pop('cropped_image_path', None)

    return "Cleanup completed"

if __name__ == '__main__':
    app.run(debug=True)
