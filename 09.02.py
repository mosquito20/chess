import pygame, sys, copy, random, os

pygame.init()

# ================= CONFIG =================
AI_DEPTH = 2
USE_IMAGES = True

IMAGE_FOLDER = r"C:\Users\MichałWojciechowski\Documents\CHESS_IMAGES"

# ================= CONSTANTS =================
BOARD_SIZE = 640
PANEL_WIDTH = 200
WIDTH = BOARD_SIZE + PANEL_WIDTH
HEIGHT = BOARD_SIZE
SQ = BOARD_SIZE // 8
FPS = 60

LIGHT = (240,217,181)
DARK  = (181,136,99)
HIGHLIGHT = (120,180,120)
MOVE_HINT = (0, 200, 255)
CAPTURE_HINT = (255, 80, 80)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess – Animated Edition")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)

# ================= BOARD =================
board = [
    ["br","bn","bb","bq","bk","bb","bn","br"],
    ["bp","bp","bp","bp","bp","bp","bp","bp"],
    ["--","--","--","--","--","--","--","--"],
    ["--","--","--","--","--","--","--","--"],
    ["--","--","--","--","--","--","--","--"],
    ["--","--","--","--","--","--","--","--"],
    ["wp","wp","wp","wp","wp","wp","wp","wp"],
    ["wr","wn","wb","wq","wk","wb","wn","wr"],
]

turn = "w"
selected = None
legal = []
status = ""
move_history = []

# ================= ANIMATION =================
AI_DELAY = 600
ai_thinking = False
ai_move = None
ai_start_time = 0

animating = False
anim_piece = None
anim_from = None
anim_to = None
anim_progress = 0
ANIM_SPEED = 0.05

captured_piece = None
capture_anim_progress = 0

# ================= LOAD IMAGES =================
piece_images = {}
if USE_IMAGES:
    for piece in ["wp","wr","wn","wb","wq","wk",
                  "bp","br","bn","bb","bq","bk"]:
        path = os.path.join(IMAGE_FOLDER,f"{piece}.png")
        if os.path.exists(path):
            img = pygame.image.load(path)
            piece_images[piece] = pygame.transform.smoothscale(img,(SQ,SQ))
        else:
            piece_images[piece] = None

# ================= DRAWING =================
def draw_board():
    for r in range(8):
        for c in range(8):
            pygame.draw.rect(screen, LIGHT if (r+c)%2==0 else DARK,
                             (c*SQ,r*SQ,SQ,SQ))

def draw_shape(r,c,p):
    cx, cy = c*SQ+SQ//2, r*SQ+SQ//2
    color = (220,220,220) if p[0]=="w" else (40,40,40)
    pygame.draw.circle(screen, color, (cx,cy), SQ//3)

def draw_pieces():
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p != "--" and not (animating and (r,c)==anim_from):
                if USE_IMAGES and piece_images.get(p):
                    screen.blit(piece_images[p], (c*SQ,r*SQ))
                else:
                    draw_shape(r,c,p)

def draw_ui():
    if selected:
        r,c = selected
        pygame.draw.rect(screen, HIGHLIGHT, (c*SQ,r*SQ,SQ,SQ), 4)
        for m in legal:
            r2,c2 = m
            center = (c2*SQ+SQ//2, r2*SQ+SQ//2)
            if board[r2][c2] != "--":
                pygame.draw.circle(screen, CAPTURE_HINT, center, 18, 3)
            else:
                pygame.draw.circle(screen, MOVE_HINT, center, 10)

    if status:
        txt = font.render(status, True, (200,30,30))
        screen.blit(txt, (10,10))

def draw_panel():
    panel_rect = pygame.Rect(BOARD_SIZE, 0, PANEL_WIDTH, HEIGHT)
    pygame.draw.rect(screen, (40,40,40), panel_rect)

    undo_btn = pygame.Rect(BOARD_SIZE+30, 200, 140, 50)
    giveup_btn = pygame.Rect(BOARD_SIZE+30, 300, 140, 50)

    pygame.draw.rect(screen, (90,90,90), undo_btn)
    pygame.draw.rect(screen, (150,60,60), giveup_btn)

    screen.blit(font.render("Undo", True, (255,255,255)),
                (undo_btn.x+40, undo_btn.y+10))
    screen.blit(font.render("Give Up", True, (255,255,255)),
                (giveup_btn.x+20, giveup_btn.y+10))

    return undo_btn, giveup_btn

# ================= CHESS LOGIC =================
def in_bounds(r,c): return 0<=r<8 and 0<=c<8

def king_pos(b,color):
    for r in range(8):
        for c in range(8):
            if b[r][c]==color+"k":
                return r,c

def raw_moves(r,c,b):
    p=b[r][c]; col=p[0]; t=p[1]
    moves=[]
    if t=="p":
        d=-1 if col=="w" else 1
        start=6 if col=="w" else 1
        if in_bounds(r+d,c) and b[r+d][c]=="--":
            moves.append((r+d,c))
            if r==start and b[r+2*d][c]=="--":
                moves.append((r+2*d,c))
        for dc in (-1,1):
            if in_bounds(r+d,c+dc) and b[r+d][c+dc]!="--" and b[r+d][c+dc][0]!=col:
                moves.append((r+d,c+dc))
    if t=="n":
        for dr,dc in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
            nr,nc=r+dr,c+dc
            if in_bounds(nr,nc) and (b[nr][nc]=="--" or b[nr][nc][0]!=col):
                moves.append((nr,nc))
    dirs=[]
    if t=="r": dirs=[(1,0),(-1,0),(0,1),(0,-1)]
    if t=="b": dirs=[(1,1),(1,-1),(-1,1),(-1,-1)]
    if t=="q": dirs=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
    if t=="k": dirs=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
    for dr,dc in dirs:
        nr,nc=r+dr,c+dc
        while in_bounds(nr,nc):
            if b[nr][nc]=="--":
                moves.append((nr,nc))
            else:
                if b[nr][nc][0]!=col:
                    moves.append((nr,nc))
                break
            if t=="k": break
            nr+=dr; nc+=dc
    return moves

def in_check(b,color):
    kr,kc = king_pos(b,color)
    for r in range(8):
        for c in range(8):
            if b[r][c]!="--" and b[r][c][0]!=color:
                if (kr,kc) in raw_moves(r,c,b):
                    return True
    return False

def legal_moves(r,c,b):
    col=b[r][c][0]
    lm=[]
    for m in raw_moves(r,c,b):
        nb=make_move(copy.deepcopy(b),((r,c),m),save=False)
        if not in_check(nb,col):
            lm.append(m)
    return lm

def all_legal(b,color):
    return [((r,c),m)
            for r in range(8)
            for c in range(8)
            if b[r][c]!="--" and b[r][c][0]==color
            for m in legal_moves(r,c,b)]

def make_move(b,m,save=True):
    if save:
        move_history.append(copy.deepcopy(b))
    (sr,sc),(er,ec)=m
    b[er][ec]=b[sr][sc]
    b[sr][sc]="--"
    return b

def evaluate(b):
    VALUES = {"p":1,"n":3,"b":3,"r":5,"q":9,"k":1000}
    return sum(
        VALUES[p[1]] if p[0]=="b" else -VALUES[p[1]]
        for row in b for p in row if p!="--"
    )

def minimax(b,d,maxing):
    if d==0:
        return evaluate(b),None
    moves=all_legal(b,"b" if maxing else "w")
    if not moves:
        return (-9999 if maxing else 9999),None
    best=None
    val=-9999 if maxing else 9999
    for m in moves:
        sc,_=minimax(copy.deepcopy(make_move(copy.deepcopy(b),m,False)),d-1,not maxing)
        if (maxing and sc>val) or (not maxing and sc<val):
            val,best=sc,m
    return val,best

# ================= ANIMATION =================
def ease_out(t):
    return 1 - (1 - t) * (1 - t)

def draw_animation():
    global anim_progress, animating, turn
    global captured_piece, capture_anim_progress

    if not animating:
        return

    sr, sc = anim_from
    er, ec = anim_to

    eased = ease_out(anim_progress)

    x = sc*SQ + (ec-sc)*SQ*eased
    y = sr*SQ + (er-sr)*SQ*eased

    if captured_piece and capture_anim_progress < 1:
        capture_anim_progress += 0.1
        scale = 1 - capture_anim_progress
        size = int(SQ * scale)
        if size > 0 and USE_IMAGES and piece_images.get(captured_piece):
            img = pygame.transform.smoothscale(piece_images[captured_piece],(size,size))
            screen.blit(img,(ec*SQ+SQ//2-size//2,er*SQ+SQ//2-size//2))

    if USE_IMAGES and piece_images.get(anim_piece):
        screen.blit(piece_images[anim_piece], (x, y))
    else:
        draw_shape(int(y//SQ), int(x//SQ), anim_piece)

    anim_progress += ANIM_SPEED

    if anim_progress >= 1:
        make_move(board,(anim_from,anim_to))
        animating = False
        captured_piece = None
        capture_anim_progress = 0
        turn = "w"

# ================= GAME LOOP =================
running=True
while running:
    clock.tick(FPS)
    draw_board()
    draw_pieces()
    draw_animation()
    draw_ui()
    undo_btn, giveup_btn = draw_panel()

    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            running=False

        if e.type==pygame.MOUSEBUTTONDOWN:
            mx,my = pygame.mouse.get_pos()

            if undo_btn.collidepoint(mx,my) and move_history:
                board = move_history.pop()
                turn="w"

            if giveup_btn.collidepoint(mx,my):
                status="YOU GAVE UP, YOU ARE"

            if turn=="w" and mx<BOARD_SIZE:
                r,c = my//SQ, mx//SQ
                if selected and (r,c) in legal:
                    make_move(board,(selected,(r,c)))
                    selected=None
                    legal=[]
                    turn="b"
                elif board[r][c]!="--" and board[r][c][0]=="w":
                    selected=(r,c)
                    legal=legal_moves(r,c,board)

    if turn=="b" and not animating:
        _, ai_move = minimax(copy.deepcopy(board),AI_DEPTH,True)
        if ai_move:
            anim_from, anim_to = ai_move
            anim_piece = board[anim_from[0]][anim_from[1]]
            captured_piece = board[anim_to[0]][anim_to[1]] if board[anim_to[0]][anim_to[1]]!="--" else None
            anim_progress=0
            capture_anim_progress=0
            animating=True

    pygame.display.flip()

pygame.quit()
sys.exit()
