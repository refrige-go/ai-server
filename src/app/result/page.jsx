'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function IngredientConfirm() {
  const router = useRouter();
  // 예시 데이터
  const [ingredients, setIngredients] = useState([
    { name: '김치', confidence: 95, status: 'selected', text: '신선한 김치 500g', category: '채소' },
    { name: '대파', confidence: 78, status: 'need_check', text: '대파 1단', category: '채소' },
    { name: '소고기(?)', confidence: 45, status: 'uncertain', text: '식용우', category: '육류(추정)' },
    { name: '돼지고기', confidence: null, status: 'manual', text: '사용자가 수동 추가한 재료', category: '육류' },
  ]);
  const [input, setInput] = useState('');

  // 선택/해제/추가 핸들러
  const handleSelect = idx => {
    setIngredients(ings =>
      ings.map((ing, i) =>
        i === idx ? { ...ing, status: 'selected' } : ing
      )
    );
  };
  const handleAdd = idx => {
    setIngredients(ings =>
      ings.map((ing, i) =>
        i === idx ? { ...ing, status: 'manual' } : ing
      )
    );
  };
  const handleManualAdd = () => {
    if (!input.trim()) return;
    setIngredients([
      ...ingredients,
      { name: input, confidence: null, status: 'manual', text: '사용자가 수동 추가한 재료', category: '직접입력' }
    ]);
    setInput('');
  };

  // 3. 추가: 선택된 재료 추가하기 버튼 클릭 시 이동
  const handleAddSelected = () => {
    router.push('/ocr/complete');
  };

  return (
    <div className="container">
      <style jsx>{`
        .container { background: #f7faff; min-height: 100vh; padding: 0 0 32px 0; }
        .header { background: #f79726; color: #fff; font-weight: bold; font-size: 1.3em; text-align: center; border-radius: 0 0 18px 18px; padding: 18px 0 14px 0; margin-bottom: 18px; }
        .summary { background: #e6fff2; color: #22c55e; border-radius: 12px; padding: 12px 18px; margin: 0 auto 18px auto; width: 92vw; max-width: 400px; font-size: 1.1em; }
        .summary b { color: #22c55e; }
        .list-title { font-weight: bold; font-size: 1.1em; margin: 0 0 10px 0; }
        .ingredient-list { width: 92vw; max-width: 400px; margin: 0 auto 18px auto; }
        .ingredient-item { border-radius: 14px; margin-bottom: 12px; padding: 16px 18px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 8px #0001; }
        .ingredient-item.selected { background: #e6fff2; border: 2px solid #22c55e; }
        .ingredient-item.need_check { background: #fffbe6; border: 2px solid #ffd966; }
        .ingredient-item.uncertain { background: #ffeaea; border: 2px solid #ff7b7b; }
        .ingredient-item.manual { background: #f3f6fa; border: 2px solid #b3c6e0; }
        .ingredient-info { flex: 1; }
        .ingredient-name { font-weight: bold; font-size: 1.1em; }
        .ingredient-status { font-size: 0.95em; margin: 2px 0 4px 0; }
        .ingredient-category { font-size: 0.92em; color: #888; }
        .btn-select, .btn-add, .btn-manual { border: none; border-radius: 50%; width: 36px; height: 36px; font-size: 1.1em; font-weight: bold; cursor: pointer; }
        .btn-select { background: #22c55e; color: #fff; }
        .btn-add { background: #ffd966; color: #f79726; }
        .btn-uncertain { background: #ff7b7b; color: #fff; }
        .btn-manual { background: #b3c6e0; color: #fff; }
        .btn-selected { background: #22c55e; color: #fff; border-radius: 12px; width: auto; padding: 0 16px; font-size: 1em; }
        .manual-add-row { display: flex; align-items: center; width: 92vw; max-width: 400px; margin: 0 auto 18px auto; }
        .manual-input { flex: 1; border: 1.5px solid #f79726; border-radius: 8px; padding: 10px; font-size: 1em; margin-right: 8px; }
        .manual-btn { background: #f79726; color: #fff; border: none; border-radius: 8px; padding: 10px 18px; font-weight: bold; font-size: 1em; cursor: pointer; }
        .add-btn-row { width: 92vw; max-width: 400px; margin: 0 auto; }
        .add-btn-main { width: 100%; background: #f79726; color: #fff; border: none; border-radius: 12px; padding: 16px 0; font-size: 1.15em; font-weight: bold; margin-top: 8px; cursor: pointer; }
      `}</style>

      <div className="header">인식된 재료 확인</div>
      <div className="summary">
        <span role="img" aria-label="축하">🎉</span> <b>총 {ingredients.length}개의 재료를 찾았어요!</b><br />
        확인하시고 냉장고에 추가해보세요
      </div>
      <div className="ingredient-list">
        <div className="list-title">인식된 재료</div>
        {ingredients.map((ing, idx) => (
          <div key={idx} className={`ingredient-item ${ing.status}`}>
            <div className="ingredient-info">
              <div className="ingredient-name">{ing.name}</div>
              <div className="ingredient-status">
                {ing.status === 'selected' && <>신뢰도: {ing.confidence}% | 자동 선택됨</>}
                {ing.status === 'need_check' && <>신뢰도: {ing.confidence}% | <span style={{color:'#f79726'}}>확인 필요</span></>}
                {ing.status === 'uncertain' && <>신뢰도: {ing.confidence}% | <span style={{color:'#ff7b7b'}}>불확실</span></>}
                {ing.status === 'manual' && <>직접 추가</>}
              </div>
              <div className="ingredient-status" style={{color:'#888'}}>인식된 텍스트: "{ing.text}"</div>
              <div className="ingredient-category">카테고리: {ing.category}</div>
            </div>
            {ing.status === 'selected' && <button className="btn-selected">선택됨</button>}
            {ing.status === 'need_check' && <button className="btn-add" onClick={()=>handleSelect(idx)}>+</button>}
            {ing.status === 'uncertain' && <button className="btn-uncertain" onClick={()=>handleSelect(idx)}>+</button>}
            {ing.status === 'manual' && <button className="btn-manual">✓</button>}
          </div>
        ))}
      </div>
      <div className="manual-add-row">
        <input
          className="manual-input"
          placeholder="재료명을 입력하세요"
          value={input}
          onChange={e => setInput(e.target.value)}
        />
        <button className="manual-btn" onClick={handleManualAdd}>추가</button>
      </div>
      <div className="add-btn-row">
        <button className="add-btn-main" onClick={handleAddSelected}>선택된 재료 추가하기</button>
      </div>
    </div>
  );
}