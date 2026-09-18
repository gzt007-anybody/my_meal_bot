"""Versioned, validated personal data. No database or Streamlit dependencies."""
import json
import math

MAX_BYTES = 2_000_000
MAX_RECORDS = 3000
LISTS = {
    'health': ['고혈압','당뇨','고지혈증','통풍','신장질환','위장관리가 필요함'],
    'allergies': ['계란','우유','땅콩','견과류','밀','갑각류','생선','대두'],
    'cuisines': ['한식','일식','중식','양식','분식','베이커리','디저트'],
}
TEXTS = ('nickname','sex','goal','extra_health','extra_allergy','extra_cuisine','likes','dislikes')

def text(value, limit=2000):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError('문자 항목의 형식 또는 길이가 올바르지 않습니다.')
    return value

def number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError('숫자 항목이 허용 범위를 벗어났습니다.')
    return value

def validate(data):
    if not isinstance(data, dict) or data.get('format') != 'my-meal-bot' or data.get('version') != 1:
        raise ValueError('지원하지 않는 백업 파일입니다. My Meal Bot 버전 1 백업을 선택하세요.')
    p = data.get('profile', {})
    if not isinstance(p, dict):
        raise ValueError('프로필 형식이 올바르지 않습니다.')
    clean = {}
    if p:
        for key in TEXTS:
            clean[key] = text(p.get(key, ''))
        for key, default, low, high in [('age',45,18,100),('height',170.,120,220),('weight',65.,30,200)]:
            clean[key] = number(p.get(key, default), low, high)
        clean['age'] = int(clean['age'])
        for key, options in LISTS.items():
            values = p.get(key, [])
            if not isinstance(values, list) or any(not isinstance(v,str) or v not in options for v in values):
                raise ValueError('프로필 선택 항목이 올바르지 않습니다.')
            clean[key] = list(dict.fromkeys(values))
    records = data.get('feedback', [])
    if not isinstance(records, list) or len(records) > MAX_RECORDS:
        raise ValueError('기록은 최대 3,000개까지 저장할 수 있습니다.')
    cleaned = []
    for r in records:
        if not isinstance(r, dict) or r.get('action') not in ['좋아요','별로예요','먹었어요','저장']:
            raise ValueError('음식 기록 형식이 올바르지 않습니다.')
        item = {k: text(r.get(k,''), 200) for k in ['time','menu','action','category','meal_time']}
        for k in ['kcal','protein','sodium']:
            item[k] = number(r.get(k,0), 0, 1_000_000)
        cleaned.append(item)
    return {'format':'my-meal-bot','version':1,'profile':clean,'feedback':cleaned}

def loads(raw):
    if not isinstance(raw, (str, bytes)) or len(raw.encode('utf-8') if isinstance(raw,str) else raw) > MAX_BYTES:
        raise ValueError('백업 파일은 2MB 이하만 사용할 수 있습니다.')
    try:
        return validate(json.loads(raw))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError('올바른 JSON 백업 파일이 아닙니다.') from exc

def dumps(profile, feedback):
    data = validate({'format':'my-meal-bot','version':1,'profile':profile,'feedback':feedback})
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True)
    if len(raw.encode('utf-8')) > MAX_BYTES:
        raise ValueError('저장 용량을 초과했습니다. 백업 후 오래된 기록을 삭제하세요.')
    return raw
