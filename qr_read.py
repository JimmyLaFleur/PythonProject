import cv2
from pyzbar import pyzbar

def qr_to_text(qr_image):
    img = cv2.imread(qr_image)
    barcodes = pyzbar.decode(img)
    for barcode in barcodes:
        barcodeData = barcode.data.decode("utf-8")
        print(barcodeData)