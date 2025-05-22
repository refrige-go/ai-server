'use client';

import { useRouter } from 'next/navigation';

export default function CompletePage() {
  const router = useRouter();
  const ingredients = [
    { name: '김치' },
    { name: '대파' },
    { name: '돼지고기' }
  ];

  return (
    <div className="container">
      <style jsx>{`
        .container { background: #f7faff; min-height: 100vh; padding: 0 0 32px 0; }
        .header { background: #f79726; color: #fff; font-weight: bold; font-size: 1.3em; text-align: center; border-radius: 0 0 18px 18px; padding: 18px 0 14px 0; margin-bottom: 18px; }
        .success-box { background: #e6fff2; color: #22c55e; border-radius: 12px; padding: 16px 18px; margin: 0 auto 18px auto; width: 92vw; max-width: 400px; font-size: 1.1em; display: flex; align-items: center; justify-content: center; gap: 10px;}
        .success-check { background: #f79726; color: #fff; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 1.3em; }
        .ingredient-list { width: 92vw; max-width: 400px; margin: 0 auto 18px auto; }
        .ingredient-item { background: #fff; border-radius: 14px; margin-bottom: 12px; padding: 16px 18px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 8px #0001; border: 2px solid #f79726; }
        .ingredient-name { font-weight: bold; font-size: 1.1em; color: #222; }
        .ingredient-check { background: #f79726; color: #fff; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-size: 1.1em; }
        .footer-btn-main { width: 92vw; max-width: 400px; margin: 32px auto 0 auto; display: block; background: #f79726; color: #fff; border: none; border-radius: 12px; padding: 16px 0; font-size: 1.15em; font-weight: bold; cursor: pointer; text-align: center; }
      `}</style>

      <div className="header">재료 추가 완료</div>
      <div className="success-box">
        <span className="success-check">✓</span>
        <span>재료가 성공적으로 추가되었습니다!</span>
      </div>
      <div className="ingredient-list">
        {ingredients.map((ing, idx) => (
          <div key={idx} className="ingredient-item">
            <span className="ingredient-name">{ing.name}</span>
            <span className="ingredient-check">✓</span>
          </div>
        ))}
      </div>
      <button className="footer-btn-main" onClick={() => router.push('/refrigerator')}>
        내 냉장고 보기
      </button>
    </div>
  );
}