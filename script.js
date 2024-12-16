const SERVER_URL = "http://45.133.9.62:5000/api";

let tasks = { today: [], tomorrow: [], day_after: [] };
let points = 0;
let inventory = [];
let recurringTasks = [];
let redemptionHistory = {};
let selectedDay = "today";

// Fetch data from the server
async function loadData() {
    try {
        const response = await fetch(`${SERVER_URL}/get_json`);
        const data = await response.json();

        tasks = data.tasks || tasks;
        points = data.points || 0;
        inventory = data.inventory || [];
        recurringTasks = data.recurring_tasks || [];
        redemptionHistory = data.redemption_history || {};

        updateUI();
        updateDateButtons();
    } catch (error) {
        console.error("Error loading data:", error);
    }
}

// Save data to the server
async function saveData() {
    try {
        const data = { tasks, points, inventory, recurring_tasks: recurringTasks, redemption_history: redemptionHistory };
        await fetch(`${SERVER_URL}/update_json`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
    } catch (error) {
        console.error("Error saving data:", error);
    }
}

// Update the date buttons with labels and dates
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

// Update the points display
function updatePoints() {
    document.getElementById("points-display").textContent = `Points: ${points}`;
}

// Update tasks for the selected day
function updateTasks() {
    const tasksList = document.getElementById("tasks-list");
    tasksList.innerHTML = "";

    tasks[selectedDay].forEach((task, index) => {
        const taskItem = document.createElement("div");
        taskItem.className = "task-box";

        const taskText = document.createElement("span");
        taskText.textContent = task.completed ? `[x] ${task.name}` : `[ ] ${task.name}`;
        taskText.onclick = () => toggleTask(index);

        const deleteButton = document.createElement("button");
        deleteButton.textContent = "Delete";
        deleteButton.className = "delete-button";
        deleteButton.onclick = () => deleteTask(index);

        taskItem.appendChild(taskText);
        taskItem.appendChild(deleteButton);
        tasksList.appendChild(taskItem);
    });
}

// Toggle task completion
function toggleTask(index) {
    tasks[selectedDay][index].completed = !tasks[selectedDay][index].completed;
    points += tasks[selectedDay][index].completed ? 5 : -5;
    updatePoints();
    updateTasks();
    saveData();
}

// Add a task
function addTask() {
    const taskInput = document.getElementById("new-task");
    const taskName = taskInput.value.trim();
    if (taskName) {
        tasks[selectedDay].push({ name: taskName, completed: false });
        taskInput.value = "";
        updateTasks();
        saveData();
    }
}

// Delete a task
function deleteTask(index) {
    tasks[selectedDay].splice(index, 1);
    updateTasks();
    saveData();
}

// Update shop items
function updateShop() {
    const shopList = document.getElementById("shop-list");
    shopList.innerHTML = "";

    const rewards = [
        {"name": "Red Bull", "cost": 15},
        {"name": "Placeholder", "cost": 15},
        {"name": "Placeholder", "cost": 30},
        {"name": "Placeholder", "cost": 50},
        {"name": "1 Snus kaufen", "cost": 100},
        {"name": "5 Snus kaufen", "cost": 500}
    ];

    rewards.forEach((reward) => {
        const rewardButton = document.createElement("button");
        rewardButton.textContent = `${reward.name} - ${reward.cost} Points`;
        rewardButton.className = "shop-button";
        rewardButton.onclick = () => redeemReward(reward);
        shopList.appendChild(rewardButton);
    });
}

// Redeem a reward
function redeemReward(reward) {
    if (points >= reward.cost) {
        points -= reward.cost;
        inventory.push(reward.name);
        updatePoints();
        updateInventory();
        saveData();
    } else {
        alert("Not enough points!");
    }
}

// Update inventory
function updateInventory() {
    const inventoryList = document.getElementById("inventory-list");
    inventoryList.innerHTML = "";

    inventory.forEach((item) => {
        const itemDiv = document.createElement("div");
        itemDiv.textContent = item;
        inventoryList.appendChild(itemDiv);
    });

    const redemptionHistoryList = document.getElementById("redemption-history");
    redemptionHistoryList.innerHTML = "";

    Object.entries(redemptionHistory).forEach(([item, count]) => {
        const historyDiv = document.createElement("div");
        historyDiv.textContent = `${item}: ${count}x redeemed`;
        redemptionHistoryList.appendChild(historyDiv);
    });
}

// Update UI elements
function updateUI() {
    updatePoints();
    updateTasks();
    updateShop();
    updateInventory();
}

// Select a specific day
function selectDay(day) {
    selectedDay = day;
    updateTasks();
}

// On page load
window.onload = () => {
    loadData();
    updateDateButtons();
};
