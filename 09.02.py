import pygame, sys, copy, random, os

pygame.init()

# ================= CONFIG =================
AI_DEPTH = 2
USE_IMAGES = True      # Set False to use shapes instead of PNGs

# ----------------------------
# 🔔 PNG IMAGE FOLDER 🔔
# Change this path to the folder where your PNGs are stored
# In your case:
IMAGE_FOLDER = r"C:\Users\MichałWojciechowski\Documents\CHESS_IMAGES"
# ----------------------------

# ================= CONSTANTS =================
WIDTH = HEIGHT = 640
SQ = WIDTH // 8
FPS = 60

LIGHT = (240,217,181)
DARK  = (181,136,99)
HIGHLIGHT = (120,180,120)
MOVE_HINT = (100,100,220)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess – PNG or Shapes")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

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
            print(f"Warning: {path} not found")
            piece_images[piece] = None

# ================= DRAWING =================
def draw_board():
    for r in range(8):
        for c in range(8):
            pygame.draw.rect(screen, LIGHT if (r+c)%2==0 else DARK,
                             (c*SQ,r*SQ,SQ,SQ))

def draw_shape(r,c,p):
    cx, cy = c*SQ+SQ//2, r*SQ+SQ//2
    color = (200,200,200) if p[0]=="w" else (50,50,50)
    outline = (245,245,245) if p[0]=="w" else (20,20,20)

    if p[1]=="p":
        pygame.draw.circle(screen, color, (cx,cy), SQ//4)
    elif p[1]=="r":
        pygame.draw.rect(screen, color, (cx-18,cy-18,36,36))
    elif p[1]=="n":
        pygame.draw.polygon(screen, color, [(cx,cy-20),(cx+20,cy+20),(cx-20,cy+20)])
    elif p[1]=="b":
        pygame.draw.polygon(screen, color, [(cx,cy-22),(cx+18,cy),(cx,cy+22),(cx-18,cy)])
    elif p[1]=="q":
        pygame.draw.circle(screen, color, (cx,cy), SQ//3)
    elif p[1]=="k":
        pygame.draw.rect(screen, color, (cx-14,cy-14,28,28))
    pygame.draw.circle(screen, outline, (cx,cy), SQ//3, 2)

def draw_pieces():
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p != "--":
                if USE_IMAGES and piece_images.get(p):
                    screen.blit(piece_images[p], (c*SQ,r*SQ))
                else:
                    draw_shape(r,c,p)

def draw_ui():
    if selected:
        r,c = selected
        pygame.draw.rect(screen, HIGHLIGHT, (c*SQ,r*SQ,SQ,SQ), 4)
        for m in legal:
            pygame.draw.circle(screen, MOVE_HINT,
                               (m[1]*SQ+SQ//2, m[0]*SQ+SQ//2), 8)

    if status:
        txt = font.render(status, True, (200,30,30))
        screen.blit(txt, (10,10))

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
        nb=make_move(b,((r,c),m))
        if not in_check(nb,col):
            lm.append(m)
    return lm

def all_legal(b,color):
    return [((r,c),m)
            for r in range(8)
            for c in range(8)
            if b[r][c]!="--" and b[r][c][0]==color
            for m in legal_moves(r,c,b)]

def make_move(b,m):
    nb=copy.deepcopy(b)
    (sr,sc),(er,ec)=m
    nb[er][ec]=nb[sr][sc]
    nb[sr][sc]="--"
    return nb

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
        sc,_=minimax(make_move(b,m),d-1,not maxing)
        if (maxing and sc>val) or (not maxing and sc<val):
            val,best=sc,m
    return val,best

# ================= GAME LOOP =================
running=True
while running:
    clock.tick(FPS)
    draw_board()
    draw_pieces()
    draw_ui()

    status = "CHECK" if in_check(board,turn) else ""

    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            running=False

        if e.type==pygame.MOUSEBUTTONDOWN and turn=="w":
            r,c = pygame.mouse.get_pos()[1]//SQ, pygame.mouse.get_pos()[0]//SQ
            if selected and (r,c) in legal:
                board = make_move(board,(selected,(r,c)))
                selected=None
                legal=[]
                turn="b"
            elif board[r][c]!="--" and board[r][c][0]=="w":
                selected=(r,c)
                legal=legal_moves(r,c,board)

    if turn=="b":
        _,m=minimax(board,AI_DEPTH,True)
        if m: board=make_move(board,m)
        turn="w"

    if not all_legal(board,turn):
        status = "CHECKMATE" if in_check(board,turn) else "STALEMATE"

    pygame.display.flip()

pygame.quit()
sys.exit()
