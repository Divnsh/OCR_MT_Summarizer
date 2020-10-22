# Image to Document Converter
**Converts images containing text to editable documents.**
Deployed on: https://img2doc.herokuapp.com/

![TextConvert](/assets/img2doc.png)

The app takes one or more images as input and returns docx files containing text detected in the images.
User can select one or several languages depending on the text in the image.
Supported languages are: English, Tamil, Hindi, Telugu, Bengali and Malayalam.

*Processing before OCR -*

OpenCV is primarily used to pre-process the images in order to get the maximum gains from the underlying OCR models.
Based on the size of the image, it is upscaled or downscaled. 
Images below a height of 800px are upscaled to twice the size using a pretrained FastRCNN model which yields a good balance between speed and quality. 
Images longer than 1024px are rescaled by a factor of 1024/length. Images between 800 and 1024 pixel length are retained as is.
All images are then saved locally at 300dpi. 

Image is converted to greyscale and depending on the dominating color in the background, the colors are inverted or kept the same.
Sharpening stretching and rotations are performed followed by noise correction using opening, closing morphological and bilateral filters.
Contours and edged are used to align any warped edges containing the text.

Finally tesseract is used to extract the processed image to text.
Output is written as a docx file and sent to the user as an attachment.  
    

*Model-*

Pretrained tesseract models for the aforementioned languages are used.
Legacy and/or LSTM models are used based on availability for the language.
Latest models were trained in 2017, so there is still room for improvement.

*Web App-*

The web application is built using Dash, which uses Flask under the hood.
App is deployed on Heroku.
