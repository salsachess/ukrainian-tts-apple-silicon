const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('./characters.sqlite');

db.serialize(() => {
    db.run(`
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            voice_id TEXT
        )
    `);
});

module.exports = db;
