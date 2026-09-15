import streamlit as st
from datetime import datetime

st.set_page_config(page_title="My Meal Bot", page_icon="🍽️", layout="wide")

for k, v in {"profile": {}, "recommendations": [], "feedback": []}.items():
    if k not in st.session_state:
        st.session_state[k] = v

MENUS = [
 {"name":"고등어구이 정식","category":"한식","meal":["점심","저녁"],"tags":["생선","담백","가족","집밥"],"avoid":["생선"],
  "items":[("잡곡밥",140,220,47,5,2,5,3),("고등어구이",100,240,0,24,16,380,0),("시금치나물",70,45,5,3,2,180,3),("두부구이",80,85,3,8,5,120,1)],
  "why":"단백질과 생선 메뉴를 함께 챙기기 좋은 균형형 한식입니다."},
 {"name":"소고기 버섯전골","category":"한식","meal":["점심","저녁"],"tags":["따뜻한","국물","가족","추운날","피곤"],"avoid":[],
  "items":[("소고기",100,215,0,26,12,65,0),("버섯·채소",180,85,14,6,2,160,6),("전골 육수",180,60,6,4,2,720,1),("잡곡밥",130,205,44,5,2,5,3)],
  "why":"따뜻한 국물과 단백질·채소를 함께 먹기 좋은 메뉴입니다."},
 {"name":"닭고기 채소덮밥","category":"한식","meal":["점심","저녁"],"tags":["간단","닭고기","혼자","단백질"],"avoid":[],
  "items":[("현미밥",150,225,48,5,2,5,3),("닭고기",120,198,0,37,4,95,0),("볶은 채소",160,120,18,5,4,320,6)],
  "why":"한 그릇으로 먹기 편하면서 단백질과 채소를 함께 구성할 수 있습니다."},
 {"name":"두부 버섯 비빔밥","category":"한식","meal":["아침","점심","저녁"],"tags":["채소","담백","혼자","가벼운"],"avoid":["대두"],
  "items":[("잡곡밥",130,205,44,5,2,5,3),("두부",100,95,3,10,5,15,1),("나물·버섯",180,110,20,6,3,280,7),("양념장",20,45,7,1,1,390,0)],
  "why":"채소 비중을 높이면서 한 끼를 간단히 구성하기 좋습니다."},
 {"name":"에그 치킨 샌드위치 세트","category":"양식","meal":["아침","점심","오후"],"tags":["샌드위치","간단","베이커리","혼자"],"avoid":["계란","밀","우유"],
  "items":[("통밀빵",90,230,42,9,3,330,6),("계란",50,72,0,6,5,70,0),("닭고기",70,116,0,22,2,55,0),("채소",80,35,7,2,0,45,3),("무가당 요거트",100,70,8,6,2,65,0)],
  "why":"빠르게 먹기 좋고 단백질을 보완한 간편식 조합입니다."},
 {"name":"연어 샐러드와 고구마","category":"양식","meal":["점심","저녁"],"tags":["생선","가벼운","채소","단백질"],"avoid":["생선"],
  "items":[("연어",100,208,0,20,13,60,0),("샐러드 채소",180,75,14,5,1,120,7),("고구마",150,195,45,3,0,60,5),("드레싱",20,70,5,0,6,190,0)],
  "why":"채소와 생선 단백질을 중심으로 비교적 가볍게 먹기 좋은 조합입니다."},
]

def total(m):
    vals=[0]*6
    for _,g,k,c,p,f,s,fi in m["items"]:
        for i,x in enumerate([k,c,p,f,s,fi]): vals[i]+=x
    return vals

def score(m,p,c):
    if any(a in m["avoid"] for a in p.get("allergies",[])): return -999
    s=4 if c["meal_time"] in m["meal"] else 0
    if m["category"] in p.get("cuisines",[]): s+=3
    likes=p.get("likes","").lower(); dislikes=p.get("dislikes","").lower()
    for tag in m["tags"]:
        if tag.lower() in likes: s+=4
        if tag.lower() in dislikes: s-=8
    if c["companion"] in m["tags"]: s+=2
    if c["mood"] in ["피곤해요","스트레스 받아요"] and ("따뜻한" in m["tags"] or "담백" in m["tags"]): s+=2
    if c["weather"] in ["추워요","비가 와요"] and ("따뜻한" in m["tags"] or "국물" in m["tags"]): s+=3
    if c["weather"]=="더워요" and "가벼운" in m["tags"]: s+=3
    kcal,carb,protein,fat,sodium,fiber=total(m)
    if "고혈압" in p.get("health",[]) and sodium>1100: s-=5
    if "당뇨" in p.get("health",[]) and carb>75: s-=4
    if p.get("goal")=="체중 줄이기" and kcal>650: s-=3
    if protein>=25: s+=2
    if fiber>=5: s+=1
    return s

def recommend(p,c):
    ranked=sorted([(score(m,p,c),m) for m in MENUS], key=lambda x:(-x[0],x[1]["name"]))
    return [m for s,m in ranked if s>-900][:3]

st.title("🍽️ My Meal Bot — 1차 프로토타입")
st.caption("건강·취향·기분·식사상황을 반영해 지금 어울리는 음식을 추천하는 MVP")
st.warning("현재 영양값은 프로토타입용 예시값입니다. 질환 치료용 식단이나 의료적 판단에 사용하지 마세요.")

t1,t2,t3=st.tabs(["👤 내 정보","✨ 오늘 추천","📊 기록 미리보기"])

with t1:
    with st.form("profile_form"):
        a,b,c=st.columns(3)
        with a:
            nickname=st.text_input("닉네임")
            age=st.number_input("나이",18,100,45)
            sex=st.selectbox("성별",["선택 안 함","남성","여성"])
        with b:
            height=st.number_input("키(cm)",120.0,220.0,170.0,0.5)
            weight=st.number_input("몸무게(kg)",30.0,200.0,65.0,0.5)
            goal=st.selectbox("목표",["건강하게 유지","체중 줄이기","체중 늘리기","근육 관리","영양 균형","특별한 목표 없음"])
        with c:
            health=st.multiselect("건강 참고사항",["고혈압","당뇨","고지혈증","통풍","신장질환","위장관리가 필요함"])
            allergies=st.multiselect("알레르기/제외 식품",["계란","우유","땅콩","견과류","밀","갑각류","생선","대두"])
        cuisines=st.multiselect("선호 음식 종류",["한식","일식","중식","양식","분식","베이커리","디저트"],default=["한식"])
        likes=st.text_input("좋아하는 음식/메뉴",placeholder="예: 고등어, 샌드위치, 된장찌개")
        dislikes=st.text_input("싫어하는 음식/메뉴",placeholder="예: 가지, 굴, 매우 매운 음식")
        saved=st.form_submit_button("💾 내 정보 저장",use_container_width=True)
    if saved:
        st.session_state.profile={"nickname":nickname,"age":age,"sex":sex,"height":height,"weight":weight,"goal":goal,"health":health,"allergies":allergies,"cuisines":cuisines,"likes":likes,"dislikes":dislikes}
        st.success("저장했습니다. '오늘 추천' 탭으로 이동하세요.")
    if st.session_state.profile:
        p=st.session_state.profile
        bmi=p["weight"]/((p["height"]/100)**2)
        st.info(f"{p.get('nickname') or '사용자'} · BMI 참고값 {bmi:.1f} · 목표: {p['goal']}")

with t2:
    if not st.session_state.profile:
        st.info("먼저 '내 정보' 탭에서 프로필을 저장해주세요.")
    else:
        with st.form("context"):
            a,b,c=st.columns(3)
            with a:
                meal_time=st.selectbox("언제 드시나요?",["아침","점심","오후","저녁","야식"])
                companion=st.selectbox("누구와 드시나요?",["혼자","가족","연인","친구","직장동료"])
            with b:
                mood=st.selectbox("오늘 기분",["기분 좋아요","그냥 그래요","조금 우울해요","스트레스 받아요","피곤해요","축하할 일이 있어요","편안해요"])
                weather=st.selectbox("현재 날씨/체감",["보통이에요","더워요","추워요","비가 와요"])
            with c:
                dining=st.selectbox("식사 방식",["상관없음","집에서 요리","외식","배달","간단하게"])
                budget=st.selectbox("예산",["상관없음","10,000원 이하","10,000~20,000원","20,000~30,000원"])
            special=st.text_area("오늘 특별한 일이 있었나요? (선택)")
            scope=st.radio("추천 범위",["지금 한 끼","오늘 3끼","일주일"],horizontal=True)
            go=st.form_submit_button("✨ 지금 나에게 맞는 음식 추천",type="primary",use_container_width=True)
        if go:
            ctx={"meal_time":meal_time,"companion":companion,"mood":mood,"weather":weather,"dining":dining,"budget":budget,"special":special,"scope":scope}
            st.session_state.recommendations=recommend(st.session_state.profile,ctx)
            st.session_state.last_context=ctx
        if st.session_state.recommendations:
            st.subheader("오늘의 TOP 3")
            for i,m in enumerate(st.session_state.recommendations,1):
                kcal,carb,protein,fat,sodium,fiber=total(m)
                with st.container(border=True):
                    st.markdown(f"### {['🥇','🥈','🥉'][i-1]} {m['name']}")
                    st.write(m["why"])
                    st.markdown("**1인 기준 구성**")
                    for name,g,*_ in m["items"]: st.write(f"• {name}: {g}g")
                    x1,x2,x3,x4=st.columns(4)
                    x1.metric("열량",f"{kcal:.0f} kcal"); x2.metric("탄수화물",f"{carb:.0f} g"); x3.metric("단백질",f"{protein:.0f} g"); x4.metric("지방",f"{fat:.0f} g")
                    st.caption(f"나트륨 약 {sodium:.0f}mg · 식이섬유 약 {fiber:.0f}g")
                    b1,b2,b3,b4=st.columns(4)
                    for col,label,action in [(b1,"👍 좋아요","좋아요"),(b2,"👎 별로예요","별로예요"),(b3,"🍴 먹었어요","먹었어요"),(b4,"💾 저장","저장")]:
                        if col.button(label,key=f"{action}_{i}"):
                            st.session_state.feedback.append((datetime.now().isoformat(),m["name"],action))
                            st.toast(f"{action} 기록 완료")

with t3:
    st.subheader("기록/통계 미리보기")
    if st.session_state.feedback:
        for when,menu,action in reversed(st.session_state.feedback):
            st.write(f"• {when[:16].replace('T',' ')} · {menu} · {action}")
    else:
        st.info("아직 기록이 없습니다.")
    st.markdown("**2차 예정:** 회원 DB · 실제 섭취기록 · 주/월/분기/연간 통계 · 날씨 자동연동 · 검증된 영양DB")

st.divider()
st.caption("MVP v0.1 · 실제 서비스 전 영양값을 검증된 데이터베이스로 교체해야 합니다.")
