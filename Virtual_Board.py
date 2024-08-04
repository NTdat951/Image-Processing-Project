import cv2
import mediapipe as mp
import numpy as np
from tkinter import *

class HandTracker():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.8, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(self.mode, self.maxHands, self.detectionCon, self.trackCon)
        self.mpDraw = mp.solutions.drawing_utils

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:
            for handLm in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLm, self.mpHands.HAND_CONNECTIONS)
        return img

    def getPostion(self, img, handNo = 0, draw=True):
        lmList =[]
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for lm in myHand.landmark:
                h, w, c = img.shape
                cx, cy = int(lm.x*w), int(lm.y*h)
                lmList.append((cx, cy))

                if draw:
                    cv2.circle(img, (cx, cy), 5, [0, 0, 255], cv2.FILLED)
        return lmList
    
    def getUpFingers(self, img):
        pos = self.getPostion(img, draw=False)
        self.upfingers = []
        if pos:
            # Ngón cái (thumb)
            self.upfingers.append((pos[4][1] < pos[3][1] and (pos[5][0]-pos[4][0]> 10)))
            # Ngón trỏ (index)
            self.upfingers.append((pos[8][1] < pos[7][1] and pos[7][1] < pos[6][1]))
            # Ngón giữa (middle)
            self.upfingers.append((pos[12][1] < pos[11][1] and pos[11][1] < pos[10][1]))
            # Ngón nhẫn (ring)
            self.upfingers.append((pos[16][1] < pos[15][1] and pos[15][1] < pos[14][1]))
            # Ngón út (pinky)
            self.upfingers.append((pos[20][1] < pos[19][1] and pos[19][1] < pos[18][1]))
        #print(self.upfingers)
        return self.upfingers

class ColorRect():
    def __init__(self, x, y, w, h, color, text='', alpha = 0.5):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.text=text
        self.alpha = alpha
        
    
    def drawRect(self, img, text_color=(255,255,255), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.8, thickness=2):
        #draw the box
        alpha = self.alpha
        bg_rec = img[self.y : self.y + self.h, self.x : self.x + self.w]
        white_rect = np.ones(bg_rec.shape, dtype=np.uint8)
        white_rect[:] = self.color
        res = cv2.addWeighted(bg_rec, alpha, white_rect, 1-alpha, 1.0)
        
        # Putting the image back to its position
        img[self.y : self.y + self.h, self.x : self.x + self.w] = res

        #put the letter
        tetx_size = cv2.getTextSize(self.text, fontFace, fontScale, thickness)
        text_pos = (int(self.x + self.w/2 - tetx_size[0][0]/2), int(self.y + self.h/2 + tetx_size[0][1]/2))
        cv2.putText(img, self.text, text_pos, fontFace, fontScale, text_color, thickness)


    def isOver(self,x,y):
        if (self.x + self.w > x > self.x) and (self.y + self.h> y >self.y):
            return True
        return False

def main_program():
    # Khởi tạo tỉ lệ dự đoán
    detector = HandTracker(detectionCon=0.8)

    # Khởi tạo webcam 
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)

    # Tạo một canvas để vẽ
    canvas = np.zeros((720,1280,3), np.uint8)

    # Khai báo một tọa độ cho trước để vẽ
    px,py = 0,0
    # Màu bút ban đầu
    color = (255,255,255)
    # Kích thước bút và tẩy ban đầu
    brushSize = 5
    eraserSize = 5

    ########### creating colors ########
    # Nút chọn màu bút (Colors button)
    colorsBtn = ColorRect(200, 0, 100, 100, (120,255,0), 'Colors')

    colors = []
    # Màu trắng (white)
    colors.append(ColorRect(300,0,100,100, (255, 255, 255), 'White'))
    # Màu đỏ (red)
    colors.append(ColorRect(400,0,100,100, (0,0,255), 'Red'))
    # Màu lam (blue)
    colors.append(ColorRect(500,0,100,100, (255,0,0), 'Blue'))
    # Màu lục (Green)
    colors.append(ColorRect(600,0,100,100, (0,255,0), 'Green'))
    # Màu vàng (Yellow)
    colors.append(ColorRect(700,0,100,100, (0,255,255), 'Yellow'))
    # Tẩy (earse)(black)
    colors.append(ColorRect(800,0,100,100, (0,0,0), 'Eraser'))
    # Xóa tất cả (clear)
    clear = ColorRect(900,0,100,100, (100,100,100), 'Clear')

    ########## pen sizes #######
    pens = []
    for i, penSize in enumerate(range(5,25,5)):
        pens.append(ColorRect(1100,50+100*i,100,100, (50,50,50), str(penSize)))

    penBtn = ColorRect(1100, 0, 100, 50, color, 'Size')

    # Nút chọn bảng trắng (white board button)
    boardBtn = ColorRect(50, 0, 100, 100, (255,255,0), 'Board')

    # Tạo một bảng trắng để vẽ lên trên
    whiteBoard = ColorRect(50, 120, 1020, 580, (255,255,255),alpha = 0.6)

    coolingCounter = 20
    hideBoard = True
    hideColors = True
    hidePenSizes = True

    while True:

        if coolingCounter:
            coolingCounter -=1
            # print(coolingCounter)

        ret, frame = cap.read()
        if not ret:
            break
        # Lật ngược khung hình webcam
        frame = cv2.flip(frame, 1)

        detector.findHands(frame)
        positions = detector.getPostion(frame, draw=False)
        upFingers = detector.getUpFingers(frame)

        if upFingers:
            x, y = positions[8][0], positions[8][1]
            if upFingers[1] and not whiteBoard.isOver(x, y):
                px, py = 0, 0

                ##### pen sizes ######
                if not hidePenSizes:
                    for pen in pens:
                        if pen.isOver(x, y):
                            brushSize = int(pen.text)
                            pen.alpha = 0
                        else:
                            pen.alpha = 0.5

                ####### chose a color for drawing #######
                if not hideColors:
                    for cb in colors:
                        if cb.isOver(x, y):
                            color = cb.color
                            cb.alpha = 0
                        else:
                            cb.alpha = 0.5

                    #Clear 
                    if clear.isOver(x, y):
                        clear.alpha = 0
                        canvas = np.zeros((720,1280,3), np.uint8)
                    else:
                        clear.alpha = 0.5
                
                # Nút nhấn chọn màu (color button)
                if colorsBtn.isOver(x, y) and not coolingCounter:
                    coolingCounter = 10
                    colorsBtn.alpha = 0
                    hideColors = False if hideColors else True
                    colorsBtn.text = 'Colors' if hideColors else 'Hide'
                else:
                    colorsBtn.alpha = 0.5
                
                # Nút nhấn chọn kích thước (size button)
                if penBtn.isOver(x, y) and not coolingCounter:
                    coolingCounter = 10
                    penBtn.alpha = 0
                    hidePenSizes = False if hidePenSizes else True
                    penBtn.text = 'Size' if hidePenSizes else 'Hide'
                else:
                    penBtn.alpha = 0.5

                
                # Nút nhấn chọn bảng trắng (white board button)
                if boardBtn.isOver(x, y) and not coolingCounter:
                    coolingCounter = 10
                    boardBtn.alpha = 0
                    hideBoard = False if hideBoard else True
                    boardBtn.text = 'Board' if hideBoard else 'Hide'

                else:
                    boardBtn.alpha = 0.5
                
                
            elif upFingers[1] and not upFingers[2]:
                if whiteBoard.isOver(x, y) and not hideBoard:
                    cv2.circle(frame, positions[8], brushSize, color,-1)
                    # Vẽ lên canvas (drawing on the canvas)
                    if px == 0 and py == 0:
                        px, py = positions[8]
                    if color == (0,0,0):
                        cv2.line(canvas, (px,py), positions[8], color, eraserSize)
                    else:
                        cv2.line(canvas, (px,py), positions[8], color, brushSize)
                    px, py = positions[8]
            
            else:
                px, py = 0, 0
            
        # Tạo nút nhấn chọn màu (put colors button)
        colorsBtn.drawRect(frame)
        cv2.rectangle(frame, (colorsBtn.x, colorsBtn.y), (colorsBtn.x +colorsBtn.w, colorsBtn.y+colorsBtn.h), (255,255,255), 2)

        # Tạo nút nhấn chọn bảng trắng (put white board button)
        boardBtn.drawRect(frame)
        cv2.rectangle(frame, (boardBtn.x, boardBtn.y), (boardBtn.x +boardBtn.w, boardBtn.y+boardBtn.h), (255,255,255), 2)

        # Mở bảng trắng trên khung hình (put the white board on the frame)
        if not hideBoard:       
            whiteBoard.drawRect(frame)
            # Chuyển đường vẽ vào khung hình chính (moving the draw to the main image)
            canvasGray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
            _, imgInv = cv2.threshold(canvasGray, 20, 255, cv2.THRESH_BINARY_INV)
            canvasBin = imgInv
            imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
            gray2rgb = imgInv
            frame = cv2.bitwise_and(frame, imgInv)
            frameAnd = frame
            frame = cv2.bitwise_or(frame, canvas)
            frameOr = frame


        ########## pen colors' boxes #########
        if not hideColors:
            for c in colors:
                c.drawRect(frame)
                cv2.rectangle(frame, (c.x, c.y), (c.x +c.w, c.y+c.h), (255,255,255), 2)

            clear.drawRect(frame)
            cv2.rectangle(frame, (clear.x, clear.y), (clear.x +clear.w, clear.y+clear.h), (255,255,255), 2)


        ########## brush size boxes ######
        penBtn.color = color
        penBtn.drawRect(frame)
        cv2.rectangle(frame, (penBtn.x, penBtn.y), (penBtn.x + penBtn.w, penBtn.y + penBtn.h), (255,255,255), 2)
        if not hidePenSizes:
            for pen in pens:
                pen.drawRect(frame)
                cv2.rectangle(frame, (pen.x, pen.y), (pen.x + pen.w, pen.y + pen.h), (255,255,255), 2)


        cv2.imshow('Virtual Board', frame)
        cv2.imshow('canvas', canvas)
        cv2.imshow('canvasGray',canvasGray)
        cv2.imshow('canvasBin',canvasBin)
        cv2.imshow('gray2rgb',gray2rgb)
        cv2.imshow('frameAnd',frameAnd)
        cv2.imshow('frameOr',frameOr)
        k = cv2.waitKey(1)
        if k == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()


frm = Tk()
frm.geometry("1280x720")
bg = PhotoImage(file = r'background.png')
label1 = Label(frm, image = bg)
label1.place(x = 0, y = 0)
frm.title("Image Processing Project")
btn_Run = Button(frm, text="Run Program", font=("Consolas", 14, "bold"), bg="cyan", fg="red", command=main_program)
btn_Run.place(x=580, y=330)
frm.mainloop()