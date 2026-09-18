"""Browser storage UI. Persistent data is never written to a server file."""
from pathlib import Path
from uuid import uuid4
import streamlit as st
from storage_model import dumps, loads

bridge = st.components.v2.component(
    'meal_personal_storage',
    html='<small data-status></small>',
    js=Path(__file__).with_name('browser_storage.js').read_text(encoding='utf-8'),
)

def request(op, **kwargs):
    st.session_state['_storage_command'] = {'id':str(uuid4()), 'op':op, **kwargs}

def apply_data(data):
    st.session_state.profile = data['profile']
    st.session_state.feedback = data['feedback']
    st.session_state.recommendations = []
    st.session_state.last_context = {}
    st.session_state.weather = {}
    # Rebuild profile widgets after restore so old widget values cannot win.
    st.session_state['_profile_epoch'] = st.session_state.get('_profile_epoch',0) + 1

def storage_panel():
    s = st.session_state
    if '_storage_command' not in s:
        s['_storage_ready'] = False
        s['_storage_enabled'] = False
        s['_storage_raw'] = None
        s['_storage_error'] = ''
        request('load')
    # Backups are staged in the previous run, before any profile widgets exist.
    if '_restore_data' in s:
        apply_data(s.pop('_restore_data'))
    with st.expander('💾 내 기기 저장 · 백업', expanded=not s['_storage_ready']):
        st.caption('같은 브라우저에서 프로필·음식 취향·선택 기록을 다시 불러옵니다. 공용 PC에서는 켜지 마세요. 저장 자료는 암호화되지 않습니다.')
        st.caption('입력·복원한 정보는 추천 처리를 위해 앱 서버로 전달됩니다. AI 추천 사용 시 건강·취향 정보 등이 OpenAI로 전달됩니다. API 키는 저장 대상에 포함되지 않습니다.')
        cmd = s['_storage_command']
        result = bridge(data=cmd, key='meal_storage_bridge', default={'result':None}, on_result_change=lambda: None).result
        if result and result.get('id') == cmd['id'] and s.get('_storage_done') != cmd['id']:
            s['_storage_done'] = cmd['id']
            if result.get('ok'):
                s['_storage_raw'] = result['raw']
                if cmd['op'] == 'load':
                    if result['raw'] is not None:
                        try:
                            apply_data(loads(result['raw']))
                            s['_storage_enabled'] = True
                        except ValueError as exc:
                            s['_storage_error'] = str(exc) + ' 기존 저장 자료는 덮어쓰지 않았습니다.'
                    s['_storage_ready'] = True
                elif cmd['op'] == 'clear':
                    s['_storage_enabled'] = False
            else:
                s['_storage_ready'] = True
                s['_storage_error'] = result.get('error','저장 실패')
            st.rerun()
        if not s['_storage_ready']:
            st.info('기기에 저장된 정보를 확인 중입니다.')
            if st.button('기기 저장 없이 계속하기'):
                s['_storage_ready'] = True
                s['_storage_done'] = cmd['id']
                s['_storage_error'] = '기기 저장을 건너뛰었습니다. 파일 백업을 이용하거나 새로고침 후 다시 시도하세요.'
                st.rerun()
            st.stop()
        if s['_storage_error']:
            st.warning(s['_storage_error'])
            st.caption('현재 입력은 세션에 유지됩니다. 백업 파일을 내려받을 수 있습니다.')
        pending = s.get('_storage_done') != cmd['id']
        if pending:
            st.info('기기에 반영 중입니다. 완료 전에는 창을 닫지 마세요.')
        elif s['_storage_enabled'] and not s['_storage_error']:
            st.success('내 기기 저장 사용 중')
        else:
            st.caption('현재는 세션에서만 사용합니다. 백업 파일을 별도로 저장할 수 있습니다.')
        if not s['_storage_enabled'] and not s['_storage_error']:
            if st.button('이 개인 기기에 저장 켜기', disabled=pending):
                s['_storage_enabled'] = True
                st.rerun()
        if s['_storage_raw'] is not None:
            confirm = st.checkbox('이 브라우저에 저장된 자료 삭제에 동의합니다')
            if st.button('기기 저장 끄고 저장 자료 삭제', disabled=not confirm or pending):
                s['_storage_error'] = ''
                request('clear', expected=s['_storage_raw'])
                st.rerun()
            st.caption('기기 사본만 삭제합니다. 현재 세션의 내용과 다운로드한 백업 파일은 유지됩니다.')
        try:
            raw = dumps(s.profile, s.feedback)
        except ValueError as exc:
            st.error(str(exc))
            return
        st.download_button('백업 파일 다운로드', raw, file_name='my-meal-backup.json', mime='application/json')
        upload = st.file_uploader('백업 파일 선택 (최대 2MB)', type=['json'])
        replace = st.checkbox('복원 시 현재 프로필과 기록을 백업 내용으로 교체합니다')
        if st.button('선택한 백업 복원', disabled=upload is None or not replace or pending):
            try:
                if upload.size > 2_000_000:
                    raise ValueError('백업 파일은 2MB 이하만 사용할 수 있습니다.')
                s['_restore_data'] = loads(upload.getvalue())
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if s['_storage_enabled'] and not s['_storage_error'] and not pending and raw != s['_storage_raw']:
            request('save', raw=raw, expected=s['_storage_raw'])
            st.rerun()
