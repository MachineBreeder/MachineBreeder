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

# --- 2단계: 최근 들은 곡 가져오기 ---
headers = {"Authorization": f"Bearer {access_token}"}
res = requests.get("https://api.spotify.com/v1/me/player/recently-played?limit=5", headers=headers)
res.raise_for_status()
data = res.json()

# --- 3단계: README에 넣을 내용 만들기 ---
new_content = "### 🎵 Recently Played on Spotify\n"
if 'items' in data:
    for item in data['items']:
        track = item['track']
        artist = track['artists'][0]['name']
        new_content += f"- **{track['name']}** - {artist}\n"

# --- 4단계: README.md 태그 사이 내용 교체 ---
with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

if "<!-- 노래 영역 시작 -->" not in readme:
    raise Exception("README.md에 '<!-- 노래 영역 시작 -->' 태그가 없습니다!")

pattern = r"(<!-- 노래 영역 시작 -->).*?(<!-- 노래 영역 끝 -->)"
replacement = rf"\g<1>\n{new_content}\g<2>"
updated_readme = re.sub(pattern, replacement, readme, flags=re.DOTALL)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(updated_readme)

print("✅ README.md 업데이트 완료!")
