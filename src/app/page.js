import { useState, useRef } from 'react';

export default function Home() {
  const [items, setItems] = useState([]);
  const [imageSrc, setImageSrc] = useState(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) videoRef.current.srcObject = stream;
    } catch (err) {
      console.error("카메라 접근 오류:", err);
    }
  };

  const captureImage = () => {
    const context = canvasRef.current.getContext('2d');
    context.drawImage(videoRef.current, 0, 0, 640, 480);
    const imageData = canvasRef.current.toDataURL('image/jpeg');
    setImageSrc(imageData);
  };

  const handleOCR = async () => {
    if (!imageSrc) return;

    // Spring Boot 서버로 전송
    const response = await fetch('http://localhost:8080/api/process-ocr', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ imageData: imageSrc }),
    });
    const data = await response.json();
    setItems(data || []);
  };

  return (
    <div>
      <video ref={videoRef} width="640" height="480" autoPlay />
      <canvas ref={canvasRef} width="640" height="480" style={{ display: 'none' }} />
      <button onClick={startCamera}>카메라 켜기</button>
      <button onClick={captureImage}>사진 찍기</button>
      <button onClick={handleOCR}>OCR 실행</button>
      {imageSrc && <img src={imageSrc} alt="Captured" />}
      <ul>
        {items.map((item, index) => (
          <li key={index}>{item.name}: {item.quantity}</li>
        ))}
      </ul>
    </div>
  );
}