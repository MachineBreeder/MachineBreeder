import requests, os, base64 as b64lib, re

# ──────────────────────────────────────────
# 헬퍼 함수
# ──────────────────────────────────────────
def esc(text):
    return str(text).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

def trunc(text, n):
    return text[:n-1] + '…' if len(text) > n else text

def fetch_b64(url):
    """이미지 URL을 base64로 변환 (GitHub SVG는 외부 URL 차단)"""
    try:
        r = requests.get(url, timeout=5)
        return f"data:image/jpeg;base64,{b64lib.b64encode(r.content).decode()}"
    except:
        return None

# ──────────────────────────────────────────
# SVG 생성
# ──────────────────────────────────────────
def generate_svg(top_artists, recent_tracks):
    W    = 800
    PAD  = 32
    FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif"

    # 색상
    BG     = "#0d1117"
    BORDER = "#21262d"
    T_PRI  = "#e6edf3"
    T_SEC  = "#8b949e"
    T_MUT  = "#484f58"
    GOLD   = "#EF9F27"

    # 아티스트 섹션 레이아웃
    A_R      = 48          # 아티스트 이미지 반지름
    A_IMG_CY = A_R + 42    # 이미지 중심 Y
    A_NAME_Y = A_IMG_CY + A_R + 20
    A_SEC_H  = A_NAME_Y + 20

    # 구분선
    DIV_Y = A_SEC_H + 10

    # 트랙 섹션 레이아웃
    T_IMG_SZ  = 44
    T_ROW_H   = 62
    T_LABEL_Y = DIV_Y + 30
    T_START_Y = DIV_Y + 50
    T_COL_W   = (W - PAD * 2) / 2

    H = T_START_Y + 5 * T_ROW_H + PAD

    svg = []
    svg.append(f'<svg width="{W}" height="{int(H)}" viewBox="0 0 {W} {int(H)}" xmlns="http://www.w3.org/2000/svg">')

    # ── ClipPath 정의 ──
    svg.append('<defs>')
    A_COL_W = (W - PAD * 2) / 5
    for i in range(len(top_artists)):
        cx = PAD + A_COL_W * i + A_COL_W / 2
        svg.append(f'<clipPath id="ac{i}"><circle cx="{cx:.1f}" cy="{A_IMG_CY}" r="{A_R}"/></clipPath>')
    for i in range(len(recent_tracks)):
        row = i // 2
        col = i % 2
        tx  = PAD + col * T_COL_W + 30
        ty  = T_START_Y + row * T_ROW_H + (T_ROW_H - T_IMG_SZ) / 2
        svg.append(f'<clipPath id="tc{i}"><rect x="{tx:.1f}" y="{ty:.1f}" width="{T_IMG_SZ}" height="{T_IMG_SZ}" rx="5"/></clipPath>')
    svg.append('</defs>')

    # ── 배경 ──
    svg.append(f'<rect width="{W}" height="{int(H)}" fill="{BG}" rx="12"/>')

    # ── 아티스트 섹션 ──
    svg.append(f'<text x="{PAD}" y="{A_IMG_CY - A_R - 14}" font-family="{FONT}" font-size="12" font-weight="600" fill="{T_SEC}" letter-spacing="0.05em">TOP ARTISTS</text>')

    for i, a in enumerate(top_artists):
        cx   = PAD + A_COL_W * i + A_COL_W / 2
        ix   = cx - A_R
        iy   = A_IMG_CY - A_R

        # 배경 원
        svg.append(f'<circle cx="{cx:.1f}" cy="{A_IMG_CY}" r="{A_R}" fill="{BORDER}"/>')

        # 아티스트 이미지
        if a.get('img_b64'):
            svg.append(f'<image href="{a["img_b64"]}" x="{ix:.1f}" y="{iy:.1f}" width="{A_R*2}" height="{A_R*2}" clip-path="url(#ac{i})" preserveAspectRatio="xMidYMid slice"/>')

        # 링 테두리 (1등: 금색)
        ring_c = GOLD if i == 0 else BORDER
        ring_w = 2.5  if i == 0 else 1.5
        svg.append(f'<circle cx="{cx:.1f}" cy="{A_IMG_CY}" r="{A_R}" fill="none" stroke="{ring_c}" stroke-width="{ring_w}"/>')

        # 아티스트 이름
        name   = esc(trunc(a['name'], 14))
        color  = T_PRI if i == 0 else T_SEC
        weight = "600" if i == 0 else "400"
        svg.append(f'<text x="{cx:.1f}" y="{A_NAME_Y}" text-anchor="middle" font-family="{FONT}" font-size="11" font-weight="{weight}" fill="{color}">{name}</text>')

    # ── 구분선 ──
    svg.append(f'<line x1="{PAD}" y1="{DIV_Y}" x2="{W-PAD}" y2="{DIV_Y}" stroke="{BORDER}" stroke-width="1"/>')

    # ── 트랙 섹션 ──
    svg.append(f'<text x="{PAD}" y="{T_LABEL_Y}" font-family="{FONT}" font-size="12" font-weight="600" fill="{T_SEC}" letter-spacing="0.05em">RECENTLY PLAYED</text>')

    # 중앙 세로 구분선
    mid = W / 2
    svg.append(f'<line x1="{mid}" y1="{T_START_Y}" x2="{mid}" y2="{T_START_Y + 5 * T_ROW_H - 8}" stroke="{BORDER}" stroke-width="0.5"/>')

    for i, t in enumerate(recent_tracks):
        row   = i // 2
        col   = i % 2
        bx    = PAD + col * T_COL_W
        by    = T_START_Y + row * T_ROW_H
        img_x = bx + 28
        img_y = by + (T_ROW_H - T_IMG_SZ) / 2
        mid_y = by + T_ROW_H / 2
        tx    = img_x + T_IMG_SZ + 12

        # 트랙 번호
        svg.append(f'<text x="{bx+14:.1f}" y="{mid_y+4:.1f}" text-anchor="middle" font-family="{FONT}" font-size="10" fill="{T_MUT}">{i+1}</text>')

        # 앨범 이미지 배경
        svg.append(f'<rect x="{img_x:.1f}" y="{img_y:.1f}" width="{T_IMG_SZ}" height="{T_IMG_SZ}" rx="5" fill="{BORDER}"/>')

        # 앨범 이미지
        if t.get('album_img_b64'):
            svg.append(f'<image href="{t["album_img_b64"]}" x="{img_x:.1f}" y="{img_y:.1f}" width="{T_IMG_SZ}" height="{T_IMG_SZ}" clip-path="url(#tc{i})" preserveAspectRatio="xMidYMid slice"/>')

        # 곡명
        svg.append(f'<text x="{tx:.1f}" y="{mid_y-5:.1f}" font-family="{FONT}" font-size="12" font-weight="500" fill="{T_PRI}">{esc(trunc(t["name"], 26))}</text>')

        # 아티스트명
        svg.append(f'<text x="{tx:.1f}" y="{mid_y+12:.1f}" font-family="{FONT}" font-size="10" fill="{T_SEC}">{esc(trunc(t["artist"], 28))}</text>')

        # 행 구분선 (마지막 행 제외, 오른쪽 열에서만 그림)
        if row < 4 and col == 1:
            sep_y = by + T_ROW_H
            svg.append(f'<line x1="{PAD}" y1="{sep_y:.1f}" x2="{W-PAD}" y2="{sep_y:.1f}" stroke="{BORDER}" stroke-width="0.5"/>')

    svg.append('</svg>')
    return '\n'.join(svg)


# ──────────────────────────────────────────
# 1단계: 액세스 토큰 갱신
# ──────────────────────────────────────────
auth_str = f"{os.environ['CLIENT_ID']}:{os.environ['CLIENT_SECRET']}"
auth_b64 = b64lib.b64encode(auth_str.encode()).decode()

token_res = requests.post("https://accounts.spotify.com/api/token",
    data={"grant_type": "refresh_token", "refresh_token": os.environ['REFRESH_TOKEN']},
    headers={"Authorization": f"Basic {auth_b64}"})

access_token = token_res.json().get("access_token")
if not access_token:
    raise Exception(f"토큰 발급 실패: {token_res.json()}")

headers = {"Authorization": f"Bearer {access_token}"}

# ──────────────────────────────────────────
# 2단계: Top Artists 가져오기 (중복 없이 5개, 최소 이미지)
# ──────────────────────────────────────────
artist_res = requests.get("https://api.spotify.com/v1/me/top/artists?limit=15&time_range=short_term", headers=headers)
artist_res.raise_for_status()

top_artists = []
seen_artists = set()
for artist in artist_res.json().get('items', []):
    if artist['name'] not in seen_artists:
        seen_artists.add(artist['name'])
        # 가장 작은 이미지 사용 (파일 크기 최소화)
        images = artist.get('images', [])
        img_url = images[-1]['url'] if images else None
        top_artists.append({
            'name': artist['name'],
            'img_b64': fetch_b64(img_url) if img_url else None
        })
    if len(top_artists) == 5:
        break

# ──────────────────────────────────────────
# 3단계: Recently Played 가져오기 (중복 없이 10개, 최소 이미지)
# ──────────────────────────────────────────
recent_res = requests.get("https://api.spotify.com/v1/me/player/recently-played?limit=30", headers=headers)
recent_res.raise_for_status()

recent_tracks = []
seen_tracks = set()
for item in recent_res.json().get('items', []):
    track = item['track']
    if track['id'] not in seen_tracks:
        seen_tracks.add(track['id'])
        images = track['album'].get('images', [])
        album_img_url = images[-1]['url'] if images else None
        recent_tracks.append({
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album_img_b64': fetch_b64(album_img_url) if album_img_url else None,
            'url': track['external_urls']['spotify']
        })
    if len(recent_tracks) == 10:
        break

# ──────────────────────────────────────────
# 4단계: SVG 파일 생성
# ──────────────────────────────────────────
svg_content = generate_svg(top_artists, recent_tracks)
with open("spotify_card.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)
print("✅ spotify_card.svg 생성 완료!")

# ──────────────────────────────────────────
# 5단계: README.md 업데이트
# ──────────────────────────────────────────
with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

if "<!-- Spotify 시작 -->" not in readme:
    raise Exception("README.md에 '<!-- Spotify 시작 -->' 태그가 없습니다!")

new_content = '\n<img src="./spotify_card.svg" width="100%" alt="Spotify Card"/>\n'
readme = re.sub(
    r"(<!-- Spotify 시작 -->).*?(<!-- Spotify 끝 -->)",
    rf"\g<1>{new_content}\g<2>",
    readme, flags=re.DOTALL
)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)
print("✅ README.md 업데이트 완료!")
