import requests, os, base64 as b64lib, re

# --- 헬퍼 함수 ---
def esc(text):
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def trunc(text, n):
    return text[:n-1] + '...' if len(text) > n else text

def fetch_b64(url):
    try:
        r = requests.get(url, timeout=5)
        return f"data:image/jpeg;base64,{b64lib.b64encode(r.content).decode()}"
    except:
        return None

def generate_svg(top_artists, recent_tracks):
    W, H = 820, 310
    FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif"

    BG       = "#0d1117"
    SURFACE  = "#161b22"
    BORDER   = "#21262d"
    T_PRI    = "#e6edf3"
    T_SEC    = "#8b949e"
    T_MUT    = "#484f58"
    GOLD     = "#EF9F27"
    SILVER   = "#9EA3A8"
    BRONZE   = "#CD7F32"
    GREEN    = "#1DB954"

    # 포디움 설정
    # 열 순서 (왼쪽→오른쪽): 4등, 2등, 1등, 3등, 5등
    col_ranks   = [3, 1, 0, 2, 4]
    bar_h       = {0: 110, 1: 80, 2: 60, 3: 40, 4: 25}
    bar_colors  = {0: GOLD, 1: SILVER, 2: BRONZE, 3: "#3d444d", 4: "#2d333b"}
    bar_tc      = {0: "#2a1500", 1: "#1a1a1a", 2: "#2a1000", 3: T_SEC, 4: T_SEC}
    img_r       = {0: 30, 1: 26, 2: 23, 3: 21, 4: 19}
    col_x       = [68, 150, 232, 314, 396]
    base_y      = 278
    bar_w       = 62
    gap         = 10

    p = []
    p.append(f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">')

    # --- ClipPath 정의 ---
    p.append('<defs>')
    for ci, rank in enumerate(col_ranks):
        if rank >= len(top_artists):
            continue
        r  = img_r[rank]
        cx = col_x[ci]
        cy = base_y - bar_h[rank] - gap - r
        p.append(f'<clipPath id="a{ci}"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>')
    for i in range(len(recent_tracks)):
        tx, ty = 478, 50 + i * 50
        p.append(f'<clipPath id="t{i}"><rect x="{tx}" y="{ty}" width="34" height="34" rx="4"/></clipPath>')
    p.append('</defs>')

    # --- 배경 ---
    p.append(f'<rect width="{W}" height="{H}" fill="{BG}" rx="12"/>')

    # --- 왼쪽: Top Artists ---
    p.append(f'<text x="20" y="26" font-family="{FONT}" font-size="12" font-weight="500" fill="{T_SEC}">Top Artists</text>')

    for ci, rank in enumerate(col_ranks):
        if rank >= len(top_artists):
            continue
        a  = top_artists[rank]
        cx = col_x[ci]
        bh = bar_h[rank]
        r  = img_r[rank]
        by = base_y - bh
        cy = by - gap - r

        # 단상 막대
        p.append(f'<rect x="{cx-bar_w//2}" y="{by}" width="{bar_w}" height="{bh}" fill="{bar_colors[rank]}" rx="4"/>')

        # 등수
        p.append(f'<text x="{cx}" y="{by+bh//2+5}" text-anchor="middle" font-family="{FONT}" font-size="14" font-weight="bold" fill="{bar_tc[rank]}">{rank+1}</text>')

        # 아티스트 이미지
        if a.get('img_b64'):
            p.append(f'<image href="{a["img_b64"]}" x="{cx-r}" y="{cy-r}" width="{r*2}" height="{r*2}" clip-path="url(#a{ci})" preserveAspectRatio="xMidYMid slice"/>')
        else:
            p.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{SURFACE}"/>')

        # 링 테두리
        ring_c = GOLD if rank == 0 else BORDER
        ring_w = 2 if rank == 0 else 1
        p.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{ring_c}" stroke-width="{ring_w}"/>')

        # 아티스트 이름
        p.append(f'<text x="{cx}" y="{cy+r+13}" text-anchor="middle" font-family="{FONT}" font-size="9" fill="{T_SEC}">{esc(trunc(a["name"], 9))}</text>')

    # 바닥선
    p.append(f'<line x1="20" y1="{base_y}" x2="430" y2="{base_y}" stroke="{BORDER}" stroke-width="1.5"/>')

    # --- 구분선 ---
    p.append(f'<line x1="447" y1="15" x2="447" y2="{H-15}" stroke="{BORDER}" stroke-width="0.5"/>')

    # --- 오른쪽: Recently Played ---
    p.append(f'<text x="462" y="26" font-family="{FONT}" font-size="12" font-weight="500" fill="{T_SEC}">Recently Played</text>')
    p.append(f'<line x1="462" y1="34" x2="{W-20}" y2="34" stroke="{BORDER}" stroke-width="0.5"/>')

    for i, track in enumerate(recent_tracks):
        ty = 50 + i * 50
        tx = 478

        # 번호
        p.append(f'<text x="463" y="{ty+22}" font-family="{FONT}" font-size="10" fill="{T_MUT}">{i+1}</text>')

        # 앨범 이미지
        if track.get('album_img_b64'):
            p.append(f'<image href="{track["album_img_b64"]}" x="{tx}" y="{ty}" width="34" height="34" clip-path="url(#t{i})" preserveAspectRatio="xMidYMid slice"/>')
        else:
            p.append(f'<rect x="{tx}" y="{ty}" width="34" height="34" rx="4" fill="{SURFACE}"/>')

        # 곡명
        p.append(f'<text x="{tx+42}" y="{ty+14}" font-family="{FONT}" font-size="12" font-weight="500" fill="{T_PRI}">{esc(trunc(track["name"], 25))}</text>')

        # 아티스트
        p.append(f'<text x="{tx+42}" y="{ty+28}" font-family="{FONT}" font-size="10" fill="{T_SEC}">{esc(trunc(track["artist"], 28))}</text>')

        # Spotify 아이콘
        p.append(f'<circle cx="{W-28}" cy="{ty+17}" r="8" fill="{GREEN}"/>')
        p.append(f'<text x="{W-28}" y="{ty+21}" text-anchor="middle" font-family="{FONT}" font-size="9" fill="white">&#9835;</text>')

    p.append('</svg>')
    return '\n'.join(p)


# --- 1단계: 액세스 토큰 갱신 ---
auth_str = f"{os.environ['CLIENT_ID']}:{os.environ['CLIENT_SECRET']}"
auth_b64 = b64lib.b64encode(auth_str.encode()).decode()

token_res = requests.post("https://accounts.spotify.com/api/token",
    data={"grant_type": "refresh_token", "refresh_token": os.environ['REFRESH_TOKEN']},
    headers={"Authorization": f"Basic {auth_b64}"})

access_token = token_res.json().get("access_token")
if not access_token:
    raise Exception(f"토큰 발급 실패: {token_res.json()}")

headers = {"Authorization": f"Bearer {access_token}"}

# --- 2단계: Top Artists 가져오기 (이미지 포함) ---
artist_res = requests.get("https://api.spotify.com/v1/me/top/artists?limit=15&time_range=short_term", headers=headers)
artist_res.raise_for_status()

top_artists = []
seen_artists = set()
for artist in artist_res.json().get('items', []):
    if artist['name'] not in seen_artists:
        seen_artists.add(artist['name'])
        img_url = artist['images'][0]['url'] if artist.get('images') else None
        top_artists.append({
            'name': artist['name'],
            'img_b64': fetch_b64(img_url) if img_url else None
        })
    if len(top_artists) == 5:
        break

# --- 3단계: Recently Played 가져오기 (앨범 이미지 포함) ---
recent_res = requests.get("https://api.spotify.com/v1/me/player/recently-played?limit=20", headers=headers)
recent_res.raise_for_status()

recent_tracks = []
seen_tracks = set()
for item in recent_res.json().get('items', []):
    track = item['track']
    if track['id'] not in seen_tracks:
        seen_tracks.add(track['id'])
        album_img_url = track['album']['images'][0]['url'] if track['album'].get('images') else None
        recent_tracks.append({
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album_img_b64': fetch_b64(album_img_url) if album_img_url else None
        })
    if len(recent_tracks) == 5:
        break

# --- 4단계: SVG 생성 및 저장 ---
svg_content = generate_svg(top_artists, recent_tracks)
with open("spotify_card.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)
print("✅ spotify_card.svg 생성 완료!")

# --- 5단계: README.md 업데이트 ---
with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

if "<!-- Spotify 시작 -->" not in readme:
    raise Exception("README.md에 '<!-- Spotify 시작 -->' 태그가 없습니다!")

new_content = '\n<img src="./spotify_card.svg" width="820" alt="Spotify Card"/>\n'
readme = re.sub(
    r"(<!-- Spotify 시작 -->).*?(<!-- Spotify 끝 -->)",
    rf"\g<1>{new_content}\g<2>",
    readme, flags=re.DOTALL
)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)
print("✅ README.md 업데이트 완료!")
