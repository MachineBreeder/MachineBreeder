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

# --- 3단계: Top Artists 가져오기 ---
artist_res = requests.get("https://api.spotify.com/v1/me/top/artists?limit=5&time_range=short_term", headers=headers)
artist_res.raise_for_status()
artist_data = artist_res.json()

top_artists = []
if 'items' in artist_data:
    for artist in artist_data['items']:
        top_artists.append(artist['name'])

# --- 4단계: Recently Played 가져오기 ---
recent_res = requests.get("https://api.spotify.com/v1/me/player/recently-played?limit=5", headers=headers)
recent_res.raise_for_status()
recent_data = recent_res.json()

recent_tracks = []
if 'items' in recent_data:
    for item in recent_data['items']:
        track = item['track']
        artist = track['artists'][0]['name']
        recent_tracks.append(f"{track['name']} - {artist}")

# --- 5단계: 테이블 형식으로 구성 ---
max_rows = max(len(top_artists), len(recent_tracks))

table = "| 🎤 Top Artists | 🎵 Recently Played |\n"
table += "|---|---|\n"
for i in range(max_rows):
    artist = f"**{top_artists[i]}**" if i < len(top_artists) else ""
    recent = f"**{recent_tracks[i]}**" if i < len(recent_tracks) else ""
    table += f"| {artist} | {recent} |\n"

new_content = f"\n{table}"

# --- 6단계: README.md 태그 사이 내용 교체 ---
if "<!-- Top Artists 시작 -->" not in readme:
    raise Exception("README.md에 '<!-- Top Artists 시작 -->' 태그가 없습니다!")

readme = re.sub(
    r"(<!-- Top Artists 시작 -->).*?(<!-- Recently Played 끝 -->)",
    rf"\g<1>{new_content}\g<2>",
    readme, flags=re.DOTALL
)

# --- 7단계: README.md 저장 ---
with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)

print("✅ README.md 업데이트 완료!")