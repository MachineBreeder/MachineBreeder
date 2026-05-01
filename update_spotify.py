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

# --- 3단계: Top Tracks 가져오기 (공통) ---
top_res = requests.get("https://api.spotify.com/v1/me/top/tracks?limit=5&time_range=short_term", headers=headers)
top_res.raise_for_status()
top_data = top_res.json()

top_tracks = []
if 'items' in top_data:
    for track in top_data['items']:
        artist = track['artists'][0]['name']
        top_tracks.append(f"{track['name']} - {artist}")

# --- 4단계: Recently Played 시도 후 Premium 여부 자동 판단 ---
recent_res = requests.get("https://api.spotify.com/v1/me/player/recently-played?limit=5", headers=headers)
is_premium = recent_res.status_code == 200  # ✅ 200이면 Premium, 403이면 Free
print(f"✅ 계정 유형: {'Premium' if is_premium else 'Free'}")

recent_tracks = []
if is_premium:
    recent_data = recent_res.json()
    if 'items' in recent_data:
        for item in recent_data['items']:
            track = item['track']
            artist = track['artists'][0]['name']
            recent_tracks.append(f"{track['name']} - {artist}")

# --- 5단계: 테이블 형식으로 구성 ---
if is_premium:
    max_rows = max(len(top_tracks), len(recent_tracks))

    table = "| 🏆 Top Tracks | 🎵 Recently Played |\n"
    table += "|---|---|\n"
    for i in range(max_rows):
        top = f"**{top_tracks[i]}**" if i < len(top_tracks) else ""
        recent = f"**{recent_tracks[i]}**" if i < len(recent_tracks) else ""
        table += f"| {top} | {recent} |\n"

    new_content = f"\n{table}"

    if "<!-- Top Tracks 시작 -->" not in readme:
        raise Exception("README.md에 '<!-- Top Tracks 시작 -->' 태그가 없습니다!")

    readme = re.sub(
        r"(<!-- Top Tracks 시작 -->).*?(<!-- Recently Played 끝 -->)",
        rf"\g<1>{new_content}\g<2>",
        readme, flags=re.DOTALL
    )
    print("✅ Premium - 테이블 업데이트 완료!")

else:
    table = "| 🏆 Top Tracks |\n"
    table += "|---|\n"
    for track in top_tracks:
        table += f"| **{track}** |\n"

    new_content = f"\n{table}"

    if "<!-- Top Tracks 시작 -->" not in readme:
        raise Exception("README.md에 '<!-- Top Tracks 시작 -->' 태그가 없습니다!")

    readme = re.sub(
        r"(<!-- Top Tracks 시작 -->).*?(<!-- Top Tracks 끝 -->)",
        rf"\g<1>{new_content}\g<2>",
        readme, flags=re.DOTALL
    )
    print("ℹ️ Free 계정 - Top Tracks만 업데이트!")

# --- 6단계: README.md 저장 ---
with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)

print("✅ README.md 업데이트 완료!")
