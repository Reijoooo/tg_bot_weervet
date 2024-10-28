const { Pool } = require('pg');

// Настройки подключения
const pool = new Pool({
  user: 'postgres',      // имя пользователя
  host: 'localhost',          // хост базы данных (обычно localhost)
  database: 'weervet_tg',   // имя базы данных
  password: '2001', // пароль пользователя
  port: 5432,                 // порт PostgreSQL, по умолчанию 5432
});

// Функция для выполнения запросов
const query = (text, params) => pool.query(text, params);

module.exports = { query };
