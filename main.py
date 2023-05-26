from datetime import datetime
from uuid import uuid4
import random
from loguru import logger
import threading

from tkinter import *
from tkinter import ttk

from api_adapter import HerculesController
from utils import *

MANAGER: HerculesController = None


def connect():
    host = host_box.get()
    user = user_box.get()
    password = password_box.get()

    global MANAGER
    MANAGER = HerculesController(host, user, password)
    bandwidth_box.insert(0, str(bytes_to_mbs(MANAGER.total_bandwidth)))
    starvation_box.insert(0, str(bytes_to_mbs(MANAGER.starvation_limit)))
    on_tick()
    logger.info("Connected successfully")


def display_processes(table, processes):
    for record in table["tree"].get_children():
        table["tree"].delete(record)

    table["count"] = 0
    for record in processes:
        if table["count"] % 2 == 0:
            table["tree"].insert(parent='', index='end', iid=table["count"], text="",
                                 values=(
                                     record["referenceId"],
                                     record["priority"],
                                     record["state"],
                                     record["bandwidth_str"],
                                     record["band_per"],
                                     record["namespace"],
                                     record["pid"]
                                 ),
                                 tags=('evenrow',))
        else:
            table["tree"].insert(parent='', index='end', iid=table["count"], text="",
                                 values=(
                                     record["referenceId"],
                                     record["priority"],
                                     record["state"],
                                     record["bandwidth_str"],
                                     record["band_per"],
                                     record["namespace"],
                                     record["pid"]
                                 ),
                                 tags=('oddrow',))
        table["count"] += 1


def update_total_bandwidth():
    global MANAGER
    input_bandwidth = float(bandwidth_box.get())
    MANAGER.update_total_bandwidth(mbs_to_bytes(input_bandwidth))


def update_starvation_limit():
    global MANAGER
    input_bandwidth = float(starvation_box.get())
    MANAGER.update_starvation_limit(mbs_to_bytes(input_bandwidth))


def display_metrics(metrics):
    global metrics_label
    metrics_label.config(text=metrics)


class BaseThread(threading.Thread):
    def __init__(self, callback=None, *args, **kwargs):
        target = kwargs.pop('target')
        super(BaseThread, self).__init__(target=self.target_with_callback, *args, **kwargs)
        self.callback = callback
        self.method = target

    def target_with_callback(self):
        self.method()
        if self.callback is not None:
            self.callback()


def threaded_bandwidth_request():
    global MANAGER
    ref_id = request_ref_box.get()
    priority = int(request_priority_box.get())
    namespace = request_namespace_box.get()

    t2 = threading.Thread(target=MANAGER.request_bandwidth, args=(ref_id, priority, namespace))
    t2.start()


def threaded_bandwidth_consume():
    global MANAGER
    ref_id = consume_ref_box.get()
    pv_pid = int(consume_pv_box.get())

    t3 = threading.Thread(target=MANAGER.consume_bandwidth, args=(ref_id, pv_pid))
    t3.start()


def threaded_bandwidth_release():
    global MANAGER
    ref_id = release_ref_box.get()

    t4 = threading.Thread(target=MANAGER.release_bandwidth, args=(ref_id,))
    t4.start()


def threaded_update():
    global MANAGER
    t1 = BaseThread(name="TT", target=MANAGER.fetch_data, callback=refresh_ui)
    t1.start()


def refresh_ui():
    display_processes(tables[0], MANAGER.get_waiting_process())
    display_processes(tables[1], MANAGER.get_running_process())
    display_processes(tables[2], MANAGER.get_finished_process())
    display_metrics(MANAGER.collect_metrics())
    root.after(250, on_tick)


def on_tick():
    global MANAGER
    if MANAGER:
        threaded_update()


root = Tk()
root.title('Demo backup process')

root.geometry("1920x1024")
# Add some style
style = ttk.Style()
# Pick a theme
# Configure our treeview colors

style.theme_use("default")
style.configure("Treeview",
                background="#D3D3D3",
                foreground="black",
                rowheight=25,
                fieldbackground="#D3D3D3"
                )
# Change selected color

style.map('Treeview',
          background=[('selected', 'blue')])
tables_frame = Frame(root)
tables_frame.grid(pady=20, row=0, column=1, rowspan=20)
Label(tables_frame, text="WAITING list").grid(row=0, column=0, pady=5)
Label(tables_frame, text="WORKING list").grid(row=2, column=0, pady=5)

Label(tables_frame, text="FINISHED list").grid(row=4, column=0, pady=5)
tables = []

for i in range(1, 6, 2):
    # Create Treeview Frame
    tree_frame = Frame(tables_frame)
    # tree_frame.pack(pady=20)
    tree_frame.grid(pady=20, padx=10, row=i, column=0)

    # Treeview Scrollbar
    tree_scroll = Scrollbar(tree_frame)
    tree_scroll.pack(side=RIGHT, fill=Y)

    # Create Treeview
    if i==3:
        my_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set, selectmode="extended", height=10)
    else:
        my_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set, selectmode="extended", height=8)

    # Pack to the screen
    my_tree.pack()

    # Configure the scrollbar
    tree_scroll.config(command=my_tree.yview)

    # Define Our Columns
    # my_tree['columns'] = ("PID", "Priority", "Bandwidth", "Transferred", "Progress")
    my_tree['columns'] = ("Ref_ID", "Priority", "State", "Bandwidth", "Band %", "Namespace", "PID")

    # Formate Our Columns
    my_tree.column("#0", width=0, stretch=NO)
    my_tree.column("Ref_ID", anchor=CENTER, width=320)
    my_tree.column("Priority", anchor=CENTER, width=40)
    my_tree.column("State", anchor=CENTER, width=170)
    my_tree.column("Bandwidth", anchor=CENTER, width=140)
    my_tree.column("Band %", anchor=CENTER, width=75)
    my_tree.column("Namespace", anchor=CENTER, width=140)
    my_tree.column("PID", anchor=CENTER, width=70)

    # Create Headings
    my_tree.heading("#0", text="", anchor=W)
    my_tree.heading("Ref_ID", text="Ref_ID", anchor=CENTER)
    my_tree.heading("Priority", text="Priority", anchor=CENTER)
    my_tree.heading("State", text="State", anchor=CENTER)
    my_tree.heading("Bandwidth", text="Bandwidth", anchor=CENTER)
    my_tree.heading("Band %", text="Band %", anchor=CENTER)
    my_tree.heading("Namespace", text="Namespace", anchor=CENTER)
    my_tree.heading("PID", text="PV_PID", anchor=CENTER)

    # Create striped row tags
    my_tree.tag_configure('oddrow', background="white")
    my_tree.tag_configure('evenrow', background="lightblue")

    tables.append({"tree": my_tree, "count": 0})
# Add Data
data = []

for _ in range(15):
    data.append(
        [
            str(uuid4()),
            random.randint(1, 8),
            random.choice(["WAITING", "STARTING", "RUNNING_WITHOUT_PID", "RUNNING", "FINISHED"]),
            f"{round(random.uniform(0.05, 99), 2)} Mb/s",
            f"{round(random.uniform(0.0, 100), 1)} %",
            random.choice(["PROTECTIONS", "REPLICATIONS", "DUMMY"]),
            random.randint(1000, 9999)
        ]
    )


def populate_from_data(table, records):
    table["count"] = 0
    for record in records:
        if table["count"] % 2 == 0:
            table["tree"].insert(parent='', index='end', iid=table["count"], text="", values=record, tags=('evenrow',))
        else:
            table["tree"].insert(parent='', index='end', iid=table["count"], text="", values=record, tags=('oddrow',))

        table["count"] += 1
# API config
api_config_frame = LabelFrame(root, text="SynetoOS 5.2 Node")
api_config_frame.grid(pady=20, padx=20, row=0, column=0)
Label(api_config_frame, text="Host: ").grid(row=0, column=0)
host_box = Entry(api_config_frame)
host_box.insert(0, "192.168.5.206")
host_box.grid(row=0, column=1)
Label(api_config_frame, text="User: ").grid(row=1, column=0)
user_box = Entry(api_config_frame)
user_box.grid(row=1, column=1)
Label(api_config_frame, text="Password: ").grid(row=2, column=0)
password_box = Entry(api_config_frame, show="*")
password_box.grid(row=2, column=1)
connect_btn = Button(api_config_frame, text="Connect", command=connect)
connect_btn.grid(pady=10, row=3, columnspan=2)

# Hercules config
hercules_config_frame = LabelFrame(root, text="Bandwidth Manager")
hercules_config_frame.grid(padx=10, pady=10, row=1, column=0)
Label(hercules_config_frame, text="Total bandwidth (Mb/s): ").grid(row=0, column=0)
bandwidth_box = Entry(hercules_config_frame)
bandwidth_box.grid(row=0, column=1)
update_total_bandwidth_btn = Button(hercules_config_frame, text="Update", command=update_total_bandwidth)
update_total_bandwidth_btn.grid(row=0, column=2, pady=5)
Label(hercules_config_frame, text="Minim starvation (Mb/s): ").grid(row=1, column=0)
starvation_box = Entry(hercules_config_frame)
starvation_box.grid(row=1, column=1)
update_total_starvation_btn = Button(hercules_config_frame, text="Update", command=update_starvation_limit)
update_total_starvation_btn.grid(row=1, column=2, pady=5)

lifecycle_frame = LabelFrame(root, text="Bandwidth lifecycle")
lifecycle_frame.grid(padx=10, pady=10, row=2, column=0)

# Request bandwidth
request_frame = LabelFrame(lifecycle_frame, text="Request bandwidth (create a new process)")
request_frame.grid(padx=40, pady=10, row=1, column=0)
Label(request_frame, text="Ref_ID: ").grid(row=0, column=0)
request_ref_box = Entry(request_frame)
request_ref_box.grid(row=0, column=1)
Label(request_frame, text="Priority (1-8): ").grid(row=1, column=0)
request_priority_box = Entry(request_frame)
request_priority_box.grid(row=1, column=1)
Label(request_frame, text="Namespace: ").grid(row=2, column=0)
request_namespace_box = Entry(request_frame)
request_namespace_box.grid(row=2, column=1)
request_btn = Button(request_frame, text="Request", command=threaded_bandwidth_request)
request_btn.grid(pady=10, row=3, columnspan=2)

# Consume bandwidth
consume_frame = LabelFrame(lifecycle_frame, text="Consume bandwidth (send PV pid)")
consume_frame.grid(padx=10, pady=10, row=2, column=0)
Label(consume_frame, text="Ref_ID: ").grid(row=0, column=0)
consume_ref_box = Entry(consume_frame, width=25)
consume_ref_box.grid(row=0, column=1)
Label(consume_frame, text="PV pid: ").grid(row=1, column=0)
consume_pv_box = Entry(consume_frame, width=25)
consume_pv_box.grid(row=1, column=1)
consume_btn = Button(consume_frame, text="Consume", command=threaded_bandwidth_consume)
consume_btn.grid(pady=10, row=2, columnspan=2)

# Release bandwidth
release_frame = LabelFrame(lifecycle_frame, text="Release bandwidth (finish process)")
release_frame.grid(padx=10, pady=10, row=3, column=0)
Label(release_frame, text="Ref_ID: ").grid(row=0, column=0)
release_ref_box = Entry(release_frame, width=25)
release_ref_box.grid(row=0, column=1)
release_btn = Button(release_frame, text="Release", command=threaded_bandwidth_release)
release_btn.grid(pady=10, row=2, columnspan=2)

# Metrics
metrics_frame = LabelFrame(root, text="Stats / Metrics")
metrics_frame.grid(padx=10, pady=10, row=3, column=0)
metrics_label = Label(metrics_frame, font="TkFixedFont", justify="left", width=50)
metrics_label.pack()


# populate_from_data(tables[0], data)
# populate_from_data(tables[1], data)
# populate_from_data(tables[2], data)

# root.after(1000, on_tick)
root.mainloop()
