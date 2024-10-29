import React from 'react';
import shedule from './pages/shedule.js';
import add_pet from './pages/add_pet.js';
import my_pets from './pages/my_pets.js';
import profile from './pages/profile.js';

function FooterButtons() {
  const handleClick = (buttonNumber) => {
    console.log(`Нажата кнопка ${buttonNumber}`);
    if (buttonNumber === 1) {
        window.location.assign('/shedule', shedule);
    }
    else if (buttonNumber === 2) {
        window.location.assign('/add_pet', add_pet);
    }
    else if (buttonNumber === 3) {
        window.location.assign('/my_pets', my_pets);
    }
    else if (buttonNumber === 4) {
        window.location.assign('/', profile);
    }
  };

  return (
    <div className="bottom-buttons">
      <button className="button" onClick={() => handleClick(1)}>Календарь</button>
      <button className="button" onClick={() => handleClick(2)}>Добавить питомца</button>
      <button className="button" onClick={() => handleClick(3)}>Мои питомцы</button>
      <button className="button" onClick={() => handleClick(4)}>Профиль</button>
    </div>
  );
}

export default FooterButtons;