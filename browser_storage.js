export default function({data, parentElement, setStateValue}) {
  const status = parentElement.querySelector('[data-status]');
  if (!data || status.dataset.command === data.id) return;
  status.dataset.command = data.id;
  const key = 'my-meal-bot.personal.v1';
  try {
    const current = localStorage.getItem(key);
    if (data.op === 'load') {
      setStateValue('result', {id:data.id, ok:true, raw:current});
    } else {
      // Do not silently overwrite newer records from another tab.
      if (current !== data.expected) throw new Error('다른 탭에서 기록이 변경됐습니다. 백업 후 새로고침하세요.');
      if (data.op === 'clear') localStorage.removeItem(key);
      else if (data.op === 'save') localStorage.setItem(key, data.raw);
      else throw new Error('지원하지 않는 저장 요청입니다.');
      setStateValue('result', {id:data.id, ok:true, raw:data.op === 'clear' ? null : data.raw});
    }
    status.textContent = '';
  } catch (e) {
    status.textContent = '기기 저장을 완료하지 못했습니다.';
    setStateValue('result', {id:data.id, ok:false, error:e.message});
  }
}
