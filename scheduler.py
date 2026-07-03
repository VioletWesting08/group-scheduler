from tkinter import *
from tkinter import filedialog
import pickle
from math import log
from matplotlib import colormaps

from ics_utils import parse_recurring_busy_slots
from schedule_data import initialize_schedule_data

def init(data):
    data.margin = 30
    data.left_margin = 75
    initialize_schedule_data(data)
    data.cell_width = (data.width-data.left_margin-data.margin)//data.rows
    data.cell_height = (data.height-data.margin)//data.cols
    data.availability_locked = False
    data.hover_cell = None
    data.locked_cell = None
    data.cmap = colormaps['RdYlGn']
    create_menu(data)
    create_list(data)
    create_availability_panel(data)
    create_buttons(data)
    redraw_root(data.canvas, data)


# converts (0, 1) rgb values to hex
def norm_rgb_to_hex(r, g, b, a=None):
    return "#{:02x}{:02x}{:02x}".format(int(255*r), int(255*g), int(255*b))

# distributes colors nicely across possible availability fractions
def get_color_fraction(x, n):
    exp = 1 if n < 2 else log(n, 2)
    frac = 0.0 if n == 0 else x/n
    return max(0.02, (frac**exp))

#---------#
# Menubar #
#---------#
# create group + view + theme menus in the menubar
def create_menu(data):
    data.menubar = Menu(data.root)
    data.menu_groups = Menu(data.menubar)
    data.menubar.add_cascade(menu=data.menu_groups, label='Groups')
    theme_menu = Menu(data.menubar)
    for theme in sorted(colormaps):
        theme_menu.add_command(label=theme,
                               command=lambda theme=theme: set_theme(data, theme))
    data.menubar.add_cascade(menu=theme_menu, label='Theme')
    data.root.config(menu=data.menubar)

# change color scheme
def set_theme(data, theme):
    data.cmap = colormaps[theme]
    redraw_root(data.canvas, data)

# restricts selection to desired group
def select_group(data, name):
    data.name_list.selection_clear(0, END)
    for i in data.groups[name]:
        data.name_list.selection_set(i)
    redraw_root(data.canvas, data)


#-------------#
# Main Window #
#-------------#
# creates buttons for main window
def create_buttons(data):
    entry = Entry(data.root)
    entry.grid(row=2, column=1, sticky=E)
    data.entry = entry
    b = Button(data.root, text="new/edit", command=lambda: new_click(data))
    b.grid(row=2, column=2, sticky=W)
    entry.bind('<Return>', lambda _: new_click(data))
    entry.focus_force()
    save = Button(data.root, text="save", command=lambda: save_click(data))
    save.grid(row=3, column=1, pady=5)
    load = Button(data.root, text="load", command=lambda: load_click(data))
    load.grid(row=3, column=1, sticky=E, pady=5)
    icsadd = Button(data.root, text="batch ics add", command=lambda: ics_add_click(data))
    icsadd.grid(row=3, column=2, sticky=E, pady=5)
    newgroup = Button(data.root, text="group", command=lambda: group_click(data))
    newgroup.grid(row=2, column=3)

# creates list of names for main window
def create_list(data):
    name_list = Listbox(data.root, selectmode=EXTENDED, exportselection=0)
    scrollbar = Scrollbar(data.root, orient=VERTICAL)
    data.name_list = name_list
    name_list.grid(row=1, column=3, pady=(data.margin, 15), padx=data.margin,
                  sticky=N+S)
    scrollbar.grid(row=1, column=3, padx=(data.margin, data.margin-15),
                   pady=(data.margin, 15), sticky=N+S+E)
    name_list.bind('<<ListboxSelect>>', lambda _: redraw_root(data.canvas, data))
    data.list_created = True
    name_list.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=name_list.yview)

def create_availability_panel(data):
    data.availability_status = StringVar()
    panel = Frame(data.root)
    panel.grid(row=1, column=4, sticky=N+S, padx=(0, data.margin),
               pady=(data.margin, 15))
    Label(panel, text="Available", font="lucida-grande 12 bold").grid(
        row=0, column=0, sticky=W+E
    )
    data.available_text = create_scrollable_text(panel, row=1, column=0,
                                              padx=(0, 10))
    Label(panel, text="Unavailable", font="lucida-grande 12 bold").grid(
        row=0, column=1, sticky=W+E
    )
    data.unavailable_text = create_scrollable_text(panel, row=1, column=1)
    Label(panel, textvar=data.availability_status).grid(
        row=2, column=0, columnspan=2, sticky=W+E, pady=(10, 0)
    )
    Label(panel, text="Click a slot to lock. Click outside the grid to unlock.",
          wraplength=220, justify=CENTER).grid(
        row=3, column=0, columnspan=2, sticky=W+E, pady=(5, 0)
    )
    panel.columnconfigure(0, weight=1)
    panel.columnconfigure(1, weight=1)

def create_scrollable_text(parent, row, column, padx=0):
    frame = Frame(parent)
    frame.grid(row=row, column=column, sticky=N+S+W+E, padx=padx)
    text = Text(frame, width=18, height=25, wrap=NONE)
    yscrollbar = Scrollbar(frame, orient=VERTICAL, command=text.yview)
    xscrollbar = Scrollbar(frame, orient=HORIZONTAL, command=text.xview)
    text.configure(yscrollcommand=yscrollbar.set,
                   xscrollcommand=xscrollbar.set,
                   state=DISABLED)
    text.grid(row=0, column=0, sticky=N+S+W+E)
    yscrollbar.grid(row=0, column=1, sticky=N+S)
    xscrollbar.grid(row=1, column=0, sticky=E+W)
    text.bind("<MouseWheel>", scroll_text_vertical)
    text.bind("<Shift-MouseWheel>", scroll_text_horizontal)
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    return text

def scroll_text_vertical(event):
    event.widget.yview_scroll(_scroll_units(event), UNITS)
    return "break"

def scroll_text_horizontal(event):
    event.widget.xview_scroll(_scroll_units(event), UNITS)
    return "break"

def _scroll_units(event):
    return -3 * int(event.delta / 120)

# main screen 'new' button action
# brings up individual screen
def new_click(data, name=None, hidden=False):
    if name:
        data.name = name
    else:
        data.name = data.entry.get().strip()
        data.entry.delete(0, END)
    top = Toplevel(data.root)
    if hidden:
        top.withdraw()
    data.top = top
    individual_screen_init(data)

# main screen 'save' button action
# saves all schedules and groupings to a file
def save_click(data):
    fname = filedialog.asksaveasfilename(parent=data.root, defaultextension='.pickle', initialdir='.')
    if fname != None and fname != '':
        outfile = open(fname, 'wb')
        pickle.dump((data.names, data.week, data.groups), outfile)
        outfile.close()

# main screen 'load' button action
# clears current schedules and groups and loads new ones from the selected file
def load_click(data):
    fname = filedialog.askopenfilename(parent=data.root)
    if fname == None or fname == '':
        return
    infile = open(fname, 'rb')
    data.names, data.week, data.groups = pickle.load(infile)
    infile.close()
    data.name_list.delete(0, END)
    data.menu_groups.delete(0, END)
    for name in data.names:
        data.name_list.insert(END, name)
    for group in data.groups:
        data.menu_groups.add_command(label=group,
                                     command=lambda x=group: select_group(data, x))
    data.name_list.selection_set(0, END)
    redraw_root(data.canvas, data)

# main screen 'batch load ics' button action
# adds data from selected .ics files, using file names as person names
def ics_add_click(data):
    fnames = filedialog.askopenfilename(parent=data.root, multiple=True, filetypes=[('ICS', '.ics')])
    for fname in fnames:
        name = fname[fname.rfind('/')+1:].split('.')[0].title()
        if True: #name not in data.names:
            new_click(data, name, hidden=True)
            load_ics(data, fname)
            done_click(data)
    
    
# helper for group_click, adds/updates group in menu
def add_group(data, name):
    if name in data.groups:
        data.menu_groups.delete(name)
    data.groups[name] = list(map(int, data.name_list.curselection()))
    data.menu_groups.add_command(label=name,
                                 command=lambda: select_group(data, name))
    
# main screen 'group' button action
# creates new group from current selection
def group_click(data):
    popup = Toplevel()
    msg = Label(popup, text="Name this group:")
    msg.pack(fill=X)
    s = StringVar()
    e = Entry(popup, textvariable=s)
    e.pack()
    e.focus_set()
    e.bind('<Return>', lambda _: (add_group(data, s.get()), popup.destroy()))

def schedule_cell_from_event(event, data):
    r = (event.x - data.left_margin) // data.cell_width
    c = (event.y - data.margin) // data.cell_height
    if 0 <= r < data.rows and 0 <= c < data.cols:
        return r, c
    return None

def set_availability_panel(data, r=None, c=None):
    free = ""
    busy = ""
    if r is not None and c is not None:
        cur_sel = set(map(lambda i: data.names[i], data.name_list.curselection()))
        free = "\n".join(cur_sel & data.week[r][c])
        busy = "\n".join(cur_sel - data.week[r][c])
    set_text_content(data.available_text, free)
    set_text_content(data.unavailable_text, busy)

def set_text_content(text, content):
    text.configure(state=NORMAL)
    text.delete('1.0', END)
    text.insert('1.0', content)
    text.configure(state=DISABLED)

# uses mouse location in order to display availability
def calendar_hover(event, data):
    if data.availability_locked:
        return
    cell = schedule_cell_from_event(event, data)
    data.hover_cell = cell
    if cell:
        set_availability_panel(data, *cell)
    else:
        set_availability_panel(data)
    redraw_root(data.canvas, data)

def calendar_click(event, data):
    cell = schedule_cell_from_event(event, data)
    if cell:
        data.availability_locked = True
        data.locked_cell = cell
        data.hover_cell = None
        set_availability_panel(data, *cell)
        data.availability_status.set("Locked")
    else:
        data.availability_locked = False
        data.locked_cell = None
        data.availability_status.set("")
        set_availability_panel(data)
    redraw_root(data.canvas, data)
    

# draws main window
def redraw_root(canvas, data):
    canvas.delete(ALL)
    selected = map(int, data.name_list.curselection())
    names = set()
    for i in selected:
        names.add(data.names[i])
    for r in range(data.rows):
        x = (r+0.5)*data.cell_width+data.left_margin
        y = data.margin
        canvas.create_text(x, y, text=data.day_names[r].title(), anchor=S)
        for c in range(data.cols):
            x0 = r*data.cell_width+data.left_margin
            y0 = c*data.cell_height+data.margin
            x1 = x0+data.cell_width
            y1 = y0+data.cell_height
            n = len(data.week[r][c].intersection(names))
            frac = get_color_fraction(n, len(names))
            fill = norm_rgb_to_hex(*(data.cmap(frac)))
            textfill = 'black' if (sum(data.cmap(frac)) - 1)/3 > 0.7 else 'white'
            canvas.create_rectangle(x0, y0, x1, y1, fill=fill)
            canvas.create_text((x0+x1)/2, (y0+y1)/2, text=str(len(names)-n), fill=textfill)
            if r == 0:
                canvas.create_text(x0-5, y0, text=str(data.times[c]), anchor=E)
            if data.hover_cell == (r, c):
                canvas.create_rectangle(x0+1, y0+1, x1-1, y1-1,
                                        outline='black', width=2)
            if data.locked_cell == (r, c):
                canvas.create_rectangle(x0+2, y0+2, x1-2, y1-2,
                                        outline='gold', width=4)
    canvas.update()


#-------------------#
# Individual Window #
#-------------------#
# draws individual window in data.top window
def individual_screen_init(data):
    name_label = Label(data.top, text=data.name)
    name_label.grid(row=1, column=1, columnspan=7)
    instruction = Label(data.top, text="Highlight busy slots.")
    instruction.grid(row=2, column=1, columnspan=7)
    data.lbs = []
    for i in range(7):
        day_label = Label(data.top, text=data.day_names[i].title(), anchor=S, bg='gray92')
        day_label.grid(row=3, column=i+1, sticky=W+E)
        lb = Listbox(data.top, selectmode=EXTENDED, exportselection=False,
                     height=32, width=10)
        data.lbs.append(lb)
        lb.grid(row=4, column=i+1)
        for t in data.times:
            lb.insert(END, str(t))
    bdone = Button(data.top, text="done", command=lambda: done_click(data))
    bdone.grid(row=5, column=5, columnspan=2)
    binvert = Button(data.top, text="invert", command=lambda: invert_click(data))
    binvert.grid(row=5, column=3, columnspan=3)
    bload = Button(data.top, text="load ics", command=lambda: load_ics(data))
    bload.grid(row=5, column=2, columnspan=2)
    data.top.bind('<Return>', lambda _: done_click(data))
    if data.name in data.names:
        load_schedule(data)

# load individual busy slots from overall availability schedule
def load_schedule(data):
    for i in range(7):
        lb = data.lbs[i]
        day = data.week[i]
        for slot in range(len(day)):
            if data.name not in day[slot]:
                lb.selection_set(slot)
                
# individual screen 'done' button action
# data.week stores available names; selected edit-window slots are busy.
def done_click(data):
    if data.name not in data.names:
        data.names.append(data.name)
        data.name_list.insert(END, data.name)
        data.name_list.selection_set(END)
    for i in range(7):
        lb = data.lbs[i]
        for t in range(data.cols):
            if lb.selection_includes(t):
                data.week[i][t].discard(data.name)
            else:
                data.week[i][t].add(data.name)
    data.top.destroy()
    redraw_root(data.canvas, data)

# individual screen 'invert' button action
# inverts selected busy slots
def invert_click(data):
    for lb in data.lbs:
        for i in range(data.cols):
            if lb.selection_includes(i):
                lb.selection_clear(i)
            else:
                lb.selection_set(i)

def select_busy_slots(data, busy_slots):
    for day_index, start_idx, end_idx in busy_slots:
        for slot_index in range(start_idx, end_idx):
            data.lbs[day_index].selection_set(slot_index)

# loads individual schedule from .ics file
def load_ics(data, fname=None):
    if not fname:
        fname = filedialog.askopenfilename(parent=data.top)

    if fname == None or fname == '':
        return
    ics_file = open(fname, 'rb')
    ics_data = ics_file.read()
    ics_file.close()

    # reset in case there is already data
    for i in range(len(data.day_names)):
        data.lbs[i].selection_clear(0, END)

    busy_slots = parse_recurring_busy_slots(
        ics_data, data.day_names, data.start, data.step, data.cols
    )
    select_busy_slots(data, busy_slots)


# runs overall application
def run(width=300, height=300):
    # Set up data and call init
    class Struct(object): pass
    data = Struct()
    data.width = width
    data.height = height
    data.timer_delay = 100 # milliseconds
    
    # create the root and the canvas
    root = Tk()
    root.geometry("+0+0")
    canvas = Canvas(root, width=data.width, height=data.height)
    canvas.grid(row=1, column=1, columnspan=2)
    data.canvas = canvas
    data.root = root
    root.option_add('*tearOff', FALSE)
    init(data)
    
    # set up events
    canvas.bind("<Motion>", lambda event: calendar_hover(event, data))
    canvas.bind("<Button-1>", lambda event: calendar_click(event, data))
    
    # and launch the app
    root.mainloop()  # blocks until window is closed
    print("bye :)")

if __name__ == "__main__":
    run(450, 600)
