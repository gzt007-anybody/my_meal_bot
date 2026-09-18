import streamlit as st
import requests
import json
import re
from datetime import datetime
from personal_storage import storage_panel
from storage_model import MAX_RECORDS
from meal_planner import build_plan
from menu_catalog import expanded_menus

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

st.set_page_config(page_title="My Meal Bot 1.0", page_icon="🍽️", layout="wide")

# ---------------------------------------------------------
# Session
# ---------------------------------------------------------
for k, v in {
    "profile": {},
    "recommendations": [],
    "feedback": [],
    "last_context": {},
    "weather": {},
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

storage_panel()

# ---------------------------------------------------------
# 실사용 베타용 메뉴 카탈로그
# nutrition = 1인분 기준의 참고값
# 실제 상용화 전 공신력 영양 DB로 교체/확장 권장
# ---------------------------------------------------------
MENUS = [
    {
        "name":"고등어구이 정식","category":"한식","meal":["점심","저녁"],
        "tags":["담백","생선","집밥","가족","단백질"],"avoid":["생선"],
        "items":[
            ("잡곡밥",140,"밥공기 약 2/3공기",220,47,5,2,5,3),
            ("고등어구이",100,"손바닥 크기 1토막",240,0,24,16,380,0),
            ("나물",80,"작은 반찬그릇 1회분",50,7,3,2,190,3),
            ("두부",80,"일반 두부 약 1/4모",85,3,8,5,120,1),
        ],
        "base_story":"소금에 간한 생선을 불에 구워 먹는 방식은 오래된 일상 식문화입니다. 복잡한 조리 없이도 든든한 한 끼가 되어 집밥의 대표적인 모습으로 자리 잡았습니다.",
        "story_type":"🌿 음식문화 이야기",
    },
    {
        "name":"소고기 버섯전골","category":"한식","meal":["점심","저녁"],
        "tags":["따뜻한","국물","가족","친구","추운날","피곤"],"avoid":[],
        "items":[
            ("소고기",100,"손바닥 크기 1장",215,0,26,12,65,0),
            ("버섯·채소",180,"두 주먹 정도",85,14,6,2,160,6),
            ("전골 육수",180,"국자 약 1.5~2번",60,6,4,2,720,1),
            ("잡곡밥",130,"밥공기 약 2/3공기",205,44,5,2,5,3),
        ],
        "base_story":"전골은 여러 재료를 한 냄비에 모아 함께 익혀 먹는 음식입니다. 한 상에 둘러앉아 같은 냄비를 나눈다는 점 때문에 가족이나 손님이 함께하는 자리와 잘 어울립니다.",
        "story_type":"🌿 음식문화 이야기",
    },
    {
        "name":"닭고기 채소덮밥","category":"한식","meal":["점심","저녁"],
        "tags":["간단","닭고기","혼자","단백질","빠른식사"],"avoid":[],
        "items":[
            ("현미밥",150,"밥공기 약 3/4공기",225,48,5,2,5,3),
            ("닭고기",120,"손바닥 크기 1장 반",198,0,37,4,95,0),
            ("볶은 채소",160,"두 주먹 정도",120,18,5,4,320,6),
        ],
        "base_story":"밥 위에 반찬을 얹어 한 그릇으로 먹는 방식은 시간과 공간을 아끼는 실용적인 식사와 잘 맞습니다. 바쁜 날에도 밥·단백질·채소를 한 번에 챙길 수 있습니다.",
        "story_type":"🌿 음식문화 이야기",
    },
    {
        "name":"두부 버섯 비빔밥","category":"한식","meal":["아침","점심","저녁"],
        "tags":["채소","담백","혼자","가벼운","균형"],"avoid":["대두"],
        "items":[
            ("잡곡밥",130,"밥공기 약 2/3공기",205,44,5,2,5,3),
            ("두부",100,"일반 두부 약 1/3모",95,3,10,5,15,1),
            ("나물·버섯",180,"두 주먹 정도",110,20,6,3,280,7),
            ("양념장",20,"밥숟가락 약 1큰술",45,7,1,1,390,0),
        ],
        "base_story":"비빔밥은 서로 다른 재료를 한 그릇 안에서 섞어 새로운 맛을 만드는 음식입니다. 여러 재료가 조화를 이룬다는 점 때문에 ‘한 그릇 속의 조화’로 자주 이야기됩니다.",
        "story_type":"🌿 음식문화 이야기",
    },
    {
        "name":"에그 치킨 샌드위치","category":"양식","meal":["아침","점심","오후"],
        "tags":["샌드위치","간단","베이커리","혼자","빠른식사"],"avoid":["계란","밀","우유"],
        "items":[
            ("통밀빵",90,"식빵 약 2장",230,42,9,3,330,6),
            ("계란",50,"중간 크기 1개",72,0,6,5,70,0),
            ("닭고기",70,"손바닥의 약 2/3",116,0,22,2,55,0),
            ("채소",80,"한 주먹 정도",35,7,2,0,45,3),
        ],
        "base_story":"‘샌드위치’라는 이름은 18세기 영국의 샌드위치 백작과 관련된 유명한 일화로 널리 알려져 있습니다. 빵 사이에 음식을 넣어 손쉽게 먹는 방식은 오늘날 간편식의 상징이 되었습니다.",
        "story_type":"📜 역사 일화",
    },
    {
        "name":"연어 샐러드와 고구마","category":"양식","meal":["점심","저녁"],
        "tags":["생선","가벼운","채소","단백질","상쾌한"],"avoid":["생선"],
        "items":[
            ("연어",100,"손바닥 크기 1조각",208,0,20,13,60,0),
            ("샐러드 채소",180,"두 주먹 정도",75,14,5,1,120,7),
            ("고구마",150,"중간 크기 1개",195,45,3,0,60,5),
            ("드레싱",20,"밥숟가락 약 1큰술",70,5,0,6,190,0),
        ],
        "base_story":"연어는 북쪽 바다와 강을 오가는 생선으로 여러 지역에서 오래전부터 중요한 식재료였습니다. 오늘날에는 신선한 채소와 함께 가볍게 즐기는 조합으로도 널리 사랑받습니다.",
        "story_type":"🌿 음식문화 이야기",
    },
    {
        "name":"닭가슴살 메밀국수","category":"한식","meal":["점심","저녁"],
        "tags":["시원한","면","더운날","가벼운","단백질"],"avoid":["밀"],
        "items":[
            ("메밀면",180,"보통 면그릇 약 1그릇",260,52,9,2,280,4),
            ("닭가슴살",100,"손바닥 크기 1장",165,0,31,4,75,0),
            ("채소",120,"한 주먹 반",50,10,3,0,90,4),
            ("양념",30,"밥숟가락 약 2큰술",70,12,1,2,520,1),
        ],
        "base_story":"메밀은 산지가 척박한 지역에서도 비교적 잘 자라 여러 지역의 구황·일상 식재료로 쓰였습니다. 차갑게 먹는 메밀국수는 더운 날 입맛을 돋우는 음식으로 사랑받아 왔습니다.",
        "story_type":"🌿 음식문화 이야기",
    },
    {
        "name":"된장찌개와 보리밥","category":"한식","meal":["아침","점심","저녁"],
        "tags":["따뜻한","국물","집밥","담백","편안한"],"avoid":["대두"],
        "items":[
            ("보리밥",140,"밥공기 약 2/3공기",210,45,5,2,5,5),
            ("된장찌개",250,"국그릇 약 1그릇",170,16,12,7,900,5),
            ("채소반찬",100,"작은 반찬 2가지",80,12,4,2,300,4),
        ],
        "base_story":"장은 오래 보관하기 어려운 콩을 발효시켜 맛과 저장성을 높인 생활의 지혜였습니다. 된장찌개는 그 장맛을 중심으로 계절 채소를 더해 끓이는 친숙한 집밥입니다.",
        "story_type":"🌿 음식문화 이야기",
    },
    {
        "name":"소고기 미역국 정식","category":"한식","meal":["아침","점심","저녁"],
        "tags":["따뜻한","국물","생일","축하","가족","편안한"],"avoid":[],
        "items":[
            ("소고기 미역국",250,"국그릇 약 1그릇",180,8,18,9,720,3),
            ("잡곡밥",130,"밥공기 약 2/3공기",205,44,5,2,5,3),
            ("나물",100,"작은 반찬 2가지",80,12,4,2,260,4),
        ],
        "base_story":"한국에서는 출산 후 미역국을 먹는 전통과 연결되어 생일에도 미역국을 먹는 문화가 자리 잡았습니다. 그래서 미역국은 단순한 국을 넘어 ‘태어난 날을 기억하는 음식’이라는 특별한 의미를 갖습니다.",
        "story_type":"🌿 음식문화 이야기",
    },
    {
        "name":"닭죽","category":"한식","meal":["아침","점심","저녁","야식"],
        "tags":["부드러운","따뜻한","피곤","편안한","간단"],"avoid":[],
        "items":[
            ("쌀죽",250,"죽그릇 약 1그릇",220,42,5,3,220,1),
            ("닭고기",80,"손바닥의 약 2/3",132,0,25,3,65,0),
            ("채소",80,"한 주먹",40,8,2,0,90,3),
        ],
        "base_story":"죽은 곡물을 물에 오래 끓여 부드럽게 만든 음식이라 식재료가 부족하거나 몸이 지쳤을 때도 먹기 쉬웠습니다. 여러 문화권에서 회복식과 편안한 음식으로 등장하는 이유가 여기에 있습니다.",
        "story_type":"🌿 음식문화 이야기",
    },
    {
        "name":"불고기 쌈밥","category":"한식","meal":["점심","저녁"],
        "tags":["고기","가족","친구","축하","푸짐한"],"avoid":[],
        "items":[
            ("불고기",120,"손바닥 크기 1장 반",280,14,28,13,650,1),
            ("쌈채소",120,"두 주먹 정도",45,8,3,0,40,4),
            ("잡곡밥",130,"밥공기 약 2/3공기",205,44,5,2,5,3),
            ("쌈장",15,"티스푼 약 2~3번",35,5,2,1,330,1),
        ],
        "base_story":"얇게 썬 고기를 양념해 굽는 음식은 특별한 날 사람들과 함께 나누기 좋은 형태입니다. 쌈채소에 밥과 고기를 함께 싸 먹으면 한입 안에 여러 맛과 식감이 모입니다.",
        "story_type":"🌿 음식문화 이야기",
    },
    {
        "name":"토마토 치킨 파스타","category":"양식","meal":["점심","저녁"],
        "tags":["면","친구","연인","외식","기분좋은"],"avoid":["밀"],
        "items":[
            ("파스타면",180,"보통 접시 1인분",300,60,11,2,20,4),
            ("닭고기",100,"손바닥 크기 1장",165,0,31,4,75,0),
            ("토마토소스",150,"국자 약 1.5번",120,20,4,3,520,4),
            ("채소",100,"한 주먹",50,10,3,0,80,3),
        ],
        "base_story":"파스타는 지역과 시대에 따라 다양한 형태로 발전했고, 토마토가 유럽 요리에 널리 쓰이면서 오늘날 익숙한 붉은 소스 파스타가 자리 잡았습니다. 한 접시에 면과 소스가 어우러지는 대표적인 공유·외식 메뉴입니다.",
        "story_type":"🌿 음식문화 이야기",
    },
]

_existing_names = {m['name'] for m in MENUS}
MENUS.extend(m for m in expanded_menus() if m['name'] not in _existing_names)

CITIES = {
    "서울": (37.5665, 126.9780),
    "부산": (35.1796, 129.0756),
    "대구": (35.8714, 128.6014),
    "인천": (37.4563, 126.7052),
    "광주": (35.1595, 126.8526),
    "대전": (36.3504, 127.3845),
    "울산": (35.5384, 129.3114),
    "창원": (35.2280, 128.6811),
    "제주": (33.4996, 126.5312),
}

def menu_total(menu):
    if not menu.get('items'):
        return [None] * 6
    vals = [0] * 6
    for _, _, _, kcal, carb, protein, fat, sodium, fiber in menu["items"]:
        for i, x in enumerate([kcal, carb, protein, fat, sodium, fiber]):
            vals[i] += x
    return vals

def current_weather(city):
    lat, lon = CITIES[city]
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,apparent_temperature,precipitation,rain,weather_code",
            "timezone": "Asia/Seoul",
        }
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        cur = r.json().get("current", {})
        t = float(cur.get("temperature_2m", 0))
        feel = float(cur.get("apparent_temperature", t))
        rain = float(cur.get("rain", 0))
        precip = float(cur.get("precipitation", 0))
        if rain > 0 or precip > 0:
            feel_text = "비가 와요"
        elif feel >= 27:
            feel_text = "더워요"
        elif feel <= 12:
            feel_text = "추워요"
        else:
            feel_text = "보통이에요"
        return {"ok": True, "temp": t, "feel": feel, "summary": feel_text}
    except Exception:
        return {"ok": False, "temp": None, "feel": None, "summary": "보통이에요"}

def hard_filtered(profile):
    allergies = profile.get("allergies", [])
    result = []
    for menu in MENUS:
        if any(a in menu["avoid"] for a in allergies):
            continue
        result.append(menu)
    return result

def local_score(menu, profile, context):
    s = 0
    if context["meal_time"] in menu["meal"]:
        s += 4
    if menu["category"] in profile.get("cuisines", []):
        s += 3
    likes = profile.get("likes", "").lower()
    dislikes = profile.get("dislikes", "").lower()
    for tag in menu["tags"]:
        if tag.lower() in likes:
            s += 3
        if tag.lower() in dislikes:
            s -= 7
    if context["companion"] in menu["tags"]:
        s += 2
    w = context.get("weather_summary", "")
    if w in ["추워요", "비가 와요"] and ("따뜻한" in menu["tags"] or "국물" in menu["tags"]):
        s += 3
    if w == "더워요" and ("시원한" in menu["tags"] or "가벼운" in menu["tags"]):
        s += 3
    if context["mood"] in ["피곤해요", "스트레스 받아요"] and ("편안한" in menu["tags"] or "따뜻한" in menu["tags"]):
        s += 2
    kcal, carb, protein, fat, sodium, fiber = menu_total(menu)
    health = profile.get("health", [])
    if "고혈압" in health and sodium is not None and sodium > 1200:
        s -= 5
    if "당뇨" in health and carb is not None and carb > 80:
        s -= 4
    if profile.get("goal") == "체중 줄이기" and kcal is not None and kcal > 700:
        s -= 4
    if protein is not None and protein >= 25:
        s += 2
    if fiber is not None and fiber >= 5:
        s += 1
    return s

def extract_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            return json.loads(m.group(0))
        raise

def ai_recommend(profile, context):
    try:
        api_key = st.secrets.get("OPENAI_API_KEY", "")
    except FileNotFoundError:
        api_key = ""
    if OpenAI is None or not api_key:
        return None, "OPENAI_API_KEY가 없어 기본 추천 엔진으로 실행했습니다."

    candidates = hard_filtered(profile)
    if context.get('planned_names'):
        candidates = [m for m in candidates if m['name'] in context['planned_names']]
    if not candidates:
        return [], "알레르기 조건 때문에 추천 가능한 메뉴가 없습니다."

    catalog = []
    for m in candidates:
        kcal, carb, protein, fat, sodium, fiber = menu_total(m)
        catalog.append({
            "name": m["name"],
            "category": m["category"],
            "meal": m["meal"],
            "tags": m["tags"],
            "nutrition": {
                "kcal": kcal, "carb_g": carb, "protein_g": protein,
                "fat_g": fat, "sodium_mg": sodium, "fiber_g": fiber
            },
            "story_seed": m["base_story"],
            "story_type": m["story_type"],
        })

    prompt = {
        "user_profile": profile,
        "today_context": context,
        "candidate_menus": catalog,
        "task": (
            "후보 메뉴 중 정확히 3개를 골라 순위를 매겨라. "
            "알레르기/건강 제한을 최우선으로 하고, 그 다음 취향·기분·날씨·동행·상황을 반영한다. "
            "각 메뉴에는 왜 오늘 어울리는지 2~3문장으로 설명하고, 음식과 관련된 짧고 재미있는 이야기를 작성한다. "
            "역사적 사실이 확실하지 않으면 역사 사실처럼 단정하지 말고 story_type을 '✨ 오늘을 위한 창작 이야기'로 표시한다. "
            "후보에 없는 메뉴는 절대 만들지 않는다."
        ),
        "output_format": {
            "recommendations": [
                {"name":"후보 메뉴명과 정확히 일치","reason":"문장","story_type":"문장","story":"3~5문장"}
            ]
        }
    }

    model = st.secrets.get("OPENAI_MODEL", "gpt-5.6-luna")
    client = OpenAI(api_key=api_key)
    try:
        response = client.responses.create(
            model=model,
            instructions=(
                "너는 한국어 개인 음식 추천 도우미다. 의료 진단을 하지 않는다. "
                "사용자 알레르기와 건강 참고사항을 존중한다. "
                "역사 이야기를 지어내서 사실처럼 말하지 않는다. 출력은 JSON만 반환한다."
            ),
            input=json.dumps(prompt, ensure_ascii=False),
        )
        data = extract_json(response.output_text)
        recs = data.get("recommendations", [])
        valid_names = {m["name"] for m in candidates}
        clean = []
        for r in recs:
            if isinstance(r, dict) and r.get("name") in valid_names and r.get('name') not in {x['name'] for x in clean}:
                clean.append({
                    "name": r["name"],
                    "reason": r.get("reason", ""),
                    "story": r.get("story", ""),
                    "story_type": r.get("story_type", "🌿 음식문화 이야기"),
                })
        if len(clean) >= 3:
            return clean[:3], f"AI 추천 엔진: {model}"
        return None, "AI 응답 형식이 불완전해 기본 추천으로 전환했습니다."
    except Exception as e:
        return None, f"AI 연결 실패로 기본 추천으로 전환했습니다: {type(e).__name__}"

def get_menu(name):
    for m in MENUS:
        if m["name"] == name:
            return m
    return None

# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.markdown("## 🍽️ My Meal Bot 1.0")
st.caption("내 건강·취향·날씨·기분·상황을 함께 생각하는 개인 음식 추천")
st.info("1.0은 실사용 베타입니다. 영양 수치는 참고용이며 의료 진단·치료를 대신하지 않습니다.")
st.caption(f'등록 메뉴 {len(MENUS)}종 · 현재 추천은 기본 엔진으로 실행하며 OpenAI API를 호출하지 않습니다.')
st.caption('새 메뉴는 일반적인 음식 아이디어이며 표준 레시피가 아닙니다. 알레르기 표시는 보수적인 참고 필터로, 실제 재료·소스·교차접촉 여부를 보장하지 않습니다. 섭취 전 반드시 확인하세요.')
with st.expander('📚 전체 메뉴 찾아보기'):
    catalog_category = st.selectbox('메뉴 분류', ['전체'] + sorted({m['category'] for m in MENUS}))
    catalog_query = st.text_input('메뉴명 검색', placeholder='예: 국수, 샌드위치, 닭')
    visible_menus = [m for m in MENUS if (catalog_category == '전체' or m['category'] == catalog_category) and catalog_query.strip() in m['name']]
    st.caption(f'{len(visible_menus)}종 표시 · 이 검색은 목록 조회용이며 추천 조건은 내 정보에서 설정합니다.')
    st.dataframe([{'메뉴':m['name'],'종류':m['category'],'식사 시간':', '.join(m['meal'])} for m in visible_menus], hide_index=True, use_container_width=True)

tab_today, tab_profile, tab_record = st.tabs(["✨ 오늘 추천", "👤 내 정보", "📊 기록"])

# ---------------------------------------------------------
# Today
# ---------------------------------------------------------
with tab_today:
    if not st.session_state.profile:
        st.warning("처음 한 번만 '내 정보'에서 프로필을 저장해주세요.")
    else:
        p = st.session_state.profile
        st.markdown(f"### {p.get('nickname') or '사용자'}님, 오늘 뭐 드실까요?")

        with st.form("recommend_form"):
            c1, c2 = st.columns(2)
            with c1:
                meal_time = st.selectbox("식사 시간", ["아침","점심","오후","저녁","야식"])
                companion = st.selectbox("누구와", ["혼자","가족","연인","친구","직장동료"])
                city = st.selectbox("현재 지역", list(CITIES.keys()), index=1)
            with c2:
                mood = st.selectbox("기분", ["기분 좋아요","그냥 그래요","조금 우울해요","스트레스 받아요","피곤해요","축하할 일이 있어요","편안해요"])
                dining = st.selectbox("식사 방식", ["상관없음","집에서 요리","외식","배달","간단하게"])
                story_style = st.selectbox("이야기 분위기", ["재미있는 역사·문화 이야기","따뜻한 감성","짧고 실용적","우화처럼"])

            with st.expander("＋ 상세 조건"):
                d1, d2 = st.columns(2)
                with d1:
                    budget = st.selectbox("예산", ["상관없음","10,000원 이하","10,000~20,000원","20,000~30,000원"])
                    amount_view = st.radio("섭취량 표시", ["g + 생활계량","g만 보기","생활계량만 보기"])
                with d2:
                    scope = st.radio("추천 범위", ["지금 한 끼","오늘 3끼","일주일"])
                    special = st.text_area("오늘 특별한 일", placeholder="예: 일이 잘 끝났어요, 가족과 오랜만에 만나요")

            st.caption('지금 한 끼: 최대 3개 후보 · 오늘 3끼: 아침/점심/저녁 · 일주일: 7일 × 3끼. 다시 누르면 가능한 대체 메뉴를 우선합니다.')
            go = st.form_submit_button("✨ 선택한 범위로 추천 / 다시 추천", type="primary", use_container_width=True)

        if go:
            with st.spinner("오늘 상황과 날씨를 함께 살펴보고 있어요..."):
                weather = current_weather(city)
                st.session_state.weather = weather
                ctx = {
                    "meal_time": meal_time, "companion": companion, "mood": mood,
                    "dining": dining, "city": city, "budget": budget,
                    "amount_view": amount_view, "scope": scope, "special": special,
                    "story_style": story_style,
                    "weather_summary": weather["summary"],
                    "temperature_c": weather.get("temp"),
                    "feels_like_c": weather.get("feel"),
                }

                previous = st.session_state.recommendations if st.session_state.last_context.get('scope') == scope else []
                ctx['shown_names'] = st.session_state.get('shown_menu_names', [])
                ai_result = build_plan(p, ctx, hard_filtered(p), local_score, previous, st.session_state.feedback)
                st.session_state.shown_menu_names = (ctx['shown_names'] + [r['name'] for r in ai_result if r['name']])[-200:]
                status = '기본 식단 엔진: 식사 시간별 구성과 메뉴 반복을 조절했습니다.'
                # style tuning (non-AI fallback and final display)
                if story_style == "짧고 실용적":
                    for r in ai_result:
                        sentences = re.split(r"(?<=[.!?])\s+", r["story"].strip())
                        r["story"] = sentences[0] if sentences else r["story"]
                elif story_style == "따뜻한 감성":
                    for r in ai_result:
                        if "오늘" not in r["story"]:
                            r["story"] += " 오늘의 한 끼가 잠시 쉬어가는 따뜻한 시간이 되면 좋겠습니다."
                elif story_style == "우화처럼":
                    for r in ai_result:
                        if not r["story_type"].startswith("✨"):
                            r["story_type"] = "✨ 오늘을 위한 창작 이야기"
                            r["story"] = "옛날 어느 작은 마을의 식탁에 이 음식이 올랐다고 상상해볼까요? " + r["story"]

                st.session_state.recommendations = ai_result
                st.session_state.last_context = ctx
                st.session_state.engine_status = status
                st.rerun()

        if st.session_state.recommendations:
            w = st.session_state.weather
            if w.get("ok"):
                st.caption(f"🌤️ {st.session_state.last_context['city']} 현재 약 {w['temp']:.1f}℃ · 체감 {w['feel']:.1f}℃ · {w['summary']}")
            else:
                st.caption("🌤️ 실시간 날씨를 불러오지 못해 기본 날씨 조건으로 추천했습니다.")

            st.caption(st.session_state.get("engine_status", ""))
            result_scope = st.session_state.last_context.get('scope','지금 한 끼')
            single_result = result_scope == '지금 한 끼'
            st.markdown('### ' + ('지금 한 끼 후보' if single_result else '오늘 아침·점심·저녁 식단' if result_scope == '오늘 3끼' else '7일 식단 · 하루 3끼'))
            if not single_result:
                st.table([{'식사':r.get('slot',''), '메뉴':r['name'] or '추천 가능한 메뉴 없음'} for r in st.session_state.recommendations])
                st.caption(f'등록 메뉴 {len(MENUS)}종에서 가능한 한 반복 없이 구성합니다. 제외 조건으로 후보가 적으면 반복될 수 있습니다. 날씨는 현재 날씨를 참고합니다.')
            elif len(st.session_state.recommendations) < 3:
                st.caption('선택한 식사 시간과 제외 조건에 맞는 메뉴만 표시합니다. 후보가 적으면 다시 추천해도 같을 수 있습니다.')

            view_mode = st.session_state.last_context.get("amount_view", "g + 생활계량")

            for i, r in enumerate(st.session_state.recommendations, 1):
                menu = get_menu(r["name"])
                if not menu:
                    st.warning(f"{r.get('slot','')}: {r.get('reason','추천 가능한 메뉴가 없습니다.')}")
                    continue
                kcal, carb, protein, fat, sodium, fiber = menu_total(menu)
                medal = ["🥇","🥈","🥉"][i-1] if single_result else r.get('slot',str(i))

                with st.container(border=True):
                    st.markdown(f"### {medal} {menu['name']}")
                    st.write(r["reason"])

                    special = st.session_state.last_context.get("special","").strip()
                    if special:
                        st.caption(f"오늘의 상황: {special}")

                    with st.expander("📖 오늘의 음식 이야기", expanded=single_result):
                        st.caption(r["story_type"])
                        st.write(r["story"])
                        if r["story_type"].startswith("✨"):
                            st.caption("※ 실제 역사 기록이 아닌 창작·감성 이야기입니다.")

                    if not menu['items']:
                        st.caption('분량·영양정보 미등록 · 실제 레시피와 1인분 구성을 확인하세요.')
                        st.caption('영양 수치가 없어 건강 조건에 따른 수치 비교에는 사용하지 않습니다.')
                    else:
                        st.markdown("**1인 기준 양**")
                        for name, grams, measure, *_ in menu["items"]:
                            if view_mode == "g만 보기":
                                st.write(f"• {name}: {grams}g")
                            elif view_mode == "생활계량만 보기":
                                st.write(f"• {name}: {measure}")
                            else:
                                st.write(f"• {name}: {grams}g · {measure}")

                        with st.expander("영양정보 자세히 보기"):
                            n1,n2,n3,n4 = st.columns(4)
                            n1.metric("열량", f"{kcal:.0f} kcal")
                            n2.metric("탄수화물", f"{carb:.0f}g")
                            n3.metric("단백질", f"{protein:.0f}g")
                            n4.metric("지방", f"{fat:.0f}g")
                            st.caption(f"나트륨 약 {sodium:.0f}mg · 식이섬유 약 {fiber:.0f}g")
                            if "고혈압" in p.get("health",[]) and sodium > 1000:
                                st.warning("나트륨이 높은 편일 수 있습니다. 국물·양념의 양을 줄여 드시는 편이 좋습니다.")

                    b1,b2,b3,b4 = st.columns(4)
                    for col,label,action in [
                        (b1,"👍 좋아요","좋아요"),
                        (b2,"👎 별로예요","별로예요"),
                        (b3,"🍴 먹었어요","먹었어요"),
                        (b4,"💾 저장","저장"),
                    ]:
                        if col.button(label, key=f"{action}_{i}"):
                            if len(st.session_state.feedback) >= MAX_RECORDS:
                                st.warning('기록이 3,000개입니다. 백업 후 오래된 기록을 삭제하세요.')
                                st.stop()
                            st.session_state.feedback.append({
                                "time": datetime.now().isoformat(),
                                "menu": menu["name"],
                                "action": action,
                                "category": menu["category"],
                                "meal_time": r.get('meal_time',st.session_state.last_context.get("meal_time", "")),
                                "kcal": kcal,
                                "protein": protein,
                                "sodium": sodium,
                            })
                            st.toast(f"{action} 기록 완료")
                            st.rerun()

        elif st.session_state.last_context:
            st.warning('현재 제외 조건과 식사 시간에 맞는 메뉴가 없습니다. 등록된 메뉴가 늘어나야 추천할 수 있습니다.')

# ---------------------------------------------------------
# Profile
# ---------------------------------------------------------
with tab_profile:
    st.markdown("### 내 정보")
    st.caption("저장된 조건은 추천 때 자동으로 반영됩니다.")

    with st.form(f"profile_form_{st.session_state.get('_profile_epoch', 0)}"):
        c1,c2 = st.columns(2)
        with c1:
            nickname = st.text_input("닉네임", value=st.session_state.profile.get("nickname",""))
            age = st.number_input("나이", 18, 100, int(st.session_state.profile.get("age",45)))
            height = st.number_input("키(cm)", 120.0, 220.0, float(st.session_state.profile.get("height",170.0)), 0.5)
        with c2:
            sex_opts = ["선택 안 함","남성","여성"]
            current_sex = st.session_state.profile.get("sex","선택 안 함")
            sex = st.selectbox("성별", sex_opts, index=sex_opts.index(current_sex) if current_sex in sex_opts else 0)
            weight = st.number_input("몸무게(kg)", 30.0, 200.0, float(st.session_state.profile.get("weight",65.0)), 0.5)
            goal_opts = ["건강하게 유지","체중 줄이기","체중 늘리기","근육 관리","영양 균형","특별한 목표 없음"]
            current_goal = st.session_state.profile.get("goal","건강하게 유지")
            goal = st.selectbox("목표", goal_opts, index=goal_opts.index(current_goal) if current_goal in goal_opts else 0)

        with st.expander("건강·알레르기"):
            health_opts = ["고혈압","당뇨","고지혈증","통풍","신장질환","위장관리가 필요함"]
            health = st.multiselect("건강 참고사항", health_opts, default=st.session_state.profile.get("health",[]))
            extra_health = st.text_input("기타 건강 참고사항", value=st.session_state.profile.get("extra_health",""), placeholder="직접 입력")

            allergy_opts = ["계란","우유","땅콩","견과류","밀","갑각류","생선","대두"]
            allergies = st.multiselect("알레르기 / 제외 식품", allergy_opts, default=st.session_state.profile.get("allergies",[]))
            extra_allergy = st.text_input("기타 알레르기 또는 피해야 할 음식", value=st.session_state.profile.get("extra_allergy",""), placeholder="직접 입력")

        with st.expander("음식 취향"):
            cuisine_opts = ["한식","일식","중식","양식","분식","베이커리","디저트","기타"]
            cuisines = st.multiselect("선호 음식 종류", cuisine_opts, default=st.session_state.profile.get("cuisines",["한식"]))
            extra_cuisine = st.text_input("기타 선호 음식 종류", value=st.session_state.profile.get("extra_cuisine",""), placeholder="예: 동남아 음식, 지중해식")
            likes = st.text_area("좋아하는 음식", value=st.session_state.profile.get("likes",""), placeholder="예: 고등어, 버섯, 국물요리")
            dislikes = st.text_area("싫어하는 음식", value=st.session_state.profile.get("dislikes",""), placeholder="예: 가지, 굴, 매우 매운 음식")

        save = st.form_submit_button("💾 내 정보 저장", type="primary", use_container_width=True)

    if save:
        st.session_state.profile = {
            "nickname": nickname, "age": age, "sex": sex, "height": height, "weight": weight,
            "goal": goal, "health": health, "extra_health": extra_health,
            "allergies": allergies, "extra_allergy": extra_allergy,
            "cuisines": cuisines, "extra_cuisine": extra_cuisine,
            "likes": likes, "dislikes": dislikes,
        }
        st.session_state.profile_saved_notice = True
        st.rerun()

    if st.session_state.pop("profile_saved_notice", False):
        st.success("내 정보를 적용했습니다. '오늘 추천'에서 바로 사용할 수 있습니다. 기기 보관 상태는 위 저장 메뉴에서 확인하세요.")

    if st.session_state.profile:
        p = st.session_state.profile
        bmi = p["weight"] / ((p["height"]/100)**2)
        st.info(f"{p.get('nickname') or '사용자'} · BMI 참고값 {bmi:.1f} · 목표: {p['goal']}")

# ---------------------------------------------------------
# Records
# ---------------------------------------------------------
with tab_record:
    st.markdown("### 내 기록")
    ate = [x for x in st.session_state.feedback if x["action"] == "먹었어요"]
    if ate:
        a,b,c,d = st.columns(4)
        a.metric("먹었어요", f"{len(ate)}회")
        for column, key, label, unit in [(b,'kcal','평균 열량','kcal'),(c,'protein','평균 단백질','g'),(d,'sodium','평균 나트륨','mg')]:
            known = [x[key] for x in ate if x.get(key) is not None]
            column.metric(label, f"{sum(known)/len(known):.0f} {unit}" if known else '정보 없음')
        st.caption('평균은 영양 수치가 등록된 기록만 계산합니다. 미등록 메뉴를 0으로 계산하지 않습니다.')

    if st.session_state.feedback:
        st.markdown("**최근 기록**")
        for index in reversed(range(max(0, len(st.session_state.feedback)-20), len(st.session_state.feedback))):
            x = st.session_state.feedback[index]
            left, right = st.columns([5,1])
            left.write(f"• {x['time'][:16].replace('T',' ')} · {x['menu']} · {x.get('category','')} · {x['action']}")
            if right.button('삭제', key=f'delete_record_{index}'):
                st.session_state.feedback.pop(index)
                st.rerun()
        if st.checkbox('모든 음식 기록을 삭제하겠습니다'):
            if st.button('음식 기록 전체 삭제'):
                st.session_state.feedback = []
                st.rerun()
    else:
        st.info("아직 기록이 없습니다.")

    st.caption("상단의 '내 기기 저장 · 백업'에서 기기 보관과 파일 백업을 관리하세요. 브라우저 데이터 삭제 또는 다른 기기 사용 시 백업으로 복원할 수 있습니다.")

st.divider()
st.caption("My Meal Bot · 확장 메뉴 기본 추천 · 개인 기록 · 실사용 베타")
