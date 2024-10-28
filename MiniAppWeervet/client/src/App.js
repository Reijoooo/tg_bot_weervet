import React, { useEffect, useState } from 'react';
import FooterButtons from './FooterButtons';
import Back_button from './BackButton.js';
// import shedule from './pages/shedule.js';
// import add_pet from './pages/add_pet.js';
// import my_pets from './pages/my_pets.js';
// import profile from './pages/profile.js';
// import { BrowserRouter as Router, Route, Link, Routes, BrowserRouter } from "react-router-dom";

function App() {
  const [viewportHeight, setViewportHeight] = useState(window.innerHeight);

  useEffect(() => {
    if (window.Telegram && window.Telegram.WebApp) {
      const tg = window.Telegram.WebApp;

      // Вызов expand() для автоматического масштабирования
      tg.expand();

      const handleViewportChange = () => {
        setViewportHeight(tg.viewportHeight); // Устанавливаем высоту вьюпорта от Telegram SDK
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
      {/* <Back_button /> */}
      {/* <BrowserRouter>
        <Routes>
            <Route path="/shedule" exact component={shedule}/>
            <Route path="/add_pet" exact component={add_pet}/>
            <Route path="/my_pets" exact component={my_pets}/>
            <Route path="/profile" exact component={profile}/>
        </Routes>
      </BrowserRouter> */}
    </div>
  );
}

export default App;
