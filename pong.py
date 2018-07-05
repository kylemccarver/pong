import sys, math, random, time, pygame
from pygame.locals import *

WINWIDTH = 700
WINHEIGHT = 500
FPS = 60
PADDLEWIDTH = 20
PADDLEHEIGHT = 70
PADDLESPEED = 5
BALLSIZE = 20
MAX_ANGLE = (5 * math.pi) / 2 # 75 deg
WINSCORE = 5

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
BGCOLOR = BLACK

UP = "up"
DOWN = "down"

WALL_TOP_RECT = pygame.Rect(0, 0, WINWIDTH, BALLSIZE)
WALL_BOTTOM_RECT = pygame.Rect(0, WINHEIGHT - BALLSIZE, WINWIDTH, BALLSIZE)


def main():
    global FPSCLOCK, DISPLAYSURF, BASICFONT, BOOP, BEEP

    pygame.init()

    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINWIDTH, WINHEIGHT))
    pygame.display.set_caption("Pong")
    BASICFONT = pygame.font.Font(None, 50)

    gameOverSurf = BASICFONT.render("Game!", 1, WHITE)
    gameOverRect = gameOverSurf.get_rect()
    gameOverRect.center = (WINWIDTH / 2, (WINHEIGHT / 3) - 50)

    instSurf = BASICFONT.render("Press any key to begin", 1, WHITE)
    instRect = instSurf.get_rect()
    instRect.center = ((WINWIDTH / 2), WINHEIGHT - 50)

    # Sounds
    BOOP = pygame.mixer.Sound("boop.ogg")
    BEEP = pygame.mixer.Sound("beep.ogg")
    WOO = pygame.mixer.Sound("woo.ogg")
    
    # Game objects
    playerRect = pygame.Rect(20, (WINHEIGHT / 2) - (PADDLEHEIGHT / 2), PADDLEWIDTH, PADDLEHEIGHT)
    opponentRect = pygame.Rect(WINWIDTH - 20 - PADDLEWIDTH, (WINHEIGHT / 2) - (PADDLEHEIGHT / 2), PADDLEWIDTH, PADDLEHEIGHT)
    ball = {"x": (WINWIDTH / 2) - (BALLSIZE / 2),
            "y": (WINHEIGHT / 2) - (BALLSIZE / 2),
            "dx": random.choice((-1, 1)),
            "dy": random.random(),
            "speed": 5.0,
            "rect": pygame.Rect((WINWIDTH / 2) - (BALLSIZE / 2), (WINHEIGHT / 2) - (BALLSIZE / 2), BALLSIZE, BALLSIZE)}

    moveUpPlayer = False
    moveDownPlayer = False
    
    playerScore = 0
    opponentScore = 0

    gameOverMode = False
    scored = None
    scoreTime = 0

    DISPLAYSURF.fill(BGCOLOR)
    drawBackground()
    # Draw ball
    pygame.draw.rect(DISPLAYSURF, WHITE, ball["rect"])
    # Draw player
    pygame.draw.rect(DISPLAYSURF, WHITE, playerRect)
    # Draw opponent
    pygame.draw.rect(DISPLAYSURF, WHITE, opponentRect)
    DISPLAYSURF.blit(instSurf, instRect)
    while checkForKeyPress() == None:
        pygame.display.update()

    while True:
        
        DISPLAYSURF.fill(BGCOLOR)
        # Draw walls and score
        drawBackground()
        drawScore(playerScore, opponentScore)

        # Handle events
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            elif event.type == KEYDOWN:
                if event.key in (K_UP, K_w):
                    moveUpPlayer = True
                    moveDownPlayer = False
                elif event.key in (K_DOWN, K_s):
                    moveDownPlayer = True
                    moveUpPlayer = False
                elif event.key == K_f:
                    if DISPLAYSURF.get_flags() & FULLSCREEN:
                        pygame.display.set_mode((WINWIDTH, WINHEIGHT))
                    else:
                        pygame.display.set_mode((WINWIDTH, WINHEIGHT), FULLSCREEN)
            elif event.type == KEYUP:
                if event.key == K_ESCAPE:
                    terminate()
                elif event.key in (K_UP, K_w):
                    moveUpPlayer = False
                elif event.key in (K_DOWN, K_s):
                    moveDownPlayer = False

        if not gameOverMode:
            # Move ball
            ball["rect"].move_ip(ball["dx"] * ball["speed"], ball["dy"] * ball["speed"])
            ball["x"] = ball["rect"].left
            ball["y"] = ball["rect"].top

            # Move opponent
            # if ball traveling up, move paddle up; if ball moving down, move paddle down
            # Computer attempts to line up the center of the paddle with the center of the ball
            if ball["rect"].centery < opponentRect.centery:
                opponentRect.move_ip(0, -1 * PADDLESPEED)
            elif ball["rect"].centery > opponentRect.centery:
                opponentRect.move_ip(0, 1 * PADDLESPEED)
            if opponentRect.top < WALL_TOP_RECT.bottom:
                opponentRect.top = WALL_TOP_RECT.bottom
            elif opponentRect.bottom > WALL_BOTTOM_RECT.top:
                opponentRect.bottom = WALL_BOTTOM_RECT.top

            # Move player
            if moveUpPlayer and playerRect.top > WALL_TOP_RECT.bottom:
                playerRect.move_ip(0, -1 * PADDLESPEED)
            elif moveDownPlayer and playerRect.bottom < WALL_BOTTOM_RECT.top:
                playerRect.move_ip(0, 1 * PADDLESPEED)

            # Check collisions (ball + walls, ball + paddle)
            if ball["x"] < -BALLSIZE: # went past the left edge of the screen
                opponentScore += 1
                if opponentScore >= WINSCORE:
                    gameOverMode = True
                reset(playerRect, opponentRect, ball)
                scored = "opponent"
                scoreTime = time.time()
            elif ball["x"] > WINWIDTH: # went past the right edge of the screen
                playerScore += 1
                if playerScore >= WINSCORE:
                    gameOverMode = True
                reset(playerRect, opponentRect, ball)
                scored = "player"
                scoreTime = time.time()

            if scored:
                if time.time() - scoreTime > 1:
                    if scored == "player":
                        ball["dx"] = 1
                        ball["dy"] = random.random()
                    else:
                        ball["dx"] = -1
                        ball["dy"] = random.random()
                    scored = None
                    scoreTime = 0

            if ball["y"] <= WALL_TOP_RECT.bottom: # hit top edge of screen
                ball["y"] = WALL_TOP_RECT.bottom
                ball["dy"] = -ball["dy"]
                BEEP.play()
            elif ball["y"] >= WALL_BOTTOM_RECT.top - BALLSIZE: # hit bottom edge of screen
                ball["y"] = WALL_BOTTOM_RECT.top - BALLSIZE
                ball["dy"] = -ball["dy"]
                BEEP.play()
            
            # Predict the position of the ball based on speed and direction before it collides with the paddle
            # This way the ball won't skip past the paddle if the speed is too fast
            # dy is adjusted based on the collision point's distance from the middle of the paddle
            predictedPos = (ball["rect"].left + ball["dx"] * ball["speed"], ball["rect"].top + ball["dy"] * ball["speed"])
            if predictedPos[0] <= playerRect.right and predictedPos[1] >= playerRect.top - (BALLSIZE - 1) and predictedPos[1] <= playerRect.bottom - 1:
                ball["rect"].left = playerRect.right
                ball["dx"] = -ball["dx"]
                ball["dy"] = angle(playerRect, ball)
                ball["speed"] += 0.5
                BOOP.play()
                predictedPos = (ball["rect"].left + ball["dx"] * ball["speed"], ball["rect"].top + ball["dy"] * ball["speed"])
            if predictedPos[0] >= opponentRect.left - BALLSIZE and predictedPos[1] >= opponentRect.top - (BALLSIZE - 1) and predictedPos[1] <= opponentRect.bottom + (BALLSIZE - 1):
                ball["rect"].right = opponentRect.left
                ball["dx"] = -ball["dx"]
                ball["dy"] = angle(opponentRect, ball)
                ball["speed"] += 0.5
                BOOP.play()
        else:
            reset(playerRect, opponentRect, ball)
            DISPLAYSURF.blit(gameOverSurf, gameOverRect)
            if playerScore > opponentScore:
                winSurf = BASICFONT.render("Player 1 wins!", 1, WHITE)
            else:
                winSurf = BASICFONT.render("The opponent wins!", 1, WHITE)
            winRect = winSurf.get_rect()
            winRect.center = ((WINWIDTH / 2), 2 * (WINHEIGHT / 3) - 50)
            DISPLAYSURF.blit(winSurf, winRect)
            DISPLAYSURF.blit(instSurf, instRect)
            pygame.display.update()
            WOO.play()
            checkForKeyPress()
            pygame.time.wait(500)
            # Wait for input to play again or quit
            while True:
                if checkForKeyPress():
                    pygame.event.get()
                    break

            gameOverMode = False
            scored = None
            playerScore = 0
            opponentScore = 0
            ball["dx"] = random.choice((-1, 1))
        
        # Draw ball
        pygame.draw.rect(DISPLAYSURF, WHITE, ball["rect"])
        # Draw player
        pygame.draw.rect(DISPLAYSURF, WHITE, playerRect)
        # Draw opponent
        pygame.draw.rect(DISPLAYSURF, WHITE, opponentRect)

        pygame.display.update()

        FPSCLOCK.tick(FPS)
                
def terminate():
    pygame.quit()
    sys.exit()

def drawBackground():
    pygame.draw.rect(DISPLAYSURF, GRAY, WALL_TOP_RECT)
    pygame.draw.rect(DISPLAYSURF, GRAY, WALL_BOTTOM_RECT)

    leftx = (WINWIDTH / 2) - (BALLSIZE / 2)
    topx = BALLSIZE

    while topx < WALL_BOTTOM_RECT.top:
        pygame.draw.rect(DISPLAYSURF, GRAY, (leftx, topx, BALLSIZE, BALLSIZE))
        topx += BALLSIZE * 2

def drawScore(playerScore, opponentScore):
    playerScoreSurf = BASICFONT.render("%s" % str(playerScore), 1, GRAY)
    playerScoreRect = playerScoreSurf.get_rect()
    playerScoreRect.topright = ((WINWIDTH / 2) - (BALLSIZE * 2), BALLSIZE * 2)
    DISPLAYSURF.blit(playerScoreSurf, playerScoreRect)

    opponentScoreSurf = BASICFONT.render("%s" % str(opponentScore), 1, GRAY)
    opponentScoreRect = opponentScoreSurf.get_rect()
    opponentScoreRect.topleft = ((WINWIDTH / 2) + (BALLSIZE * 2), BALLSIZE * 2)
    DISPLAYSURF.blit(opponentScoreSurf, opponentScoreRect)

def reset(playerRect, opponentRect, ball):
    # Player reset
    playerRect.topleft = (20, (WINHEIGHT / 2) - (PADDLEHEIGHT / 2))
    # Opponent reset
    opponentRect.topleft = (WINWIDTH - 20 - PADDLEWIDTH, (WINHEIGHT / 2) - (PADDLEHEIGHT / 2))
    # Ball reset
    ball["rect"].topleft = ((WINWIDTH / 2) - (BALLSIZE / 2), (WINHEIGHT / 2) - (BALLSIZE / 2))
    ball["x"] = ball["rect"].left
    ball["y"] = ball["rect"].top
    ball["dx"], ball["dy"] = (0, 0)
    ball["speed"] = 5.0

def angle(paddleRect, ball):
    ballCenter = ball["rect"].centery
    paddleCenter = paddleRect.centery
    dist = ballCenter - paddleCenter
    ratio = dist / (PADDLEHEIGHT / 2)
    return math.sin(ratio * MAX_ANGLE)

def checkForKeyPress():
    if len(pygame.event.get(QUIT)) > 0:
        terminate()
    
    keyUpEvents = pygame.event.get(KEYUP)
    if len(keyUpEvents) == 0:
        return None
    if keyUpEvents[0].key == K_ESCAPE:
        terminate()
    return keyUpEvents[0].key
    

if __name__ == "__main__":
    main()