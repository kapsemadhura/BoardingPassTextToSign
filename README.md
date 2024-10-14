# BoardingPassTextToSign
Enhancing Accessibility for Hearing-Impaired Travelers with  Real-Time Sign Language Guidance

# Flask App for YOLOv5 Object Detection

This Flask application performs object detection using a YOLOv5 model. The app allows users to upload images, processes them using the trained model, and displays the detected objects with bounding boxes on the web interface. 

## Features
- Upload images for object detection
- Display detected objects with bounding boxes
- Access the app from multiple devices on the same local network

## Prerequisites
- Python 3.7+
- Flask
- YOLOv5 dependencies (torch, torchvision, etc.)

## Installation

1. **Clone the Repository:**
    ```bash
    git clone https://github.com/kapsemadhura/BoardingPassTextToSign.git
    cd your-flask-app
    ```

2. **Install Required Packages:**
    Make sure you have Anaconda or Python with `pip` installed. Then, install the necessary packages:
    ```bash
    pip install -r requirements.txt
    ```

3. **Set Up YOLOv5:**
    YOLOv5 is properly configured and trained. This app expects the model file (`.pt`) to be available.

4. **Prepare Environment Variables (Optional):**
   You can set up a `.env` file with necessary environment variables such as model paths and configurations.

## Running the Application

1. **Run the Flask App:**
    ```bash
    python app.py
    ```

2. **Access the App on Localhost:**
   - Open your web browser and go to `http://192.168.0.194:5000`.

3. **Access the App on Mobile:**
   - Ensure your mobile device is connected to the same Wi-Fi network as your computer.
   - Identify your computer's IP address from the terminal output. 
   - Open a browser on your mobile device and navigate to `http://192.168.0.194:5000`

## Example Usage

1. Go to the web app in your browser.
2. Upload an image file from the test boarding pass images folder.
3. View the results on browser.

## Troubleshooting

- **Port or Address Not Accessible:**
  - Ensure your firewall allows incoming traffic on port `5000`.
  - Make sure you are using the correct IP address and that both devices are on the same network.

- **Model File Not Found:**
  - Confirm that the path to your YOLOv5 model weights is correct.





