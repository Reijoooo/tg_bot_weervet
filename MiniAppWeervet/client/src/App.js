import React, { useEffect, useState } from 'react';

function App() {
  const [viewportHeight, setViewportHeight] = useState(window.innerHeight); // Управление высотой экрана

  useEffect(() => {
    const tg = window.Telegram.WebApp;

    // Разворачиваем мини-приложение на весь экран
    tg.expand();

    // Изменение высоты окна при изменении вьюпорта
    const handleViewportChange = () => {
      setViewportHeight(tg.viewportHeight);
      console.log("Изменение вьюпорта. Высота: " + tg.viewportHeight);
    };

    tg.onEvent('viewportChanged', handleViewportChange);

    return () => {
      tg.offEvent('viewportChanged', handleViewportChange);
    };
  }, []);

  return (
    <div id="app" style={{ height: `${viewportHeight}px` }}>
      <h1>Контент приложения</h1>
      <div className="bottom-buttons">
        <button className="button">Кнопка 1</button>
        <button className="button">Кнопка 2</button>
        <button className="button">Кнопка 3</button>
        <button className="button">Кнопка 4</button>
      </div>
    </div>
  );
}

export default App;
