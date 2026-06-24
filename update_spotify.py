import requests, os, base64, re

# --- 1단계: 액세스 토큰 갱신 ---
auth_str = f"{os.environ['CLIENT_ID']}:{os.environ['CLIENT_SECRET']}"
auth_b64 = base64.b64encode(auth_str.encode()).decode()

token_res = requests.post("https://accounts.spotify.com/api/token",
    data={"grant_type": "refresh_token", "refresh_token": os.environ['REFRESH_TOKEN']},
    headers={"Authorization": f"Basic {auth_b64}"})

access_token = token_res.json().get("access_token")
if not access_token:
    raise Exception(f"토큰 발급 실패: {token_res.json()}")

headers = {"Authorization": f"Bearer {access_token}"}

# --- 2단계: README.md 읽기 ---
with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

# --- 3단계: Top Artists 가져오기 (중복 없이 5개) ---
artist_res = requests.get("https://api.spotify.com/v1/me/top/artists?limit=15&time_range=short_term", headers=headers)
artist_res.raise_for_status()
artist_data = artist_res.json()

top_artists = []
seen_artists = set()
if 'items' in artist_data:
    for artist in artist_data['items']:
        name = artist['name']
        if name not in seen_artists:
            seen_artists.add(name)
            top_artists.append({
                "name": name,
                "img_url": artist['images'][0]['url'] if artist.get('images') else ""
            })
        if len(top_artists) == 5:
            break

# --- 4단계: Recently Played 가져오기 (중복 없이 5개) ---
recent_res = requests.get("https://api.spotify.com/v1/me/player/recently-played?limit=20", headers=headers)
recent_res.raise_for_status()
recent_data = recent_res.json()

recent_tracks = []
seen_tracks = set()
if 'items' in recent_data:
    for item in recent_data['items']:
        track = item['track']
        track_id = track['id']
        if track_id not in seen_tracks:
            seen_tracks.add(track_id)
            recent_tracks.append({
                "name": track['name'],
                "artist": track['artists'][0]['name'],
                "url": track['external_urls']['spotify']
            })
        if len(recent_tracks) == 5:
            break

# --- 5단계: Top Artists 테이블 구성 ---
artist_cells = ""
for artist in top_artists:
    artist_cells += f"""    <td align="center" width="120">
      <img src="{artist['img_url']}" width="80" height="80" style="border-radius:50%;object-fit:cover"/><br/>
      <b>{artist['name']}</b>
    </td>\n"""

top_artists_html = f"""
<h3>🎤 Top Artists</h3>
<table><tr>
{artist_cells}</tr></table>
"""

# --- 6단계: Recently Played 테이블 구성 (앨범 이미지 제거) ---
recent_rows = ""
for track in recent_tracks:
    recent_rows += f'| [**{track["name"]}**]({track["url"]}) | {track["artist"]} |\n'

recently_played_html = f"""
<h3>🎵 Recently Played</h3>

| 곡명 | 아티스트 |
|---|---|
{recent_rows}"""

# --- 7단계: README.md 태그 사이 내용 교체 ---
new_content = f"\n{top_artists_html}\n{recently_played_html}\n"

if "<!-- Spotify 시작 -->" not in readme:
    raise Exception("README.md에 '<!-- Spotify 시작 -->' 태그가 없습니다!")

readme = re.sub(
    r"(<!-- Spotify 시작 -->).*?(<!-- Spotify 끝 -->)",
    rf"\g<1>{new_content}\g<2>",
    readme, flags=re.DOTALL
)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)

print("✅ README.md 업데이트 완료!")
