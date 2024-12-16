const SERVER_URL = "http://45.133.9.62:5000/api";

let tasks = { today: [], tomorrow: [], day_after: [] };
let points = 0;
let inventory = [];
let recurringTasks = [];
let redemptionHistory = {};
let rewards = [];
let selectedDay = "today";

// Fetch data from the server
async function loadData() {
    console.log("Loading data from server...");
    try {
        const response = await fetch(`${SERVER_URL}/get_json`);
        if (!response.ok) throw new Error(`Failed to fetch data: ${response.status}`);
        
        const data = await response.json();
        console.log("Server response:", data);

        tasks = data.tasks || { today: [], tomorrow: [], day_after: [] };
        points = data.points || 0;
        inventory = data.inventory || [];
        recurringTasks = data.recurring_tasks || [];
        redemptionHistory = data.redemption_history || {};
        rewards = data.rewards || [];

        addRecurringTasksToDailyTasks(); // Recurring Tasks einfügen
        updateUI();
        updateDateButtons();
    } catch (error) {
        console.error("Error loading data:", error);
        alert("Failed to load data from the server.");
    }
}

// Save data to the server
async function saveData() {
    console.log("Saving data to server...");
    try {
        const data = {
            tasks,
            points,
            inventory,
            recurring_tasks: recurringTasks,
            redemption_history: redemptionHistory,
        };

        const response = await fetch(`${SERVER_URL}/update_json`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });

        if (!response.ok) throw new Error("Failed to save data.");
        console.log("Data saved successfully.");
    } catch (error) {
        console.error("Error saving data:", error);
        alert("Failed to save data.");
    }
}

// Dynamische Beschriftungen für Datum-Buttons
function getDateLabels() {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);
    const dayAfter = new Date(today);
    dayAfter.setDate(today.getDate() + 2);

    return {
        today: `Today (${today.toLocaleDateString()})`,
        tomorrow: `Tomorrow (${tomorrow.toLocaleDateString()})`,
        day_after: `Day After (${dayAfter.toLocaleDateString()})`,
    };
}

function updateDateButtons() {
    const labels = getDateLabels();
    document.getElementById("today-button").textContent = labels.today;
    document.getElementById("tomorrow-button").textContent = labels.tomorrow;
    document.getElementById("day-after-button").textContent = labels.day_after;
}

// Punkte aktualisieren
function updatePoints() {
    document.getElementById("points-display").textContent = `Points: ${points}`;
}

function addTask() {
    const taskInput = document.getElementById("new-task");
    const taskName = taskInput.value.trim();

    console.log("Adding task:", taskName); // Debugging

    if (taskName) {
        tasks[selectedDay].push({ name: taskName, completed: false });
        taskInput.value = "";
        updateUI();
        saveData();
    } else {
        alert("Task name cannot be empty.");
    }
}

// Aufgaben für den gewählten Tag anzeigen
function updateTasks() {
    const tasksList = document.getElementById("tasks-list");
    tasksList.innerHTML = "";

    tasks[selectedDay].forEach((task, index) => {
        const taskItem = document.createElement("div");
        taskItem.className = "task-box";

        const taskText = document.createElement("span");
        taskText.textContent = task.completed ? `[x] ${task.name}` : `[ ] ${task.name}`;
        taskText.onclick = () => toggleTask(selectedDay, index);

        const deleteButton = document.createElement("button");
        deleteButton.textContent = "Delete";
        deleteButton.className = "delete-button";
        deleteButton.onclick = () => deleteTask(selectedDay, index);

        taskItem.appendChild(taskText);
        taskItem.appendChild(deleteButton);
        tasksList.appendChild(taskItem);
    });
}

// Task abhaken
function toggleTask(day, index) {
    const task = tasks[day][index];
    task.completed = !task.completed;

    // Punkteberechnung: Nur für Nicht-Recurring Tasks
    if (!task.isRecurring) {
        points += task.completed ? 5 : -5;
    }

    updateUI();
    saveData();
}

// Task löschen
function deleteTask(day, index) {
    tasks[day].splice(index, 1);
    updateUI();
    saveData();
}

// Recurring Tasks zu Daily Tasks hinzufügen
function addRecurringTasksToDailyTasks() {
    Object.keys(tasks).forEach((day) => {
        recurringTasks.forEach((recurringTask) => {
            const exists = tasks[day].some((task) => task.name === recurringTask.name);
            if (!exists) {
                tasks[day].push({ name: recurringTask.name, completed: false, isRecurring: true });
            }
        });
    });
    saveData();
}

// Recurring Tasks anzeigen
function updateRecurringTasks() {
    const recurringList = document.getElementById("recurring-list");
    recurringList.innerHTML = "";

    recurringTasks.forEach((task, index) => {
        const taskDiv = document.createElement("div");
        taskDiv.className = "task-box";

        const taskText = document.createElement("span");
        taskText.textContent = task.name;

        const deleteButton = document.createElement("button");
        deleteButton.textContent = "Delete";
        deleteButton.className = "delete-button";
        deleteButton.onclick = () => {
            recurringTasks.splice(index, 1);
            updateRecurringTasks();
            addRecurringTasksToDailyTasks(); // Daily Tasks aktualisieren
            saveData();
        };

        taskDiv.appendChild(taskText);
        taskDiv.appendChild(deleteButton);
        recurringList.appendChild(taskDiv);
    });
}

// Neue Recurring Task hinzufügen
function addRecurringTask() {
    const taskInput = document.getElementById("new-recurring-task");
    const taskName = taskInput.value.trim();

    if (taskName) {
        recurringTasks.push({ name: taskName });
        taskInput.value = "";
        updateRecurringTasks();
        addRecurringTasksToDailyTasks(); // Direkt in die Daily Tasks einfügen
        saveData();
    } else {
        alert("Recurring task name cannot be empty.");
    }
}

function updateUnfinishedTasks() {
    const unfinishedList = document.getElementById("unfinished-list");
    unfinishedList.innerHTML = ""; // Liste zurücksetzen

    // Iteriere über alle Tagesaufgaben
    Object.keys(tasks).forEach((day) => {
        tasks[day].forEach((task, index) => {
            if (!task.completed) {
                const taskDiv = document.createElement("div");
                taskDiv.className = "task-box";

                // Task-Name
                const taskText = document.createElement("span");
                taskText.textContent = `${task.name} (${day})`;
                taskText.onclick = () => toggleUnfinishedTask(day, index); // Task abhaken

                // Löschen-Button
                const deleteButton = document.createElement("button");
                deleteButton.textContent = "Delete";
                deleteButton.className = "delete-button";
                deleteButton.onclick = () => {
                    tasks[day].splice(index, 1); // Task aus dem Array entfernen
                    updateUnfinishedTasks(); // Liste neu laden
                    saveData(); // Änderungen speichern
                };

                // Elemente zusammenfügen
                taskDiv.appendChild(taskText);
                taskDiv.appendChild(deleteButton);
                unfinishedList.appendChild(taskDiv);
            }
        });
    });
}

// Abhaken einer Unfinished Task
function toggleUnfinishedTask(day, index) {
    tasks[day][index].completed = true;
    points += 2; // Nur 2 Punkte für unerledigte Aufgaben
    updateUI(); // UI aktualisieren
    saveData(); // Änderungen speichern
}

// Unfinished Task abhaken
function toggleUnfinishedTask(day, index) {
    tasks[day][index].completed = true;
    points += 2; // Nur 2 Punkte für Unfinished Tasks
    updateUI();
    saveData();
}

// Shop aktualisieren
function updateShop() {
    const shopList = document.getElementById("shop-list");
    shopList.innerHTML = ""; // Shop-Inhalte zurücksetzen

    // Dynamische Erstellung basierend auf Rewards aus JSON
    rewards.forEach((reward) => {
        const button = document.createElement("button");
        button.textContent = `${reward.name} - ${reward.cost} Points`;
        button.className = "shop-button";
        button.onclick = () => redeemReward(reward); // Einlösen-Logik
        shopList.appendChild(button);
    });
}

// Belohnung einlösen
function redeemReward(reward) {
    if (points >= reward.cost) {
        points -= reward.cost; // Punkte abziehen
        inventory.push(reward.name); // Belohnung ins Inventar
        updateUI(); // UI aktualisieren
        saveData(); // Änderungen speichern
        alert(`You redeemed: ${reward.name}`);
    } else {
        alert("Not enough points!");
    }
}

// Inventar anzeigen
function updateInventory() {
    const inventoryList = document.getElementById("inventory-list");
    inventoryList.innerHTML = "";

    inventory.forEach((item) => {
        const itemDiv = document.createElement("div");
        itemDiv.textContent = item;
        inventoryList.appendChild(itemDiv);
    });
}

// UI aktualisieren
function updateUI() {
    updatePoints();
    updateTasks();
    updateShop();
    updateInventory();
    updateRecurringTasks();
    updateUnfinishedTasks();
}

// Tag auswählen
function selectDay(day) {
    selectedDay = day;
    updateTasks();
}

// Initialisierung
window.onload = () => {
    loadData();
    updateDateButtons();

    document.getElementById("today-button").onclick = () => selectDay("today");
    document.getElementById("tomorrow-button").onclick = () => selectDay("tomorrow");
    document.getElementById("day-after-button").onclick = () => selectDay("day_after");
    document.getElementById("add-task-button").onclick = addTask;
    document.getElementById("add-recurring-button").onclick = addRecurringTask;
};
