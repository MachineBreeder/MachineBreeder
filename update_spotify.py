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

# --- 2단계: Premium 여부 확인 ---
user_res = requests.get("https://api.spotify.com/v1/me", headers=headers)
user_res.raise_for_status()
is_premium = user_res.json().get("product") == "premium"
print(f"✅ 계정 유형: {'Premium' if is_premium else 'Free'}")

# --- 3단계: README.md 읽기 ---
with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

# --- 4단계: Top Tracks 업데이트 (공통) ---
top_res = requests.get("https://api.spotify.com/v1/me/top/tracks?limit=5&time_range=short_term", headers=headers)
top_res.raise_for_status()
top_data = top_res.json()

top_content = "\n#### 🏆 Top Tracks\n"
if 'items' in top_data:
    for track in top_data['items']:
        artist = track['artists'][0]['name']
        top_content += f"- **{track['name']}** - {artist}\n"

if "<!-- Top Tracks 시작 -->" not in readme:
    raise Exception("README.md에 '<!-- Top Tracks 시작 -->' 태그가 없습니다!")

readme = re.sub(
    r"(<!-- Top Tracks 시작 -->).*?(<!-- Top Tracks 끝 -->)",
    rf"\g<1>{top_content}\g<2>",
    readme, flags=re.DOTALL
)

# --- 5단계: Recently Played 업데이트 (Premium만) ---
if is_premium:
    recent_res = requests.get("https://api.spotify.com/v1/me/player/recently-played?limit=5", headers=headers)
    recent_res.raise_for_status()
    recent_data = recent_res.json()

    recent_content = "\n#### 🎵 Recently Played\n"
    if 'items' in recent_data:
        for item in recent_data['items']:
            track = item['track']
            artist = track['artists'][0]['name']
            recent_content += f"- **{track['name']}** - {artist}\n"

    if "<!-- Recently Played 시작 -->" not in readme:
        raise Exception("README.md에 '<!-- Recently Played 시작 -->' 태그가 없습니다!")

    readme = re.sub(
        r"(<!-- Recently Played 시작 -->).*?(<!-- Recently Played 끝 -->)",
        rf"\g<1>{recent_content}\g<2>",
        readme, flags=re.DOTALL
    )
    print("✅ Recently Played 업데이트 완료!")
else:
    print("ℹ️ Free 계정 - Recently Played 유지")

# --- 6단계: README.md 저장 ---
with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)

print("✅ README.md 업데이트 완료!")
