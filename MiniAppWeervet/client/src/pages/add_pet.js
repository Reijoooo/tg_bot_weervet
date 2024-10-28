import React, { useEffect, useState } from 'react';

function Add_pet() {
    const [name, setName] = useState('');
    const [type, setType] = useState('');
    const [date_birth, setDate_birth] = useState('');
    const [age, setAge] = useState('');
    const [sex, setSex] = useState('');
    const [breed, setBreed] = useState('');
    const [color, setColor] = useState('');
    const [weight, setWeight] = useState('');
    const [sterilized, setSterilized] = useState('');
    const [chip_number, setChip_number] = useState('');
    const [chip_place, setChip_place] = useState('');
    const [town, setTown] = useState('');
    const [keeping, setKeeping] = useState('');
    const [special_signs, setSpecial_signs] = useState('');
    const [photo, setPhoto] = useState('');

    // Получаем сегодняшнуюю дату
    const [today, setToday] = useState('');
    useEffect(() => {
        const currentDate = new Date();
        const formattedDate = currentDate.toISOString().split('T')[0]; // Форматируем в YYYY-MM-DD
        setToday(formattedDate);
    }, []);

    const calculateAge = () => {
        if (!date_birth) return;
    
        const today = new Date();
        const birth = new Date(date_birth);
    
        let age = today.getFullYear() - birth.getFullYear();
        const monthDifference = today.getMonth() - birth.getMonth();
        const dayDifference = today.getDate() - birth.getDate();
    
        // Проверяем, был ли день рождения в текущем году
        if (monthDifference < 0 || (monthDifference === 0 && dayDifference < 0)) {
          age -= 1;
        }


    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
        const response = await fetch('/api/add_pets', {
            method: 'POST',
            headers: {
            'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, type, date_birth, age, sex, breed, color, weight, sterilized, chip_number, chip_place, town, keeping, special_signs, photo}),
        });

        if (response.ok) {
            alert('Данные успешно отправлены!');
            // setName('');
            // setType('');
            // set('');
            // set('');
            // set('');
            // set('');
            // set('');
            // set('');
            // set('');
            // set('');
            // set('');
            // set('');
            // set('');
            // set('');
            // set('');
            // set('');
            // set('');
            // set('');
            // set('');
        } else {
            alert('Ошибка при отправке данных');
        }
        } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка при отправке данных');
        }
    };

    return (
        <form onSubmit={handleSubmit}>
        <label>
            Имя:
            <input type="text" value={name} onChange={(e) => setName(e.target.value)}/>
        </label>
        <br />
        <label>
            Вид:
            <input type="text" value={type} onChange={(e) => setType(e.target.value)}/>
        </label>
        <br />
        <label>
            Дата рождения (приблизительная):
            <input type="date" max={today} value={date_birth} onChange={(e) => setDate_birth(e.target.value)}/>
        </label>
        <br />
        <label>
            Пол:
            <select type="text" value={age} onChange={(e) => setSex(e.target.value)}>
                <option value="man">Мужской</option>
                <option value="woman">Женский</option>
            </select>
        </label>
        <br />
        <label>
            Порода:
            <input type="text" value={breed} onChange={(e) => setBreed(e.target.value)}/>
        </label>
        <br />
        <label>
            Цвет:
            <input type="text" value={color} onChange={(e) => setColor(e.target.value)}/>
        </label>
        <br />
        <label>
            Вес:
            <input type="number" step="0,1" value={weight} onChange={(e) => setWeight(e.target.value)}/>
        </label>
        <br />
        <label>
            Стерилизация:
            <select type="text" value={sterilized} onChange={(e) => setSterilized(e.target.value)}>
                <option value="yes">Да</option>
                <option value="no">Нет</option>
            </select>
        </label>
        <br />
        <label>
            Номер чипа (если есть):
            <input type="text" value={chip_number} onChange={(e) => setChip_number(e.target.value)}/>
        </label>
        <br />
        <label>
            Место установки чипа:
            <input type="text" value={chip_place} onChange={(e) => setChip_place(e.target.value)}/>
        </label>
        <br />
        <label>
            Город проживания:
            <input type="text" value={town} onChange={(e) => setTown(e.target.value)}/>
        </label>
        <br />
        <label>
            Условия содержания:
            <input type="text" value={keeping} onChange={(e) => setKeeping(e.target.value)}/>
        </label>
        <br />
        <label>
            Особые приметы:
            <input type="text" value={special_signs} onChange={(e) => setSpecial_signs(e.target.value)}/>
        </label>
        <br />
        <label>
            Фото:
            <input type="file" value={photo} onChange={(e) => setPhoto(e.target.value)}/>
        </label>
        <button type="submit" onClick={calculateAge}>Отправить</button>
        </form>
    );
    }
}

export default Add_pet;