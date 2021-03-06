import cv2
import pytesseract
import numpy as np
import os,sys
from PIL import Image
import tempfile
import scipy.stats as stats
from transform import four_point_transform
import imutils
#from skimage.filters import threshold_local
from docx import Document
import glob
import re
import datetime
import io,base64,imageio

### Pre-processing


def cv2_readable():
    with open(file_path, "rb") as fid:
        data = fid.read()
    b64_bytes = base64.b64encode(data)
    b64_string = b64_bytes.decode()
    # reconstruct image as an numpy array
    img = imageio.imread(io.BytesIO(base64.b64decode(b64_string)))
    cv2_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return cv2_img


# Rescale
def save_temp(im):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    temp_filename = temp_file.name
    im.save(temp_filename, dpi=(300, 300))
    return temp_filename

def set_image_dpi():
    cvim=cv2_readable()
    cvimmat = cv2.cvtColor(cvim, cv2.COLOR_BGR2RGB)
    im = Image.fromarray(cvimmat)
    #im = Image.open(filepath)
    length_x, width_y = im.size
    if length_x<800:
        # Create an SR object
        sr = cv2.dnn_superres.DnnSuperResImpl_create()
        sr.readModel('./models/FSRCNN_x2.pb')
        sr.setModel("fsrcnn", 2)
        im_resized = Image.fromarray(sr.upsample(cvim).astype('uint8'),'RGB')
    else:
        factor = min(1, float(1024.0 / length_x))
        size = int(factor * length_x), int(factor * width_y)
        im_resized = im.resize(size, Image.ANTIALIAS)
    temp_filename=save_temp(im_resized)
    return temp_filename

# Grayscale and Invert colors if background is dark
def rescale_color_correct():
    rescaled=set_image_dpi()
    img=cv2.imread(rescaled)
    img=cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # grey-scale
    mode_color=stats.mode(img,axis=None)[0][0] # Dominant background color
    if mode_color<100:     # invert colors if background in black
        img = (255 - img)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        rescaled = temp_file.name
        cv2.imwrite(rescaled,img)
    return rescaled,mode_color

# Fred's textcleaner
def fred_clean():
    os.system('bash textcleaner -g -e stretch -f 25 -o 10 -u -s 1 -T -p 10 '+rescaled+' ./processed_img/res'+now+'.png')
    imag=cv2.imread('./processed_img/res'+now+'.png')
    imag=cv2.cvtColor(imag, cv2.COLOR_BGR2GRAY) # grey-scale
    #imag = cv2.bitwise_not(imag)
    os.remove('./processed_img/res'+now+'.png')
    return imag

# Dilating and eroding
def noise_correction():
    kernel = np.ones((2,2),np.uint8)
    opening = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
    #blur = cv2.GaussianBlur(opening,(5,5),0) # noise treatment
    blur = cv2.bilateralFilter(img, 9, 75, 75)
    #thresh = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
    #cv2.imshow('blur',blur)
    return blur,opening

def align():
    image = cv2_readable()
    #image = cv2.imread(file_path)
    ratio = image.shape[0] / 500.0
    orig = image.copy()
    image = imutils.resize(image, height=500)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 75, 200)
    #cv2.imshow("edged", edged)
    # find the contours in the edged image, keeping only the
    # largest ones, and initialize the screen contour
    cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:5]
    # loop over the contours
    for c in cnts:
        area = cv2.contourArea(c)
        if area > gray.size / 40:
            # approximate the contour
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            # if our approximated contour has four points, then we
            # can assume that we have found our screen
            if len(approx) == 4:
                screenCnt = approx
                break
    # show the contour (outline) of the piece of paper
    cv2.drawContours(image, [screenCnt], -1, (0, 255, 0), 2)
    #cv2.imshow("Outline", image)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    warped = four_point_transform(orig, screenCnt.reshape(4, 2) * ratio)
    # warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    # T = threshold_local(warped, 11, offset=10, method="gaussian")
    # warped = (warped > T).astype("uint8") * 255
    # show the original and scanned images
    #cv2.imshow("Original", imutils.resize(orig, height = 650))
    #cv2.imshow("Scanned", imutils.resize(warped, height = 650))
    #cv2.waitKey(0)
    filepath = file_path.split('.')[0] + '_aligned'+now+'.png'
    cv2.imwrite(filepath, warped)
    return filepath

# Get final text
def get_ocr():
    text=pytesseract.image_to_string(blur, config=custom_config)
    return text

# Transform txt in docx
def txt_to_doc():
    doc = Document()
    files = glob.glob("./xtracted_texts/*"+now+".txt")
    with open(files[0], 'r', encoding='utf-8') as openfile:
        line = openfile.read()
        # Only retaining valid XML characters
        line=re.sub(u'[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD\U00010000-\U0010FFFF]+', '', line)
        doc.add_paragraph(line)
        doc.save(files[0][:-4] + ".docx")
    #os.system(files[0][:-4] + ".docx")
    print("Document saved at: " + files[0][:-4] + ".docx")

if __name__=='__main__':
    #os.chdir('/home/divyansh/PycharmProjects/Summarizer')
    #file_path = os.path.abspath('./test_images/hind2.jpg')
    file_path = sys.argv[1]
    fp1=file_path
    now = str(datetime.datetime.now()).replace(' ', '')
    fileList = glob.glob('./xtracted_texts/*')
    for f in fileList:
        delta=(datetime.datetime.now() - datetime.datetime.strptime(f.split('/')[-1][4:29], "%Y-%m-%d%H:%M:%S.%f")).seconds
        if delta>120: # files older than 2 minutes are deleted
            os.remove(f)
    #Adding custom options
    #custom_config = r'-l hin --oem 3 --psm 1'
    custom_config = r'-l '+str(sys.argv[2])+' --oem 3 --psm 1'
    # oem options:
    # 0. Legacy engine only.
    # 1. Neural nets LSTM engine only.
    # 2. Legacy + LSTM engines.
    # 3. Default, based on what is available.
    # languages:
    # Hin, mal, tam, ben, tel, eng
    try:
        file_path=align()
        change_perspective=False
    except Exception as e:
        print("Outer edges not found."+str(e))
        change_perspective=True
    rescaled,mode_color=rescale_color_correct()
    print(mode_color)
    img=fred_clean()
    blur,opening=noise_correction()
    #cv2.imwrite('blur.jpg', blur)
    if change_perspective:
        pts=np.float32([[0,0],[blur.shape[1],0],[blur.shape[1],blur.shape[0]],[0,blur.shape[0]]])
        blur = four_point_transform(blur, pts)
    text=get_ocr()
    with open('./xtracted_texts/text'+now+'.txt','w+') as f:
        f.write(text)
    txt_to_doc()
    try:
        os.remove(fp1)
        os.remove(file_path)
    except:
        pass


# skew correction
# def deskew(image):
#     gray = cv2.bitwise_not(gray)
#     thresh = cv2.threshold(gray, 0, 255,
#                            cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
#     # rotation
#     coords = np.column_stack(np.where(thresh > 0))
#     angle = cv2.minAreaRect(coords)[-1]
#     if angle < -45:
#         angle = -(90 + angle)
#     else:
#         angle = -angle
#     (h, w) = image.shape[:2]
#     center = (w // 2, h // 2)
#     M = cv2.getRotationMatrix2D(center, angle, 1.0)
#     rotated = cv2.warpAffine(thresh, M, (w, h),
#                              flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
#     return rotated
# deskew = deskew(img)
# cv2.imshow('deskew',deskew)


