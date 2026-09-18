"""Build meal slots from the existing filtered catalog, without API calls."""
from collections import Counter

def build_plan(profile, context, menus, score, previous=(), feedback=()):
    scope = context.get('scope', '지금 한 끼')
    single = scope == '지금 한 끼'
    slots = [(0, context['meal_time'])] if single else [
        (day, meal) for day in range(7 if scope == '일주일' else 1)
        for meal in ['아침','점심','저녁']
    ]
    used = Counter()
    shown = Counter(context.get("shown_names", []))
    recent = Counter(r.get('menu') for r in feedback[-30:] if r.get('action') == '먹었어요')
    disliked = {r.get('menu') for r in feedback[-30:] if r.get('action') == '별로예요'}
    previous_names = {r.get('name') for r in previous}
    previous_slots = {r.get('slot'): r.get('name') for r in previous}
    result = []
    for day, meal in slots:
        slot = f'{day+1}일차 · {meal}' if scope == '일주일' else meal
        eligible = [m for m in menus if meal in m['meal']]
        for choice in range(min(3, len(eligible)) if single else 1):
            candidates = [m for m in eligible if not single or m['name'] not in {r['name'] for r in result}]
            if not candidates:
                result.append({'name':'','slot':slot,'meal_time':meal,'reason':'현재 조건과 식사 시간에 맞는 메뉴가 없습니다.','story':'','story_type':''})
                break
            # Change the previous slot when possible; prefer unused alternatives.
            excluded = previous_names if single else {previous_slots.get(slot)}
            fresh = [m for m in candidates if m['name'] not in excluded]
            if fresh:
                candidates = fresh
            slot_context = dict(context, meal_time=meal)
            selected = min(candidates, key=lambda m: (
                used[m['name']],
                shown[m['name']],
                -(score(m, profile, slot_context) - recent[m['name']]*3 - (7 if m['name'] in disliked else 0)),
                m['name'],
            ))
            used[selected['name']] += 1
            result.append({
                'name':selected['name'], 'slot':slot, 'meal_time':meal,
                'reason':f'{meal}에 맞는 메뉴 중 취향과 현재 조건을 고려했습니다. 최근 식사 기록과 식단 내 반복도 함께 반영했습니다.',
                'story':selected['base_story'], 'story_type':selected['story_type'],
            })
    return result
