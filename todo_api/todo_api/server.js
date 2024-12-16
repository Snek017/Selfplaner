const express = require("express");
const fs = require("fs");
const path = require("path");
const app = express();
const PORT = 5000;

// Middleware für JSON und statische Dateien
app.use(express.json());
app.use(express.static(path.join(__dirname, "public"))); // Statische Dateien im "public"-Ordner

// Pfad zur JSON-Datei
const DATA_PATH = path.join(__dirname, "todo_data.json");

// Funktion: JSON-Daten laden
function loadData() {
    try {
        const data = fs.readFileSync(DATA_PATH, "utf-8");
        return JSON.parse(data);
    } catch (error) {
        console.error("Error loading data:", error);
        // Rückfall auf Standardstruktur, falls Datei fehlt
        return {
            tasks: { today: [], tomorrow: [], day_after: [] },
            points: 0,
            inventory: [],
            recurring_tasks: [],
            rewards: [],
            redemption_history: {},
            completed_recurring_tasks: { today: [], tomorrow: [], day_after: [] },
        };
    }
}

// Funktion: JSON-Daten speichern
function saveData(data) {
    try {
        fs.writeFileSync(DATA_PATH, JSON.stringify(data, null, 2));
        console.log("Data saved successfully.");
    } catch (error) {
        console.error("Error saving data:", error);
    }
}

// Root-Route (HTML-Seite oder Begrüßungsnachricht)
app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "public", "index.html")); // Index-Datei bereitstellen
});

// API-Endpunkte

// 1. JSON-Daten abrufen
app.get("/api/get_json", (req, res) => {
    try {
        const data = loadData();
        res.json(data);
    } catch (error) {
        console.error("Error loading JSON data:", error);
        res.status(500).json({ message: "Failed to load data." });
    }
});

// 2. JSON-Daten aktualisieren
app.post("/api/update_json", (req, res) => {
    try {
        const incomingData = req.body;
        const existingData = loadData();

        // Aktualisiere nur die Felder, die im Request vorhanden sind
        existingData.tasks = incomingData.tasks || existingData.tasks;
        existingData.points = incomingData.points || existingData.points;
        existingData.inventory = incomingData.inventory || existingData.inventory;
        existingData.recurring_tasks =
            incomingData.recurring_tasks || existingData.recurring_tasks;

        // **Rewards (Shop) nur überschreiben, wenn im Request vorhanden**
        existingData.rewards = incomingData.rewards || existingData.rewards;

        existingData.redemption_history =
            incomingData.redemption_history || existingData.redemption_history;

        // Daten speichern
        saveData(existingData);
        res.json({ message: "Data updated successfully!" });
    } catch (error) {
        console.error("Error updating JSON data:", error);
        res.status(500).json({ message: "Failed to update data." });
    }
});

// Server starten
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});
