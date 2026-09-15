# My Meal Bot 1.0

실사용 베타 버전입니다.

## 핵심 기능
- 프로필/건강/알레르기/음식 취향
- 실시간 날씨(Open-Meteo)
- OpenAI 기반 TOP 3 개인화 추천
- 음식 역사·문화·감성 스토리텔링
- g + 생활계량
- 영양정보
- 좋아요/싫어요/먹었어요/저장
- 세션 내 간단 통계
- OpenAI 장애/키 미설정 시 기본 추천 엔진으로 자동 전환

## Streamlit Secrets
OpenAI AI 추천을 사용하려면 Streamlit Cloud > App settings > Secrets 에 아래처럼 입력하세요.

OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "gpt-5.6-luna"

OPENAI_MODEL은 생략해도 되며 기본값은 gpt-5.6-luna입니다.

## 주의
현재 영양수치는 메뉴 카탈로그 기반 참고값입니다.
상용 서비스 전 K-FIND/식품영양성분 DB 등 공신력 있는 데이터 연동을 권장합니다.
회원별 장기 저장은 아직 DB 미연결 상태입니다.
