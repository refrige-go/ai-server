'use client';

import React, { useRef } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const videoRef = useRef(null);
  const router = useRouter();

  // 카메라 켜기
  const startCamera = async () => {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    }
  };

  // 사진 촬영
  const capturePhoto = () => {
    if (!videoRef.current) return;
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    //alert('사진이 촬영되었습니다!');
    router.push('/result');
  };

  // 페이지 이동
  const goGallery = () => {
    window.location.href = '/gallery';
  };
  const goHistory = () => {
    window.location.href = '/history';
  };

  return (
    <div className="container">
      <style jsx>{`
        body, .container {
          background: #f7faff;
        }
        .header-wrap {
          width: 92vw;
          max-width: 400px;
          margin: 0 auto;
        }
        .header {
          background: #f79726;
          color: #fff;
          padding: 20px 24px 14px 24px;
          border-radius: 0 0 18px 18px;
          box-shadow: 0 2px 8px #0001;
          text-align: left;
          width: 100%;
          box-sizing: border-box;
        }
        .header-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .header-title {
          font-size: 1.5em;
          font-weight: bold;
        }
        .header-info {
          background: #fff3;
          border-radius: 50%;
          width: 22px; height: 22px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1em;
          font-weight: bold;
        }
        .header-desc {
          font-size: 1em;
          margin-top: 6px;
          opacity: 0.95;
        }
        .camera-area {
          margin: 22px auto 0 auto;
          width: 92vw;
          max-width: 400px;
          aspect-ratio: 1/1.1;
          background: #f3f6fa;
          border: 2px dashed #b3c6e0;
          border-radius: 18px;
          position: relative;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          overflow: hidden;
        }
        video {
          width: 100%;
          height: 100%;
          object-fit: cover;
          border-radius: 18px;
          z-index: 1;
        }
        .camera-guide {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -60%);
          color: #222;
          text-align: center;
          z-index: 2;
          pointer-events: none;
          width: 90%;
        }
        .camera-guide-main {
          font-size: 1.15em;
          font-weight: bold;
          color: #222;
        }
        .camera-guide-sub {
          font-size: 0.98em;
          color: #7a8fa6;
          margin-top: 4px;
        }
                  .tips {
          margin: 16px auto 0 auto;
          width: 92vw;
          max-width: 400px;
          background: #fffbe6;
          border: 1.5px solid #ffe0a3;
          border-radius: 10px;
          color: #e67e22;
          font-size: 1em;
          padding: 10px 15px 8px 15px;
          box-sizing: border-box;
          font-weight: 500;
        }
        .tips-title {
          font-weight: bold;
          color: #ff9800;
          font-size: 1.08em;
        }
        .tips-list {
          margin: 7px 0 0 0;
          padding: 0;
          list-style: none;
          color: #e67e22;
          font-weight: 400;
        }
        .footer {
          display: flex;
          justify-content: space-around;
          align-items: center;
          margin: 28px auto 0 auto;
          width: 92vw;
          max-width: 400px;
        }
        .footer-btn {
          flex: 1;
          margin: 0 8px;
          padding: 12px 0;
          font-size: 1.08em;
          border: none;
          border-radius: 12px;
          background: #f3f6fa;
          color: #f79726;
          font-weight: bold;
          cursor: pointer;
          transition: background 0.2s;
        }
        .footer-btn:active {
          background: #ffe0a3;
        }
        .main-btn {
          background: #fff;
          color: #f79726;
          font-size: 2.1em;
          border-radius: 50%;
          width: 64px;
          height: 64px;
          min-width: 64px;
          min-height: 64px;
          max-width: 64px;
          max-height: 64px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 12px;
          box-shadow: 0 2px 8px #0002;
          border: 4px solid #f79726;
          padding: 0; /* padding 제거 */
          flex: none; /* flex-grow, flex-shrink 모두 0 */
        }
        .main-btn:active {
          background: #d17a00;
        }
        @media (max-width: 500px) {
          .header-wrap, .header, .camera-area, .tips, .footer { max-width: 98vw; }
        }
      `}</style>

      {/* 상단 헤더 */}
      <div className="header-wrap">
        <div className="header">
          <div className="header-row">
            <span className="header-title">재료 사진 인식</span>
            <span className="header-info">i</span>
          </div>
          <div className="header-desc">
            AI가 재료를 자동으로 찾아드려요!<br />
            영수증이나 재료 사진을 찍어보세요
          </div>
        </div>
      </div>

      {/* 카메라 영역 */}
      <div className="camera-area" onClick={startCamera}>
        <video ref={videoRef} autoPlay playsInline />
        <div className="camera-guide">
          <div className="camera-guide-main">재료나 영수증을 화면에 맞춰 촬영하세요</div>
          <div className="camera-guide-sub">명확하게 보이도록 가까이서 찍으면 인식률이 높아져요</div>
        </div>
      </div>

      {/* 촬영 팁 */}
      <div className="tips">
        <div className="tips-title">촬영 팁</div>
        <ul className="tips-list">
          <li>밝은 곳에서 촬영하세요</li>
          <li>글자가 선명하게 보이도록 해주세요</li>
          <li>영수증은 구겨지지 않게 펼쳐주세요</li>
        </ul>
      </div>

      {/* 하단 버튼 */}
      <div className="footer">
        <button className="footer-btn" onClick={goGallery}>갤러리</button>
        <button className="footer-btn main-btn" onClick={capturePhoto}>●</button>
        <button className="footer-btn" onClick={goHistory}>인식 기록</button>
      </div>
    </div>
  );
}