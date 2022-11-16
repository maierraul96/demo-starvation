from datetime import datetime

from tkinter import *
from tkinter import ttk

from manager import BackupManager
from process import BackupProcess

MANAGER = BackupManager(10, 0.5)
LAST_TIMESTAMP = datetime.now()
PAUSED = False

root = Tk()
root.title('Demo backup process')
root.geometry("1920x480")

# Add some style
style = ttk.Style()
# Pick a theme
style.theme_use("default")
# Configure our treeview colors

style.configure("Treeview",
                background="#D3D3D3",
                foreground="black",
                rowheight=25,
                fieldbackground="#D3D3D3"
                )
# Change selected color
style.map('Treeview',
          background=[('selected', 'blue')])

Label(root, text="WAITING list").grid(row=0, column=0, pady=5)
Label(root, text="WORKING list").grid(row=0, column=1, pady=5)
Label(root, text="FINISHED list").grid(row=0, column=2, pady=5)

tables = []
for i in range(3):
    # Create Treeview Frame
    tree_frame = Frame(root)
    # tree_frame.pack(pady=20)
    tree_frame.grid(pady=20, padx=10, row=1, column=i)

    # Treeview Scrollbar
    tree_scroll = Scrollbar(tree_frame)
    tree_scroll.pack(side=RIGHT, fill=Y)

    # Create Treeview
    my_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set, selectmode="extended")

    # Pack to the screen
    my_tree.pack()

    # Configure the scrollbar
    tree_scroll.config(command=my_tree.yview)

    # Define Our Columns
    my_tree['columns'] = ("PID", "Priority", "Bandwidth", "Transferred", "Progress")

    # Formate Our Columns
    my_tree.column("#0", width=0, stretch=NO)
    my_tree.column("PID", anchor=W, width=40)
    my_tree.column("Priority", anchor=CENTER, width=45)
    my_tree.column("Bandwidth", anchor=CENTER, width=100)
    my_tree.column("Transferred", anchor=CENTER, width=150)
    my_tree.column("Progress", anchor=W, width=210)

    # Create Headings
    my_tree.heading("#0", text="", anchor=W)
    my_tree.heading("PID", text="PID", anchor=CENTER)
    my_tree.heading("Priority", text="Priority", anchor=CENTER)
    my_tree.heading("Bandwidth", text="Bandwidth", anchor=CENTER)
    my_tree.heading("Transferred", text="Transferred", anchor=CENTER)
    my_tree.heading("Progress", text="Progress", anchor=CENTER)

    # Create striped row tags
    my_tree.tag_configure('oddrow', background="white")
    my_tree.tag_configure('evenrow', background="lightblue")

    tables.append({"tree": my_tree, "count": 0})

# Add Data
data = [
    [101, 2, "12.5 Mb/s", "200 MB / 560 MB", "########## 100%"],
    [102, 4, "12 Mb/s", "200 MB / 560 MB", "####### 80%"],
    [103, 8, "30 Mb/s", "200 MB / 560 MB", "######### 90%"],
    [104, 1, "1.5 Mb/s", "200 MB / 560 MB", "▮" + "▯"*19 + " 10%"],
    [105, 5, "0.5 Mb/s", "200 MB / 560 MB", "▮"*20 + " 100%"],
]


def populate_from_data(table, records):
    table["count"] = 0
    for record in records:
        if table["count"] % 2 == 0:
            table["tree"].insert(parent='', index='end', iid=table["count"], text="", values=(record[0], record[1], record[2], record[3], record[4]),
                           tags=('evenrow',))
        else:
            table["tree"].insert(parent='', index='end', iid=table["count"], text="", values=(record[0], record[1], record[2], record[3], record[4]),
                           tags=('oddrow',))

        table["count"] += 1


configure_frame = Frame(root)
configure_frame.grid(pady=20, row=2, column=0)
Label(configure_frame, text="Total bandwidth (Mb/s)").grid(row=0, column=0)
Label(configure_frame, text="Min starvation limit (Mb/s)").grid(row=0, column=1)

bandwidth_box = Entry(configure_frame)
bandwidth_box.grid(row=1, column=0)
starvation_box = Entry(configure_frame)
starvation_box.grid(row=1, column=1)
bandwidth_box.insert(0, MANAGER.bandwidth)
starvation_box.insert(0, MANAGER.starvation_limit)


add_frame = Frame(root)
add_frame.grid(pady=20, row=2, column=1)

# Labels
Label(add_frame, text="Size (MB)").grid(row=0, column=0)
Label(add_frame, text="Priority (1-8)").grid(row=0, column=1)

# Entry boxes
size_box = Entry(add_frame)
size_box.grid(row=1, column=0)

priority_box = Entry(add_frame)
priority_box.grid(row=1, column=1)


# Add Record
def add_process():
    new_process = BackupProcess(int(size_box.get()), int(priority_box.get()))
    print(f"INFO New process added with PID={new_process.pid}")
    MANAGER.add_new_process(new_process)

    # Clear the boxes
    size_box.delete(0, END)
    priority_box.delete(0, END)


def configure():
    MANAGER.bandwidth = float(bandwidth_box.get())
    MANAGER.starvation_limit = float(starvation_box.get())
    print(f"INFO Manager successfully configured with TOTAL_BANDWIDTH={MANAGER.bandwidth}Mb/s and MIN_STARVATION_LIMIT={MANAGER.starvation_limit}Mb/s")
    MANAGER.update()


def display_processes(table, processes):
    for record in table["tree"].get_children():
        table["tree"].delete(record)

    table["count"] = 0
    for record in processes:
        if table["count"] % 2 == 0:
            table["tree"].insert(parent='', index='end', iid=table["count"], text="",
                                 values=(
                                     record.pid,
                                     record.priority,
                                     f"{record.speed:.2f} Mb/s",
                                     f"{record.transferred_size:.1f} MB / {record.size} MB",
                                     record.compute_progress(),
                                 ),
                                 tags=('evenrow',))
        else:
            table["tree"].insert(parent='', index='end', iid=table["count"], text="",
                                 values=(
                                     record.pid,
                                     record.priority,
                                     f"{record.speed:.2f} Mb/s",
                                     f"{record.transferred_size:.1f} MB / {record.size} MB",
                                     record.compute_progress(),
                                 ),
                                 tags=('oddrow',))
        table["count"] += 1


def pause():
    global PAUSED

    if not PAUSED:
        PAUSED = True
        pause_btn.config(text="PLAY")
    else:
        PAUSED = False
        pause_btn.config(text="PAUSE")
    print(f"INFO PAUSED = {PAUSED}")


def on_tick():
    global LAST_TIMESTAMP, PAUSED
    now = datetime.now()
    if not PAUSED:
        MANAGER.new_tick(now - LAST_TIMESTAMP)
    display_processes(tables[0], MANAGER.waiting_list)
    display_processes(tables[1], MANAGER.working_list)
    display_processes(tables[2], MANAGER.finished_list)
    LAST_TIMESTAMP = now
    root.after(250, on_tick)


# Buttons
add_process = Button(add_frame, text="Add process", command=add_process)
add_process.grid(pady=10, row=2, columnspan=2)

configure_btn = Button(configure_frame, text="Configure",  command=configure)
configure_btn.grid(pady=10, row=2, columnspan=2)

pause_btn = Button(root, text="PAUSE", command=pause, width=10, height=5)
pause_btn.grid(pady=10, row=2, column=2)


root.after(250, on_tick)
root.mainloop()
