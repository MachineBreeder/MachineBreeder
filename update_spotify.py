import requests, os, base64, re

def esc(text):
    return str(text).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

def trunc(text, n):
    return text[:n-1] + '…' if len(text) > n else text

def generate_html(top_artists, recent_tracks):

    # --- 상단: Top Artists (5등분으로 꽉 채우기) ---
    artist_cells = ''
    for a in top_artists:
        img  = f'<img src="{a["img_url"]}" width="72" height="72"/>' if a.get('img_url') else ''
        name = esc(trunc(a['name'], 12))
        artist_cells += f'<td align="center" width="20%">{img}<br/><sub><b>{name}</b></sub></td>\n'

    artists_html = f'''<b>🎤 Top Artists</b><br/><br/>
<table width="100%">
<tr>
{artist_cells}
</tr>
</table>'''

    # --- 하단: Recently Played 5행 2열 ---
    track_rows = ''
    for i in range(0, 10, 2):
        left  = recent_tracks[i]     if i   < len(recent_tracks) else None
        right = recent_tracks[i + 1] if i+1 < len(recent_tracks) else None

        def track_cell(t, num):
            if not t:
                return '<td width="50%">&nbsp;</td>'
            img  = f'<img src="{t["album_img_url"]}" width="42" height="42"/>' if t.get('album_img_url') else ''
            name = esc(trunc(t['name'], 24))
            art  = esc(trunc(t['artist'], 26))
            return f'''<td valign="middle" width="50%">
<table width="100%"><tr>
<td width="20" align="center"><sub>{num}</sub></td>
<td width="46">{img}</td>
<td><a href="{t["url"]}"><b>{name}</b></a><br/><sub>{art}</sub></td>
</tr></table>
</td>'''

        track_rows += f'<tr>\n{track_cell(left, i+1)}\n{track_cell(right, i+2)}\n</tr>\n'

    recent_html = f'''<b>🎵 Recently Played</b><br/><br/>
<table width="100%" cellspacing="0" cellpadding="6">
{track_rows}
</table>'''

    return f'''{artists_html}

<br/>
<hr/>
<br/>

{recent_html}'''


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

# --- 2단계: Top Artists 가져오기 (중복 없이 5개) ---
artist_res = requests.get("https://api.spotify.com/v1/me/top/artists?limit=15&time_range=short_term", headers=headers)
artist_res.raise_for_status()

top_artists = []
seen_artists = set()
for artist in artist_res.json().get('items', []):
    if artist['name'] not in seen_artists:
        seen_artists.add(artist['name'])
        top_artists.append({
            'name': artist['name'],
            'img_url': artist['images'][0]['url'] if artist.get('images') else None
        })
    if len(top_artists) == 5:
        break

# --- 3단계: Recently Played 가져오기 (중복 없이 10개) ---
recent_res = requests.get("https://api.spotify.com/v1/me/player/recently-played?limit=30", headers=headers)
recent_res.raise_for_status()

recent_tracks = []
seen_tracks = set()
for item in recent_res.json().get('items', []):
    track = item['track']
    if track['id'] not in seen_tracks:
        seen_tracks.add(track['id'])
        recent_tracks.append({
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album_img_url': track['album']['images'][0]['url'] if track['album'].get('images') else None,
            'url': track['external_urls']['spotify']
        })
    if len(recent_tracks) == 10:
        break

# --- 4단계: README.md 업데이트 ---
new_content = f'\n{generate_html(top_artists, recent_tracks)}\n'

with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

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
