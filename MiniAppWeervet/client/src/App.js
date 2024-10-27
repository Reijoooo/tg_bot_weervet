import React, { useEffect, useState } from 'react';

function FooterButtons() {
  const handleClick = (button) => {
    console.log(`Button ${button} clicked!`);
  };

  return (
    <div className="bottom-buttons">
      <button className="button" onClick={() => handleClick(1)}>Кнопка 1</button>
      <button className="button" onClick={() => handleClick(2)}>Кнопка 2</button>
      <button className="button" onClick={() => handleClick(3)}>Кнопка 3</button>
      <button className="button" onClick={() => handleClick(4)}>Кнопка 4</button>
    </div>
  );
}

function App() {
  const [viewportHeight, setViewportHeight] = useState(window.innerHeight);

  useEffect(() => {
    if (window.Telegram && window.Telegram.WebApp) {
      const tg = window.Telegram.WebApp;
      tg.expand();

      const handleViewportChange = () => {
        setViewportHeight(tg.viewportHeight);
        console.log("Изменение вьюпорта. Высота: " + tg.viewportHeight);
      };

      tg.onEvent('viewportChanged', handleViewportChange);

      return () => {
        tg.offEvent('viewportChanged', handleViewportChange);
      };
    }
  }, []);

  return (
    <div id="app" style={{ height: `${viewportHeight}px` }}>
      <h1>Контент приложения</h1>
      <FooterButtons />
    </div>
  );
}

export default App;
