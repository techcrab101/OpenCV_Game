import cv2
import random
import time
import numpy as np

class Enemy():
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius

class App():
    def __init__(self, cam):
        # Lower and upper bounds for the H, S, V values respectively
        self.minHue = 74
        self.minSaturation = 129
        self.minValue = 11
        self.maxHue = 255
        self.maxSaturation = 255
        self.maxValue = 255
        self.lowerHSV = np.array([self.minHue, self.minSaturation, self.minValue])
        self.upperHSV = np.array([self.maxHue, self.maxSaturation, self.maxValue])

        self.cap = cv2.VideoCapture(cam)
        self.imgWidth = 1280
        self.imgHeight = 720
        self.cap.set(3, self.imgWidth)
        self.cap.set(4, self.imgHeight)
        self.resolution = 1

        self.font = cv2.FONT_HERSHEY_DUPLEX

        self.paddleRadius = 20
        self.paddleVisible = False
        self.paddleX = 0
        self.paddleY = 0

        self.ForegroundElements = []

        self.score = 0
        self.t0 = time.time()
        self.totalTime = 1
        self.gameState = "Running"

        self.enemyCount = 5
        self.enemySpawnBorder = self.resolution + 20

        self.high_score = 0

        self.time_on_button = 3

    def findPaddle(self, cntrs, hierarchy):
        if len(cntrs) == 0:
            return None

        biggestArea = 0
        Cnt = None

        for i in range(len(cntrs)):
            cnt = cntrs[i]
            area = cv2.contourArea(cnt)

            if area < biggestArea:
                continue

            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)

            if hull_area > 0:
                targetSolidity = 1
                solidityTolerance = 0.25

                minSolidity = targetSolidity - solidityTolerance
                maxSolidity = targetSolidity + solidityTolerance

                solidity = float(area) / hull_area

                if minSolidity < solidity and solidity < maxSolidity:
                    if hierarchy[0][i][2] != -1 and hierarchy[0][i][3] == -1:
                        Cnt = cnt
                        biggestArea = area

        return Cnt

    def generateEnemy(self):
        intX = random.randrange(self.enemySpawnBorder,
                                self.imgWidth - self.enemySpawnBorder, 1)
        intY = random.randrange(self.enemySpawnBorder,
                                self.imgHeight - self.enemySpawnBorder, 1)
        radius = random.randrange(20, 50, 1)
        #id = uuid.uuid4
        enemy = Enemy(intX, intY, radius)
        self.ForegroundElements.append(enemy)

    def drawMenu(self):
        intX = int(self.imgWidth/2)
        intY = int(self.imgHeight - (self.imgHeight/4))
        radius = 25

        enemy = Enemy(intX, intY, radius)
        self.ForegroundElements.append(enemy)

    def getPaddle(self):
        self.hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)

        # Creates a image Threshold based on the lower and upper bounds on HSV values
        self.imgThresh = cv2.inRange(self.hsv, self.lowerHSV, self.upperHSV)

        #self.imgThresh = cv2.GaussianBlur(self.imgThresh, (7, 7), 0)
        #self.imgThresh = cv2.erode(self.imgThresh, np.ones((3,3), np.uint8), iterations=4)

        # We really don't need to use im2 and hierarchy variables, just ignore these for now
        # [Next, Previous, First_Child, Parent]
        self.contours, self.hierarchy = cv2.findContours(self.imgThresh,
                                         cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2:]

        self.paddle = self.findPaddle(self.contours, self.hierarchy)#self.sortedContours)

    def drawPaddle(self):
        # Draw the Paddle
        self.paddleVisible = not (self.paddle is None)
        if self.paddleVisible:
            self.paddleMoment = cv2.moments(self.paddle)
            self.paddleX = int(self.paddleMoment['m10'] / self.paddleMoment['m00']) \
                           * self.resolution
            self.paddleY = int(self.paddleMoment['m01'] / self.paddleMoment['m00']) \
                           * self.resolution

            cv2.circle(self.originalImg, (self.paddleX, self.paddleY),
                       self.paddleRadius, (0, 255, 0), 20)
            cv2.drawContours(self.originalImg, [self.paddle * self.resolution],
                             0, (255, 0, 0), 2)

        cv2.drawContours(self.originalImg, self.contours, -1, (255, 0, 0), 2)

    def updateGame(self):
        self.t1 = time.time()

        self.captureSuccess, self.originalImg = self.cap.read()
        self.originalImg = cv2.flip(self.originalImg, 1)

        self.img = cv2.resize(self.originalImg, None
                              , fx=(1/self.resolution), fy = (1/self.resolution))

        if self.gameState == "End":
            cv2.putText(self.originalImg, "Score: {}".format(self.score),
                        (int( 50 ), int(100)),
                        self.font, 2.5, (0, 0, 0), 3)
            cv2.putText(self.originalImg, "Score: {}".format(self.score),
                        (int(55), int(95)),
                        self.font, 2.5, (255, 255, 255), 3)
            cv2.putText(self.originalImg, "Highscore: {}".format(self.high_score),
                        (int(50), int(150)),
                        self.font, 1.0, (0, 0, 0), 3)
            cv2.putText(self.originalImg, "Highscore: {}".format(self.high_score),
                        (int(55), int(145)),
                        self.font, 1.0, (255, 255, 255), 3)
            self.getPaddle()
            self.drawPaddle()
            self.ForegroundElements.clear()
            self.drawMenu()

            for object in self.ForegroundElements:

                cv2.putText(self.originalImg, "Restarting in {}".format(self.time_on_button),
                            (int(object.x/2), int(object.y - object.radius - 20)),
                            self.font, 1.0, (0, 0, 0), 3)
                cv2.putText(self.originalImg,
                            "Restarting in {}".format(self.time_on_button),
                            (
                            int(object.x / 2) + 5, int(object.y - object.radius - 20) - 5),
                            self.font, 1.0, (255, 255, 255), 3)
                cv2.circle(self.originalImg, (object.x, object.y), object.radius
                           , (0, 0, 255), 10)


                self.enemyCenter = np.array((object.x, object.y))
                self.paddleCenter = np.array((self.paddleX, self.paddleY))

                self.dist = np.linalg.norm(self.enemyCenter - self.paddleCenter)
                self.collisionRange = self.paddleRadius + 20 + object.radius
                if self.dist < self.collisionRange:
                    if (self.t1 - self.t0) >= 1:
                        self.t0 = time.time()
                        self.time_on_button -= 1

                    if self.time_on_button <= 0:
                        self.totalTime = 60
                        self.gameState = "Running"
                        if self.score > self.high_score:
                            self.high_score = self.score
                        self.score = 0
                else:
                    self.time_on_button = 3

            return self.originalImg

        if self.totalTime <= 0:
            self.gameState = "End"
            self.ForegroundElements.clear()

        if (self.t1 - self.t0) >= 1:
            self.t0 = time.time()
            self.totalTime -= 1

        self.getPaddle()

        while len(self.ForegroundElements) < (self.enemyCount):
            self.generateEnemy()

        # Draw all the Objects

        # Draw Text
        cv2.putText(self.originalImg, "Score: {}".format(self.score), (50, 50),
                    self.font, 1.0, (0, 0, 0), 3)
        cv2.putText(self.originalImg, "Score: {}".format(self.score), (50 + 5, 50 - 5),
                    self.font, 1.0, (255, 255, 255), 3)
        cv2.putText(self.originalImg, "Highscore: {}".format(self.high_score), (50, 100),
                    self.font, 1.0, (0, 0, 0), 3)
        cv2.putText(self.originalImg, "Highscore: {}".format(self.high_score),
                    (50 + 5, 100 - 5),
                    self.font, 1.0, (255, 255, 255), 3)
        cv2.putText(self.originalImg, "Time: {}".format(self.totalTime), (50, 150),
                    self.font, 1.0, (0, 0, 0), 3)
        cv2.putText(self.originalImg, "Time: {}".format(self.totalTime), (50 + 5, 150 - 5),
                    self.font, 1.0, (255, 255, 255), 3)

        self.drawPaddle()

        # Draw the enemies
        for object in self.ForegroundElements:
            if self.paddleVisible:
                # Check the Collisions
                self.enemyCenter = np.array((object.x, object.y))
                self.paddleCenter = np.array((self.paddleX, self.paddleY))

                self.dist = np.linalg.norm(self.enemyCenter - self.paddleCenter)
                self.collisionRange = self.paddleRadius + 20 + object.radius
                if self.dist < self.collisionRange:
                    self.ForegroundElements.remove(object)
                    self.score += 1

            cv2.circle(self.originalImg, (object.x, object.y), object.radius
                       , (0,0,255), 10)

        return self.originalImg

App = App(0)

while True:
    cv2.imshow("Window", App.updateGame())

    cv2.waitKey(1)
