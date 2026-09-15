import streamlit as st
from datetime import datetime

st.set_page_config(page_title="My Meal Bot", page_icon="🍽️", layout="wide")

# -----------------------------
# Session state
# -----------------------------
for k, v in {
    "profile": {},
    "recommendations": [],
    "feedback": [],
    "last_context": {},
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -----------------------------
# Prototype menu DB
# nutrient values are example-only for MVP
# tuple: name, grams, household_measure, kcal, carb, protein, fat, sodium, fiber
# -----------------------------
MENUS = [
    {
        "name": "고등어구이 정식",
        "category": "한식",
        "meal": ["점심", "저녁"],
        "tags": ["생선", "담백", "가족", "집밥"],
        "avoid": ["생선"],
        "items": [
            ("잡곡밥", 140, "밥공기 약 2/3공기", 220, 47, 5, 2, 5, 3),
            ("고등어구이", 100, "손바닥 크기 1토막 정도", 240, 0, 24, 16, 380, 0),
            ("시금치나물", 70, "작은 반찬그릇 1회분", 45, 5, 3, 2, 180, 3),
            ("두부구이", 80, "일반 두부 약 1/4모", 85, 3, 8, 5, 120, 1),
        ],
        "why": "단백질과 생선을 함께 챙기기 좋은 균형형 한식입니다."
    },
    {
        "name": "소고기 버섯전골",
        "category": "한식",
        "meal": ["점심", "저녁"],
        "tags": ["따뜻한", "국물", "가족", "추운날", "피곤"],
        "avoid": [],
        "items": [
            ("소고기", 100, "손바닥 크기 1장 정도", 215, 0, 26, 12, 65, 0),
            ("버섯·채소", 180, "두 주먹 정도", 85, 14, 6, 2, 160, 6),
            ("전골 육수", 180, "국자 약 1.5~2번", 60, 6, 4, 2, 720, 1),
            ("잡곡밥", 130, "밥공기 약 2/3공기", 205, 44, 5, 2, 5, 3),
        ],
        "why": "따뜻한 국물과 단백질·채소를 함께 먹기 좋은 메뉴입니다."
    },
    {
        "name": "닭고기 채소덮밥",
        "category": "한식",
        "meal": ["점심", "저녁"],
        "tags": ["간단", "닭고기", "혼자", "단백질"],
        "avoid": [],
        "items": [
            ("현미밥", 150, "밥공기 약 3/4공기", 225, 48, 5, 2, 5, 3),
            ("닭고기", 120, "손바닥 크기 1장 반 정도", 198, 0, 37, 4, 95, 0),
            ("볶은 채소", 160, "두 주먹 정도", 120, 18, 5, 4, 320, 6),
        ],
        "why": "한 그릇으로 먹기 편하면서 단백질과 채소를 함께 구성하기 좋습니다."
    },
    {
        "name": "두부 버섯 비빔밥",
        "category": "한식",
        "meal": ["아침", "점심", "저녁"],
        "tags": ["채소", "담백", "혼자", "가벼운"],
        "avoid": ["대두"],
        "items": [
            ("잡곡밥", 130, "밥공기 약 2/3공기", 205, 44, 5, 2, 5, 3),
            ("두부", 100, "일반 두부 약 1/3모", 95, 3, 10, 5, 15, 1),
            ("나물·버섯", 180, "두 주먹 정도", 110, 20, 6, 3, 280, 7),
            ("양념장", 20, "밥숟가락 약 1큰술", 45, 7, 1, 1, 390, 0),
        ],
        "why": "채소 비중을 높이면서 한 끼를 간단히 구성하기 좋습니다."
    },
    {
        "name": "에그 치킨 샌드위치 세트",
        "category": "양식",
        "meal": ["아침", "점심", "오후"],
        "tags": ["샌드위치", "간단", "베이커리", "혼자"],
        "avoid": ["계란", "밀", "우유"],
        "items": [
            ("통밀빵", 90, "식빵 약 2장", 230, 42, 9, 3, 330, 6),
            ("계란", 50, "중간 크기 1개", 72, 0, 6, 5, 70, 0),
            ("닭고기", 70, "손바닥의 약 2/3 크기", 116, 0, 22, 2, 55, 0),
            ("채소", 80, "한 주먹 정도", 35, 7, 2, 0, 45, 3),
            ("무가당 요거트", 100, "작은 컵 1개", 70, 8, 6, 2, 65, 0),
        ],
        "why": "빠르게 먹기 좋고 단백질을 보완한 간편식 조합입니다."
    },
    {
        "name": "연어 샐러드와 고구마",
        "category": "양식",
        "meal": ["점심", "저녁"],
        "tags": ["생선", "가벼운", "채소", "단백질"],
        "avoid": ["생선"],
        "items": [
            ("연어", 100, "손바닥 크기 1조각", 208, 0, 20, 13, 60, 0),
            ("샐러드 채소", 180, "두 주먹 정도", 75, 14, 5, 1, 120, 7),
            ("고구마", 150, "중간 크기 1개 정도", 195, 45, 3, 0, 60, 5),
            ("드레싱", 20, "밥숟가락 약 1큰술", 70, 5, 0, 6, 190, 0),
        ],
        "why": "채소와 생선 단백질을 중심으로 비교적 가볍게 먹기 좋은 조합입니다."
    },
]

def total(menu):
    vals = [0] * 6
    for _, _, _, kcal, carb, protein, fat, sodium, fiber in menu["items"]:
        for i, x in enumerate([kcal, carb, protein, fat, sodium, fiber]):
            vals[i] += x
    return vals

def score(menu, profile, context):
    # allergy exclusion
    allergies = profile.get("allergies", [])
    extra_allergy = profile.get("extra_allergy", "").strip()
    if any(a in menu["avoid"] for a in allergies):
        return -999

    score_value = 0
    if context["meal_time"] in menu["meal"]:
        score_value += 4
    if menu["category"] in profile.get("cuisines", []):
        score_value += 3

    likes = profile.get("likes", "").lower()
    dislikes = profile.get("dislikes", "").lower()
    for tag in menu["tags"]:
        if tag.lower() in likes:
            score_value += 4
        if tag.lower() in dislikes:
            score_value -= 8

    if context["companion"] in menu["tags"]:
        score_value += 2
    if context["mood"] in ["피곤해요", "스트레스 받아요"] and ("따뜻한" in menu["tags"] or "담백" in menu["tags"]):
        score_value += 2
    if context["weather"] in ["추워요", "비가 와요"] and ("따뜻한" in menu["tags"] or "국물" in menu["tags"]):
        score_value += 3
    if context["weather"] == "더워요" and "가벼운" in menu["tags"]:
        score_value += 3

    kcal, carb, protein, fat, sodium, fiber = total(menu)
    health = profile.get("health", [])
    if "고혈압" in health and sodium > 1100:
        score_value -= 5
    if "당뇨" in health and carb > 75:
        score_value -= 4
    if profile.get("goal") == "체중 줄이기" and kcal > 650:
        score_value -= 3
    if protein >= 25:
        score_value += 2
    if fiber >= 5:
        score_value += 1

    # free-text fields are stored now; AI interpretation comes in later version.
    _ = extra_allergy
    _ = profile.get("extra_health", "")
    return score_value

def recommend(profile, context):
    ranked = sorted(
        [(score(m, profile, context), m) for m in MENUS],
        key=lambda x: (-x[0], x[1]["name"])
    )
    return [m for s, m in ranked if s > -900][:3]

# -----------------------------
# Header
# -----------------------------
st.markdown("## 🍽️ My Meal Bot")
st.caption("건강·취향·기분·상황을 반영해 지금 어울리는 음식을 추천합니다.")
st.warning("현재 영양값은 프로토타입용 예시값입니다. 질환 치료용 식단이나 의료적 판단에 사용하지 마세요.")

if st.session_state.pop("profile_saved_notice", False):
    st.success("내 정보를 저장했습니다. 이제 '오늘 추천' 탭에서 바로 추천받을 수 있습니다.")

tab_today, tab_profile, tab_record = st.tabs(["✨ 오늘 추천", "👤 내 정보", "📊 기록"])

# -----------------------------
# TODAY: compact-first UI
# -----------------------------
with tab_today:
    if not st.session_state.profile:
        st.info("처음 한 번만 '내 정보'에서 프로필을 저장해주세요.")
    else:
        st.markdown("### 오늘 뭐 먹을까요?")
        with st.form("quick_recommend_form"):
            q1, q2 = st.columns(2)
            with q1:
                meal_time = st.selectbox("식사 시간", ["아침", "점심", "오후", "저녁", "야식"])
                companion = st.selectbox("누구와", ["혼자", "가족", "연인", "친구", "직장동료"])
            with q2:
                mood = st.selectbox("기분", ["기분 좋아요", "그냥 그래요", "조금 우울해요", "스트레스 받아요", "피곤해요", "축하할 일이 있어요", "편안해요"])
                dining = st.selectbox("식사 방식", ["상관없음", "집에서 요리", "외식", "배달", "간단하게"])

            with st.expander("＋ 상세 조건 추가"):
                e1, e2 = st.columns(2)
                with e1:
                    weather = st.selectbox("날씨/체감", ["보통이에요", "더워요", "추워요", "비가 와요"])
                    budget = st.selectbox("예산", ["상관없음", "10,000원 이하", "10,000~20,000원", "20,000~30,000원"])
                with e2:
                    scope = st.radio("추천 범위", ["지금 한 끼", "오늘 3끼", "일주일"], horizontal=False)
                    amount_view = st.radio("섭취량 표시", ["g + 생활계량", "g만 보기", "생활계량만 보기"], index=0)
                special = st.text_area("오늘 특별한 일 (선택)", placeholder="예: 일이 잘 끝났어요, 가족과 오랜만에 만나요")

            go = st.form_submit_button("✨ 지금 추천받기", type="primary", use_container_width=True)

        if go:
            context = {
                "meal_time": meal_time,
                "companion": companion,
                "mood": mood,
                "dining": dining,
                "weather": weather,
                "budget": budget,
                "scope": scope,
                "special": special,
                "amount_view": amount_view,
            }
            st.session_state.last_context = context
            st.session_state.recommendations = recommend(st.session_state.profile, context)

        if st.session_state.recommendations:
            st.divider()
            st.markdown("### 오늘의 TOP 3")
            view_mode = st.session_state.last_context.get("amount_view", "g + 생활계량")
            for i, menu in enumerate(st.session_state.recommendations, 1):
                kcal, carb, protein, fat, sodium, fiber = total(menu)
                medal = ["🥇", "🥈", "🥉"][i - 1]

                with st.container(border=True):
                    st.markdown(f"### {medal} {menu['name']}")
                    st.write(menu["why"])

                    special_text = st.session_state.last_context.get("special", "").strip()
                    if special_text:
                        st.caption(f"오늘의 상황: {special_text}")

                    st.markdown("**1인 기준 구성**")
                    for name, grams, measure, *_ in menu["items"]:
                        if view_mode == "g만 보기":
                            st.write(f"• {name}: {grams}g")
                        elif view_mode == "생활계량만 보기":
                            st.write(f"• {name}: {measure}")
                        else:
                            st.write(f"• {name}: {grams}g · {measure}")

                    with st.expander("영양정보 자세히 보기"):
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("열량", f"{kcal:.0f} kcal")
                        c2.metric("탄수화물", f"{carb:.0f} g")
                        c3.metric("단백질", f"{protein:.0f} g")
                        c4.metric("지방", f"{fat:.0f} g")
                        st.caption(f"나트륨 약 {sodium:.0f}mg · 식이섬유 약 {fiber:.0f}g")
                        if "고혈압" in st.session_state.profile.get("health", []) and sodium > 1000:
                            st.warning("나트륨이 높은 편일 수 있습니다. 국물·양념 섭취량을 줄이는 방향을 권합니다.")

                    b1, b2, b3, b4 = st.columns(4)
                    actions = [
                        (b1, "👍 좋아요", "좋아요"),
                        (b2, "👎 별로예요", "별로예요"),
                        (b3, "🍴 먹었어요", "먹었어요"),
                        (b4, "💾 저장", "저장"),
                    ]
                    for col, label, action in actions:
                        if col.button(label, key=f"{action}_{i}"):
                            st.session_state.feedback.append((datetime.now().isoformat(), menu["name"], action))
                            st.toast(f"{action} 기록 완료")

# -----------------------------
# PROFILE: simple + expandable detail
# -----------------------------
with tab_profile:
    st.markdown("### 내 정보")
    st.caption("한 번 저장하면 오늘 추천에서 반복 입력하지 않아도 됩니다.")

    with st.form("profile_form"):
        p1, p2 = st.columns(2)
        with p1:
            nickname = st.text_input("닉네임", value=st.session_state.profile.get("nickname", ""))
            age = st.number_input("나이", 18, 100, int(st.session_state.profile.get("age", 45)))
            height = st.number_input("키(cm)", 120.0, 220.0, float(st.session_state.profile.get("height", 170.0)), 0.5)
        with p2:
            sex_options = ["선택 안 함", "남성", "여성"]
            current_sex = st.session_state.profile.get("sex", "선택 안 함")
            sex = st.selectbox("성별", sex_options, index=sex_options.index(current_sex) if current_sex in sex_options else 0)
            weight = st.number_input("몸무게(kg)", 30.0, 200.0, float(st.session_state.profile.get("weight", 65.0)), 0.5)
            goal_options = ["건강하게 유지", "체중 줄이기", "체중 늘리기", "근육 관리", "영양 균형", "특별한 목표 없음"]
            current_goal = st.session_state.profile.get("goal", "건강하게 유지")
            goal = st.selectbox("목표", goal_options, index=goal_options.index(current_goal) if current_goal in goal_options else 0)

        with st.expander("건강·알레르기 자세히 입력"):
            st.markdown("**건강 참고사항**")
            health_options = ["고혈압", "당뇨", "고지혈증", "통풍", "신장질환", "위장관리가 필요함"]
            old_health = st.session_state.profile.get("health", [])
            hcols = st.columns(2)
            health = []
            for idx, item in enumerate(health_options):
                if hcols[idx % 2].checkbox(item, value=item in old_health, key=f"health_{item}"):
                    health.append(item)
            extra_health = st.text_input(
                "기타 건강 참고사항",
                value=st.session_state.profile.get("extra_health", ""),
                placeholder="예: 갑상선 관련 식이조절 필요"
            )

            st.markdown("**알레르기 / 제외 식품**")
            allergy_options = ["계란", "우유", "땅콩", "견과류", "밀", "갑각류", "생선", "대두"]
            old_allergy = st.session_state.profile.get("allergies", [])
            acols = st.columns(2)
            allergies = []
            for idx, item in enumerate(allergy_options):
                if acols[idx % 2].checkbox(item, value=item in old_allergy, key=f"allergy_{item}"):
                    allergies.append(item)
            extra_allergy = st.text_input(
                "기타 알레르기 또는 피해야 할 음식",
                value=st.session_state.profile.get("extra_allergy", ""),
                placeholder="예: 키위, 복숭아"
            )

        with st.expander("음식 취향 자세히 입력"):
            cuisine_options = ["한식", "일식", "중식", "양식", "분식", "베이커리", "디저트"]
            cuisines = st.multiselect(
                "선호 음식 종류",
                cuisine_options,
                default=st.session_state.profile.get("cuisines", ["한식"])
            )
            extra_cuisine = st.text_input(
                "기타 선호 음식 종류",
                value=st.session_state.profile.get("extra_cuisine", ""),
                placeholder="예: 동남아 음식, 지중해식"
            )
            likes = st.text_area(
                "좋아하는 음식/메뉴",
                value=st.session_state.profile.get("likes", ""),
                placeholder="예: 고등어, 샌드위치, 된장찌개"
            )
            dislikes = st.text_area(
                "싫어하는 음식/메뉴",
                value=st.session_state.profile.get("dislikes", ""),
                placeholder="예: 가지, 굴, 매우 매운 음식"
            )

        saved = st.form_submit_button("💾 내 정보 저장", type="primary", use_container_width=True)

    if saved:
        st.session_state.profile = {
            "nickname": nickname,
            "age": age,
            "sex": sex,
            "height": height,
            "weight": weight,
            "goal": goal,
            "health": health,
            "extra_health": extra_health,
            "allergies": allergies,
            "extra_allergy": extra_allergy,
            "cuisines": cuisines,
            "extra_cuisine": extra_cuisine,
            "likes": likes,
            "dislikes": dislikes,
        }
        st.session_state.profile_saved_notice = True
        st.rerun()

    if st.session_state.profile:
        p = st.session_state.profile
        bmi = p["weight"] / ((p["height"] / 100) ** 2)
        st.info(f"{p.get('nickname') or '사용자'} · BMI 참고값 {bmi:.1f} · 목표: {p['goal']}")

# -----------------------------
# RECORD
# -----------------------------
with tab_record:
    st.markdown("### 기록")
    st.caption("현재는 이 브라우저 세션의 피드백만 표시합니다. 회원 DB는 다음 단계에서 연결합니다.")
    if st.session_state.feedback:
        for when, menu, action in reversed(st.session_state.feedback):
            st.write(f"• {when[:16].replace('T', ' ')} · {menu} · {action}")
    else:
        st.info("아직 기록이 없습니다.")

    with st.expander("다음 단계 예정"):
        st.write("• 실제 섭취 음식과 추천 음식 분리 저장")
        st.write("• 주/월/분기/연간 영양 통계")
        st.write("• 음식 선호 자동 학습")
        st.write("• 회원별 로그인 및 데이터 분리")
        st.write("• 검증된 식품 영양 DB 연동")
        st.write("• 날씨 자동 연동")

st.divider()
st.caption("MVP v0.2 · 생활계량은 이해를 돕기 위한 대략적인 기준이며, 실제 식품 크기와 조리 상태에 따라 달라질 수 있습니다.")
