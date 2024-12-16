import json
import requests
import time
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# Server-URL
SERVER_URL = "http://45.133.9.62:5000"

# Globale Variablen
tasks = {"today": [], "tomorrow": [], "day_after": []}
points = 0
inventory = []
recurring_tasks = []
redemption_history = {}
completed_recurring_tasks = {"today": [], "tomorrow": [], "day_after": []}

# Farben für Darkmode
BG_COLOR = "#121212"
FG_COLOR = "#ffffff"
BTN_COLOR = "#1f1f1f"


# Hilfsfunktion: JSON-Daten mit Wiederholung laden
def fetch_json_with_retry(url, retries=3, delay=2):
    for attempt in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except (json.JSONDecodeError, requests.RequestException) as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e

# Daten vom Server laden
rewards = []  # Globale Variable für Rewards

def download_from_server():
    global tasks, points, inventory, recurring_tasks, redemption_history, completed_recurring_tasks, rewards
    try:
        data = fetch_json_with_retry(f"{SERVER_URL}/api/get_json")
        tasks = data.get("tasks", {"today": [], "tomorrow": [], "day_after": []})
        points = data.get("points", 0)
        inventory = data.get("inventory", [])
        recurring_tasks = data.get("recurring_tasks", [])
        redemption_history = data.get("redemption_history", {})
        completed_recurring_tasks = data.get("completed_recurring_tasks", {"today": [], "tomorrow": [], "day_after": []})
        rewards = data.get("rewards", [])
    except Exception as e:
        messagebox.showerror("Fehler beim Herunterladen", f"Fehler: {str(e)}")


def upload_to_server():
    try:
        data = {
            "tasks": tasks,
            "points": points,
            "inventory": inventory,
            "recurring_tasks": recurring_tasks,
            "redemption_history": redemption_history,
            "completed_recurring_tasks": completed_recurring_tasks
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(f"{SERVER_URL}/api/update_json", json=data, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Fehler beim Hochladen: {response.status_code} - {response.text}")
    except Exception as e:
        messagebox.showerror("Fehler beim Upload", str(e))

# Aufgabenverwaltung
def toggle_task(index, day):
    """Schaltet den Status einer Aufgabe um und aktualisiert die Punkte."""
    global points
    task = tasks[day][index]
    task["completed"] = not task["completed"]
    points += 5 if task["completed"] else -5

def toggle_recurring_task(name, day):
    """Markiert eine wiederkehrende Aufgabe als abgeschlossen."""
    if name not in completed_recurring_tasks[day]:
        completed_recurring_tasks[day].append(name)
        global points
        points += 5

# Unerledigte Aufgaben aktualisieren
def update_uncompleted_tasks():
    """Sammelt alle unerledigten Aufgaben aus allen Tagen."""
    uncompleted = []
    for day_key, day_tasks in tasks.items():
        for task in day_tasks:
            if not task["completed"]:
                uncompleted.append({"name": task["name"], "day": day_key})
    return uncompleted

# Inventar und Belohnungen
def redeem_reward(reward):
    """Belohnung einlösen, wenn genügend Punkte vorhanden sind."""
    global points, inventory
    if points >= reward["cost"]:
        points -= reward["cost"]
        inventory.append(reward["name"])
    else:
        messagebox.showwarning("Zu wenig Punkte", "Nicht genug Punkte!")

def redeem_inventory_item(item_name):
    """Ein Item aus dem Inventar einlösen."""
    if item_name in inventory:
        inventory.remove(item_name)
        redemption_history[item_name] = redemption_history.get(item_name, 0) + 1
        messagebox.showinfo("Einlösen", f"'{item_name}' wurde eingelöst!")

# Wiederkehrende Aufgaben
def add_recurring_task(task_name):
    """Fügt eine neue wiederkehrende Aufgabe hinzu."""
    recurring_tasks.append({"name": task_name})

def delete_recurring_task(task_name):
    """Entfernt eine wiederkehrende Aufgabe."""
    global recurring_tasks
    recurring_tasks = [task for task in recurring_tasks if task["name"] != task_name]

# Datenbank-Initialisierung
download_from_server()


# Starte die App (Rest des Codes bleibt gleich)

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
    """Speichert die Daten direkt auf dem Server."""
    upload_to_server()

def load_data():
    """Lädt die Daten direkt vom Server."""
    download_from_server()

load_data()

# Globale Variable für ausgewählten Tag
selected_day = "today"

# SystemTray-Funktionen
def create_image():
    image = Image.new("RGB", (64, 64), "black")
    dc = ImageDraw.Draw(image)
    dc.rectangle([16, 16, 48, 48], fill="white")
    return image



def add_task():
    task_name = task_entry.get().strip()
    if task_name:
        tasks[selected_day].append({"name": task_name, "completed": False})
        update_task_list()
        task_entry.delete(0, tk.END)
        upload_to_server()  # Änderungen sofort synchronisieren


def delete_task():
    selected = task_list.curselection()
    if selected:
        tasks[selected_day].pop(selected[0])
        update_task_list()
        save_data()

def toggle_task(index):
    global points
    task = tasks[selected_day][index]
    task["completed"] = not task["completed"]
    points += 5 if task["completed"] else -5
    update_task_list()
    update_points()
    upload_to_server()  # Änderungen sofort synchronisieren


def update_task_list():
    """Aktualisiert die Aufgabenliste basierend auf dem ausgewählten Tag."""
    # Liste löschen, um sicherzustellen, dass keine alten Einträge vorhanden sind
    task_list.delete(0, tk.END)
    root.update_idletasks()  # Erzwinge sofortige visuelle Aktualisierung

    # Reguläre Aufgaben in die Liste einfügen
    for task in tasks[selected_day]:
        status = "[x] " if task["completed"] else "[ ] "
        task_list.insert(tk.END, status + task["name"])

    # Wiederkehrende Aufgaben hinzufügen
    for task in recurring_tasks:
        if task["name"] not in completed_recurring_tasks[selected_day]:
            task_list.insert(tk.END, "[ ] " + task["name"])

    # Sicherstellen, dass keine weiteren Renderings ausstehen
    root.update_idletasks()

def reload_data():
    download_from_server()  # Neueste Daten abrufen
    update_task_list()  # Aufgabenliste aktualisieren
    update_inventory()  # Inventar aktualisieren
    update_points()  # Punkte aktualisieren

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
    """Aktualisiert die Aufgabenliste basierend auf dem ausgewählten Tag."""
    task_list.delete(0, tk.END)  # Alle bestehenden Einträge löschen

    # Reguläre Aufgaben in die Liste einfügen
    for task in tasks[selected_day]:
        status = "[x] " if task["completed"] else "[ ] "
        task_list.insert(tk.END, status + task["name"])

    # Wiederkehrende Aufgaben in die Liste einfügen
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
        upload_to_server()  # Änderungen sofort synchronisieren
    else:
        messagebox.showwarning("Zu wenig Punkte", "Nicht genug Punkte!")


def update_inventory():
    inventory_list.delete(0, tk.END)
    for item in inventory:
        inventory_list.insert(tk.END, item)

def update_redemption_history():
    redemption_list.delete(0, tk.END)  # Listbox leeren
    for item, count in redemption_history.items():
        redemption_list.insert(tk.END, f"{item}: {count}x eingelöst")


def redeem_inventory_item():
    selected = inventory_list.curselection()
    if selected:
        item_name = inventory.pop(selected[0])  # Item aus dem Inventar entfernen
        redemption_history[item_name] = redemption_history.get(item_name, 0) + 1  # History aktualisieren
        update_inventory()  # Inventar aktualisieren
        update_redemption_history()  # Anzeige aktualisieren
        save_data()  # Daten speichern
        messagebox.showinfo("Einlösen", f"'{item_name}' wurde eingelöst!")


# Hauptfenster
root = tk.Tk()
root.title("To-Do App")
root.geometry("500x450")  # Kompaktes Fenster
root.configure(bg=BG_COLOR)

# Darkmode für Tabs
style = ttk.Style()
style.theme_use("default")
style.configure("TNotebook", background=BG_COLOR)
style.configure("TNotebook.Tab", background=BTN_COLOR, foreground=FG_COLOR, padding=[5, 2])
style.map("TNotebook.Tab", background=[("selected", "#333333")], foreground=[("selected", "#ffffff")])

# Tabs
notebook = ttk.Notebook(root)
notebook.pack(expand=1, fill="both", padx=5, pady=5)

# Funktion: Tag auswählen
selected_day = "today"

def select_day(day_key):
    """Wechselt den ausgewählten Tag und aktualisiert die Aufgabenliste."""
    global selected_day
    selected_day = day_key
    update_task_list()

# Tab 1: Tasks
calendar_tab = tk.Frame(notebook, bg=BG_COLOR)
notebook.add(calendar_tab, text="Tasks")

# Header
tk.Label(calendar_tab, text="Tasks", font=("Arial", 14, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(pady=5)

# Tagesauswahl
day_frame = tk.Frame(calendar_tab, bg=BG_COLOR)
day_frame.pack(pady=5)
date_labels = get_date_labels()
for i, day_key in enumerate(["today", "tomorrow", "day_after"]):
    tk.Button(
        day_frame,
        text=date_labels[i],
        command=lambda d=day_key: select_day(d),
        bg="#444444",
        fg=FG_COLOR,
        font=("Arial", 10),
        width=12,
        relief="flat"
    ).pack(side=tk.LEFT, padx=5)

# Aufgabenliste
task_list = tk.Listbox(calendar_tab, width=40, height=8, bg=BTN_COLOR, fg=FG_COLOR, font=("Arial", 10))
task_list.pack(pady=5)

# Buttons für Aufgaben
button_frame = tk.Frame(calendar_tab, bg=BG_COLOR)
button_frame.pack(pady=5)
tk.Button(button_frame, text="➕ Add", command=add_task, bg="#555555", fg=FG_COLOR, font=("Arial", 10), relief="flat").pack(side=tk.LEFT, padx=5)
tk.Button(button_frame, text="❌ Delete", command=delete_task, bg="#555555", fg=FG_COLOR, font=("Arial", 10), relief="flat").pack(side=tk.LEFT, padx=5)
tk.Button(button_frame, text="🔄 Refresh", command=reload_data, bg="#555555", fg=FG_COLOR, font=("Arial", 10), relief="flat").pack(side=tk.LEFT, padx=5)

# Punkte-Anzeige
points_label = tk.Label(calendar_tab, text=f"Points: {points}", bg=BG_COLOR, fg="#FFD700", font=("Arial", 12, "bold"))
points_label.pack(pady=5)

# Eingabefeld für Aufgaben
task_entry = tk.Entry(calendar_tab, width=30, bg=BTN_COLOR, fg=FG_COLOR, font=("Arial", 10))
task_entry.pack(pady=5)

# Tab 2: Uncompleted Tasks
uncompleted_tab = tk.Frame(notebook, bg=BG_COLOR)
notebook.add(uncompleted_tab, text="Uncompleted")
tk.Label(uncompleted_tab, text="Uncompleted Tasks", font=("Arial", 14, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(pady=5)
uncompleted_list = tk.Listbox(uncompleted_tab, width=40, height=10, bg=BTN_COLOR, fg=FG_COLOR, font=("Arial", 10))
uncompleted_list.pack(pady=5)
tk.Button(uncompleted_tab, text="🔄 Refresh", command=update_uncompleted_list, bg="#555555", fg=FG_COLOR, font=("Arial", 10), relief="flat").pack(pady=5)

# Tab 3: Recurring Tasks
recurring_tab = tk.Frame(notebook, bg=BG_COLOR)
notebook.add(recurring_tab, text="Recurring")
tk.Label(recurring_tab, text="Recurring Tasks", font=("Arial", 14, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(pady=5)
recurring_task_list = tk.Listbox(recurring_tab, width=40, height=10, bg=BTN_COLOR, fg=FG_COLOR, font=("Arial", 10))
recurring_task_list.pack(pady=5)
recurring_entry = tk.Entry(recurring_tab, width=30, bg=BTN_COLOR, fg=FG_COLOR, font=("Arial", 10))
recurring_entry.pack(pady=5)
tk.Button(recurring_tab, text="➕ Add", command=add_recurring_task, bg="#555555", fg=FG_COLOR, font=("Arial", 10), relief="flat").pack(pady=5)
tk.Button(recurring_tab, text="❌ Delete", command=delete_recurring_task, bg="#555555", fg=FG_COLOR, font=("Arial", 10), relief="flat").pack(pady=5)

# Tab 4: Shop
shop_tab = tk.Frame(notebook, bg=BG_COLOR)
notebook.add(shop_tab, text="Shop")
tk.Label(shop_tab, text="Shop", font=("Arial", 14, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(pady=5)
for reward in rewards:
    tk.Button(
        shop_tab,
        text=f"{reward['name']} - {reward['cost']} Points",
        command=lambda r=reward: redeem_reward(r),
        bg="#444444",
        fg=FG_COLOR,
        font=("Arial", 10),
        width=25,
        relief="flat"
    ).pack(pady=3)

# Tab 5: Inventory
inventory_tab = tk.Frame(notebook, bg=BG_COLOR)
notebook.add(inventory_tab, text="Inventory")
tk.Label(inventory_tab, text="Inventory", font=("Arial", 14, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(pady=5)
inventory_list = tk.Listbox(inventory_tab, width=40, height=8, bg=BTN_COLOR, fg=FG_COLOR, font=("Arial", 10))
inventory_list.pack(pady=5)
tk.Button(inventory_tab, text="✅ Use", command=redeem_inventory_item, bg="#555555", fg=FG_COLOR, font=("Arial", 10), relief="flat").pack(pady=5)
tk.Label(inventory_tab, text="History:", bg=BG_COLOR, fg=FG_COLOR, font=("Arial", 12, "bold")).pack(pady=5)
redemption_list = tk.Listbox(inventory_tab, width=40, height=8, bg=BTN_COLOR, fg=FG_COLOR, font=("Arial", 10))
redemption_list.pack(pady=5)

# Starte die App
root.mainloop()
