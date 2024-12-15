import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import json
import os
from pystray import Icon as icon, MenuItem as item, Menu
from PIL import Image, ImageDraw

# JSON-Dateipfad
DATA_FILE = "todo_data.json"

# Datenstrukturen
tasks = {"today": [], "tomorrow": [], "day_after": []}
points = 0
rewards = [
    {"name": "Red Bull", "cost": 15},
    {"name": "Placeholder", "cost": 15},
    {"name": "Placeholder", "cost": 30},
    {"name": "Placeholder", "cost": 50},
    {"name": "1 Snus kaufen", "cost": 100},
    {"name": "5 Snus kaufen", "cost": 500}
]
inventory = []
recurring_tasks = []
redemption_history = {}
completed_recurring_tasks = {"today": [], "tomorrow": [], "day_after": []}  # Status für abgehakte wiederkehrende Aufgaben

# Farben für Darkmode
BG_COLOR = "#121212"
FG_COLOR = "#ffffff"
BTN_COLOR = "#1f1f1f"

# Hilfsfunktionen für Datumsberechnung
def get_date_labels():
    today = datetime.now()
    return [
        today.strftime("%A - %d.%m"),
        (today + timedelta(days=1)).strftime("%A - %d.%m"),
        (today + timedelta(days=2)).strftime("%A - %d.%m")
    ]

# Datenbank-Funktionen
def save_data():
    with open(DATA_FILE, "w") as file:
        json.dump({
            "tasks": tasks,
            "points": points,
            "inventory": inventory,
            "recurring_tasks": recurring_tasks,
            "redemption_history": redemption_history,
            "completed_recurring_tasks": completed_recurring_tasks
        }, file)

def load_data():
    global tasks, points, inventory, recurring_tasks, redemption_history, completed_recurring_tasks
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            data = json.load(file)
            tasks.update(data.get("tasks", tasks))
            points = data.get("points", 0)
            inventory.extend(data.get("inventory", []))
            recurring_tasks.extend(data.get("recurring_tasks", []))
            redemption_history.update(data.get("redemption_history", {}))
            completed_recurring_tasks.update(data.get("completed_recurring_tasks", completed_recurring_tasks))

# Globale Variable für ausgewählten Tag
selected_day = "today"

# SystemTray-Funktionen
def create_image():
    image = Image.new("RGB", (64, 64), "black")
    dc = ImageDraw.Draw(image)
    dc.rectangle([16, 16, 48, 48], fill="white")
    return image

def minimize_to_tray():
    root.withdraw()
    tray_icon = icon("To-Do App", create_image(), menu=Menu(item("Öffnen", restore_window), item("Beenden", exit_app)))
    tray_icon.run()

def restore_window(icon, item):
    icon.stop()
    root.deiconify()

def exit_app(icon, item):
    icon.stop()
    save_data()
    root.destroy()

# Aufgaben-Funktionen
def add_task():
    task_name = task_entry.get().strip()
    if task_name:
        tasks[selected_day].append({"name": task_name, "completed": False})
        update_task_list()
        task_entry.delete(0, tk.END)
        save_data()

def delete_task():
    selected = task_list.curselection()
    if selected:
        tasks[selected_day].pop(selected[0])
        update_task_list()
        save_data()

def toggle_task(index):
    global points
    task = tasks[selected_day][index]
    if not task["completed"]:
        task["completed"] = True
        points += 5
    update_task_list()
    update_points()
    save_data()

def update_task_list():
    task_list.delete(0, tk.END)

    # Reguläre Aufgaben in die Liste einfügen
    for i, task in enumerate(tasks[selected_day]):
        status = "[x] " if task["completed"] else "[ ] "
        task_list.insert(tk.END, status + task["name"])

    # Wiederkehrende Aufgaben hinzufügen, wenn sie nicht abgehakt sind
    for task in recurring_tasks:
        if task["name"] not in completed_recurring_tasks[selected_day]:
            task_list.insert(tk.END, "[ ] " + task["name"])

    # Doppelklick-Event für reguläre und wiederkehrende Aufgaben
    def toggle_combined_task(event):
        selected = task_list.curselection()
        if selected:
            index = selected[0]
            if index < len(tasks[selected_day]):  # Reguläre Aufgabe
                toggle_task(index)
            else:  # Wiederkehrende Aufgabe
                task_index = index - len(tasks[selected_day])
                recurring_task_name = recurring_tasks[task_index]["name"]
                completed_recurring_tasks[selected_day].append(recurring_task_name)
                global points
                points += 5
                update_task_list()
                update_points()
                save_data()

    task_list.bind("<Double-1>", toggle_combined_task)

def update_points():
    points_label.config(text=f"Punkte: {points}")

def update_task_list():
    task_list.delete(0, tk.END)

    # Reguläre Aufgaben in die Liste einfügen
    for i, task in enumerate(tasks[selected_day]):
        status = "[x] " if task["completed"] else "[ ] "
        task_list.insert(tk.END, status + task["name"])

    # Wiederkehrende Aufgaben in die Liste einfügen
    for i, task in enumerate(recurring_tasks):
        is_completed = task["name"] in completed_recurring_tasks[selected_day]
        status = "[x] " if is_completed else "[ ] "
        task_list.insert(tk.END, status + task["name"])

    # Doppelklick-Event für reguläre und wiederkehrende Aufgaben
    def toggle_combined_task(event):
        selected = task_list.curselection()
        if selected:
            index = selected[0]
            if index < len(tasks[selected_day]):  # Reguläre Aufgabe
                toggle_task(index)
            else:  # Wiederkehrende Aufgabe
                recurring_index = index - len(tasks[selected_day])
                recurring_task_name = recurring_tasks[recurring_index]["name"]
                if recurring_task_name not in completed_recurring_tasks[selected_day]:
                    completed_recurring_tasks[selected_day].append(recurring_task_name)
                    global points
                    points += 5
                    update_points()
                    save_data()
                update_task_list()

    task_list.bind("<Double-1>", toggle_combined_task)


# Wiederkehrende Aufgaben
def add_recurring_task():
    task_name = recurring_entry.get().strip()
    if task_name:
        recurring_tasks.append({"name": task_name})
        update_recurring_task_list()
        recurring_entry.delete(0, tk.END)
        save_data()

def delete_recurring_task():
    selected = recurring_task_list.curselection()
    if selected:
        recurring_tasks.pop(selected[0])
        update_recurring_task_list()
        save_data()

def update_recurring_task_list():
    recurring_task_list.delete(0, tk.END)
    for task in recurring_tasks:
        recurring_task_list.insert(tk.END, task["name"])

# Unerledigte Aufgaben
def update_uncompleted_list():
    uncompleted_list.delete(0, tk.END)
    for day_key, day_tasks in tasks.items():
        for task in day_tasks:
            if not task["completed"]:
                uncompleted_list.insert(tk.END, f"{task['name']} ({day_key})")

def redeem_reward(reward):
    global points
    if points >= reward["cost"]:
        points -= reward["cost"]
        inventory.append(reward["name"])
        update_points()
        update_inventory()
        save_data()
    else:
        messagebox.showwarning("Zu wenig Punkte", "Nicht genug Punkte!")

def update_inventory():
    inventory_list.delete(0, tk.END)
    for item in inventory:
        inventory_list.insert(tk.END, item)

def update_redemption_history():
    redemption_list.delete(0, tk.END)
    for item, count in redemption_history.items():
        redemption_list.insert(tk.END, f"{item}: {count}x eingelöst")

def redeem_inventory_item():
    selected = inventory_list.curselection()
    if selected:
        item_name = inventory.pop(selected[0])
        redemption_history[item_name] = redemption_history.get(item_name, 0) + 1
        update_inventory()
        update_redemption_history()
        save_data()
        messagebox.showinfo("Einlösen", f"'{item_name}' wurde eingelöst!")

# Hauptfenster
root = tk.Tk()
root.title("To-Do App")
root.geometry("500x450")
root.configure(bg=BG_COLOR)

# Darkmode für Tabs
style = ttk.Style()
style.theme_use("default")
style.configure("TNotebook", background=BG_COLOR)
style.configure("TNotebook.Tab", background=BTN_COLOR, foreground=FG_COLOR, padding=[5, 2])
style.map("TNotebook.Tab", background=[("selected", BTN_COLOR)], foreground=[("selected", FG_COLOR)])

# Tabs
notebook = ttk.Notebook(root)
notebook.pack(expand=1, fill="both")

# Tab 1: Kalender & Aufgaben
calendar_tab = tk.Frame(notebook, bg=BG_COLOR)
notebook.add(calendar_tab, text="Kalender & Aufgaben")
date_labels = get_date_labels()
day_frame = tk.Frame(calendar_tab, bg=BG_COLOR)
day_frame.pack()

for i, day_key in enumerate(["today", "tomorrow", "day_after"]):
    tk.Button(day_frame, text=date_labels[i], command=lambda d=day_key: select_day(d),
              bg=BTN_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, padx=5)

def select_day(day_key):
    global selected_day
    selected_day = day_key
    update_task_list()

task_entry = tk.Entry(calendar_tab, width=30, bg=BTN_COLOR, fg=FG_COLOR)
task_entry.pack()
task_list = tk.Listbox(calendar_tab, width=50, height=10, bg=BTN_COLOR, fg=FG_COLOR)
task_list.pack()
tk.Button(calendar_tab, text="Hinzufügen", command=add_task, bg=BTN_COLOR, fg=FG_COLOR).pack()
tk.Button(calendar_tab, text="Löschen", command=delete_task, bg=BTN_COLOR, fg=FG_COLOR).pack()
points_label = tk.Label(calendar_tab, text=f"Punkte: {points}", bg=BG_COLOR, fg=FG_COLOR)
points_label.pack()

# Tab 2: Unerledigte Aufgaben
uncompleted_tab = tk.Frame(notebook, bg=BG_COLOR)
notebook.add(uncompleted_tab, text="Unerledigt")
uncompleted_list = tk.Listbox(uncompleted_tab, width=50, height=15, bg=BTN_COLOR, fg=FG_COLOR)
uncompleted_list.pack()
tk.Button(uncompleted_tab, text="Aktualisieren", command=update_uncompleted_list, bg=BTN_COLOR, fg=FG_COLOR).pack()

# Tab 3: Wiederkehrende Aufgaben
recurring_tab = tk.Frame(notebook, bg=BG_COLOR)
notebook.add(recurring_tab, text="Wiederkehrend")
recurring_entry = tk.Entry(recurring_tab, width=30, bg=BTN_COLOR, fg=FG_COLOR)
recurring_entry.pack()
tk.Button(recurring_tab, text="Hinzufügen", command=add_recurring_task, bg=BTN_COLOR, fg=FG_COLOR).pack()
recurring_task_list = tk.Listbox(recurring_tab, width=50, height=15, bg=BTN_COLOR, fg=FG_COLOR)
recurring_task_list.pack()
tk.Button(recurring_tab, text="Löschen", command=delete_recurring_task, bg=BTN_COLOR, fg=FG_COLOR).pack()

# Tab 4: Shop
shop_tab = tk.Frame(notebook, bg=BG_COLOR)
notebook.add(shop_tab, text="Shop")
for reward in rewards:
    tk.Button(shop_tab, text=f"{reward['name']} - {reward['cost']} Punkte", command=lambda r=reward: redeem_reward(r),
              bg=BTN_COLOR, fg=FG_COLOR).pack()

# Tab 5: Inventar & Verlauf
inventory_tab = tk.Frame(notebook, bg=BG_COLOR)
notebook.add(inventory_tab, text="Inventar")
inventory_list = tk.Listbox(inventory_tab, width=50, height=8, bg=BTN_COLOR, fg=FG_COLOR)
inventory_list.pack()
tk.Button(inventory_tab, text="Einlösen", command=redeem_inventory_item, bg=BTN_COLOR, fg=FG_COLOR).pack()
tk.Label(inventory_tab, text="Verlauf:", bg=BG_COLOR, fg=FG_COLOR).pack(pady=5)
redemption_list = tk.Listbox(inventory_tab, width=50, height=8, bg=BTN_COLOR, fg=FG_COLOR)
redemption_list.pack()

# Lade Daten und starte App
load_data()
update_task_list()
update_recurring_task_list()
update_inventory()
update_redemption_history()
update_points()
root.protocol("WM_DELETE_WINDOW", minimize_to_tray)
root.mainloop()
