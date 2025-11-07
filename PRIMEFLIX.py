import tkinter as tk
from tkinter import ttk, messagebox, font
import os

# Safe Pillow import — if not installed, we'll fallback to placeholders without crashing.
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False
    print("Pillow not available — poster images will use placeholders.")


BG_PATH = "/Users/ralphblesson/Desktop/selsnium/Untitled design (2).png"
OVERLAY_PATH = "/Users/ralphblesson/Downloads/NETFLIXBG2.png"

root = tk.Tk()
root.title("PRIMEFLIX 🎬")
root.attributes("-fullscreen", True)   # fullscreen; press Esc to exit

favourites = []

# --- Poster preprocessing helper (paste after MOVIES list) ---
def preprocess_movie_posters(movies, dest_dir="/tmp/primeflix_posters", size=(200, 300), overwrite=False):
    """
    - Ensures each movie with an 'image' path is valid.
    - Resizes images to `size` and writes them into dest_dir.
    - Updates movie['image'] to the resized file path for consistent use by Browse.
    - Prints missing/invalid paths so you can fix them.
    """
    if not PIL_AVAILABLE:
        print("Pillow not available — skipping poster preprocessing.")
        return

    os.makedirs(dest_dir, exist_ok=True)
    from PIL import Image

    missing = []
    count = 0
    for m in movies:
        p = m.get("image")
        if not p:
            missing.append((m.get("title", "<unknown>"), "no path set"))
            continue

        # normalize path
        p = os.path.expanduser(p)
        p = os.path.abspath(p)

        if not os.path.exists(p):
            missing.append((m.get("title", "<unknown>"), p))
            continue

        # destination path
        safe_name = f"{m['title'].strip().replace(' ', '_')}_{m.get('year','').__str__()}"
        # remove characters that might break filenames
        safe_name = "".join(ch for ch in safe_name if ch.isalnum() or ch in ("_", "-"))
        ext = ".jpg"
        out_path = os.path.join(dest_dir, safe_name + ext)

        # skip if exists and not overwrite
        if not overwrite and os.path.exists(out_path):
            m["image"] = out_path
            continue

        try:
            img = Image.open(p)
            img = img.convert("RGB")
            img = img.resize(size, Image.LANCZOS)
            img.save(out_path, quality=90)
            m["image"] = out_path
            count += 1
        except Exception as e:
            missing.append((m.get("title", "<unknown>"), f"failed to process: {e}"))

    print(f"Poster preprocessing done — processed {count} images. {len(missing)} missing/fails:")
    for t, reason in missing:
        print(" -", t, "->", reason)

# call it immediately after YOUR MOVIES list definition:
# preprocess_movie_posters(MOVIES, dest_dir="/mnt/data/primeflix_posters", size=(200,300))


# --- Load background images (keep references to avoid GC) ---
bg_image = tk.PhotoImage(file=BG_PATH)
overlay_image = tk.PhotoImage(file=OVERLAY_PATH)


root._bg_image = bg_image
root._overlay_image = overlay_image

# Place background and overlay
bg_label = tk.Label(root, image=bg_image)
bg_label.place(x=0, y=0, relwidth=1, relheight=1)
overlay_label = tk.Label(root, image=overlay_image)
overlay_label.place(x=0, y=0, relwidth=1, relheight=1)

# --- Navbar ---
navbar_height = 80
navbar = tk.Frame(root, bg="black", height=navbar_height)
navbar.pack(fill="x", side="top")

# Add the text label inside navbar aligned to left
search_text_label = tk.Label(
    navbar,
    text="Find your next favorite movie 🎬",
    font=("Garamond Bold", 16, "bold"),
    fg="white",
    bg="black"
)
search_text_label.place(relx=0.5, rely=0.4, anchor="center")

# Function to open a new page
def open_page(page_name):
    new_window = tk.Toplevel(root)
    new_window.title(page_name)
    new_window.attributes("-fullscreen", True)
    new_window.bind("<Escape>", lambda e: new_window.attributes("-fullscreen", False))

    if page_name == "Home":
        new_window.configure(bg="black")
        tk.Label(new_window, text="WELCOME TO PRIMEFLIX", font=("Impact", 48, "bold"), fg="red",bg="black",).pack(pady=40)
        tk.Label(new_window, text="Browse thousands of movies, add to your list, and much more!", font=("Arial", 22),bg="black").pack(pady=10)
        tk.Label(new_window, text="Continue Watching:", font=("Arial", 18, "underline"),bg="black").pack(pady=(30,10))
        tk.Label(new_window, text="Premam (Malayalam) | Bahubali 2 (Telugu)", font=("Arial", 16),bg="black").pack()

    elif page_name == "Browse":
        new_window.configure(bg="black")
        tk.Label(new_window, text="BROWSE", font=("Impact", 36, "bold"), fg="white", bg="black").pack(pady=10)

        # Outer canvas + scrollbar
        canvas = tk.Canvas(new_window, bg="black", highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(new_window, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Frame inside canvas that holds the grid
        scroll_frame = tk.Frame(canvas, bg="black")
        window_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        # keep image refs to avoid GC
        new_window._images = []

        # center function (defined early so detail panel can call it)
        def center_grid(event=None):
            canvas_width = canvas.winfo_width()
            frame_reqw = scroll_frame.winfo_reqwidth()
            x = max((canvas_width - frame_reqw) // 2, 0)
            canvas.coords(window_id, x, 0)
            canvas.configure(scrollregion=canvas.bbox("all"))

        # In-place detail panel (seamless — no extra Toplevel)
        detail_panel = None

        def show_details_in_panel(m):
            nonlocal detail_panel
            # destroy existing panel
            if detail_panel and detail_panel.winfo_exists():
                detail_panel.destroy()

            # create right-side panel
            detail_panel = tk.Frame(new_window, bg="#0d0d0d", width=420)
            detail_panel.place(relx=1.0, y=0, anchor="ne", relheight=1.0)

            back_btn = tk.Button(detail_panel, text="← Back", font=("Arial", 12), bg="#222", fg="black",
                                 bd=0, relief="flat",
                                 command=lambda: (detail_panel.destroy(), center_grid()))
            back_btn.pack(padx=12, pady=12, anchor="nw")

            tk.Label(detail_panel, text=m["title"], bg="#0d0d0d", fg="white",
                     font=("Arial", 20, "bold"), wraplength=380, justify="center").pack(pady=(12,8))
            tk.Label(detail_panel, text=f"{m['year']}  •  ⭐ {m['rating']}",
                     bg="#0d0d0d", fg="#cccccc", font=("Arial", 12)).pack(pady=(0,8))
            tk.Label(detail_panel, text="Genres: " + ", ".join(m["genres"]),
                     bg="#0d0d0d", fg="#cfcfcf", font=("Arial", 12), wraplength=380, justify="left").pack(pady=(0,12), padx=12)

            # poster in detail panel (try image)
            poster_box = tk.Canvas(detail_panel, width=260, height=390, bg="#111", highlightthickness=0)
            poster_box.pack(pady=8)
            poster_path = m.get("image")
            if poster_path and PIL_AVAILABLE and os.path.exists(poster_path):
                try:
                    img = Image.open(poster_path)
                    img = img.resize((260, 390), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    poster_box.create_image(0, 0, image=photo, anchor="nw")
                    poster_box.image = photo
                    new_window._images.append(photo)
                except Exception:
                    poster_box.create_rectangle(4, 4, 256, 386, outline="#333", width=2, fill="#222")
                    poster_box.create_text(130, 195, text="Poster\nUnavailable", fill="white", font=("Arial", 14))
            else:
                poster_box.create_rectangle(4, 4, 256, 386, outline="#333", width=2, fill="#222")
                poster_box.create_text(130, 195, text="Poster\nPlaceholder", fill="white", font=("Arial", 14))

            tk.Label(detail_panel, text="Description:\n(Replace with real synopsis)", bg="#0d0d0d", fg="#bfbfbf",
                     font=("Arial", 11), wraplength=380, justify="left").pack(padx=12, pady=(12,8))

            def _addfav():
                if m not in favourites:
                    favourites.append(m)
                    messagebox.showinfo("Favourites", f"{m['title']} added to favourites!")
                else:
                    messagebox.showinfo("Favourites", f"{m['title']} is already in favourites.")

            fav_btn = tk.Button(detail_panel, text="Add to favourites", font=("Arial", 12, "bold"),
                                bg="#16A085", fg="red", bd=0, relief="flat", command=_addfav)
            fav_btn.pack(pady=(8,18))

            # re-center grid so layout stays nice with panel open
            center_grid()

        # display random movies in a stable 4-column grid
        import random
        displayed_movies = random.sample(MOVIES, min(20, len(MOVIES)))

        cols = 4
        row = 0
        col = 0
        for movie in displayed_movies:
            frame = tk.Frame(scroll_frame, bg="black", padx=10, pady=10)
            frame.grid(row=row, column=col, padx=20, pady=20)

            # Poster canvas (with safe image loading)
            canvas_poster = tk.Canvas(frame, width=200, height=300, bg="#333", highlightthickness=0, cursor="hand2")
            canvas_poster.pack()

            poster_path = movie.get("image")
            if poster_path and PIL_AVAILABLE and os.path.exists(poster_path):
                try:
                    img = Image.open(poster_path)
                    img = img.resize((200, 300), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    canvas_poster.create_image(0, 0, image=photo, anchor="nw")
                    canvas_poster.image = photo
                    new_window._images.append(photo)
                except Exception as e:
                    print(f"Failed to load poster '{poster_path}': {e}")
                    canvas_poster.create_text(100, 150, text="Poster\nUnavailable", fill="white", font=("Arial", 12))
            else:
                canvas_poster.create_text(100, 150, text="Poster\nPlaceholder", fill="white", font=("Arial", 12))

            label = tk.Label(frame, text=movie["title"], fg="white", bg="black", font=("Arial", 14, "bold"),
                             cursor="hand2", wraplength=200, justify="center")
            label.pack(pady=5)

            tk.Label(frame, text=f"⭐ {movie['rating']} | {movie['year']}", fg="white", bg="black", font=("Arial", 10)).pack()

            # Correctly capture movie and bind clicks (outside function definition)
            def on_click(event, m=movie):
                show_details_in_panel(m)

            canvas_poster.bind("<Button-1>", on_click)
            label.bind("<Button-1>", on_click)

            col += 1
            if col == cols:
                col = 0
                row += 1

        # finalize layout and ensure scrollregion correct
        scroll_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        center_grid()

        # bind canvas resize to recenter
        canvas.bind("<Configure>", center_grid)
        new_window.bind("<Configure>", lambda e: canvas.after(50, center_grid))

        # --- Reliable mouse-wheel / trackpad scrolling (only when over browse area) ---
        def _on_mousewheel(event):
            if getattr(event, "delta", None):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            else:
                if event.num == 5:
                    canvas.yview_scroll(1, "units")
                elif event.num == 4:
                    canvas.yview_scroll(-1, "units")

        def _bind_wheel(e=None):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel)
            canvas.bind_all("<Button-5>", _on_mousewheel)

        def _unbind_wheel(e=None):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", _bind_wheel)
        canvas.bind("<Leave>", _unbind_wheel)
        scroll_frame.bind("<Enter>", _bind_wheel)
        scroll_frame.bind("<Leave>", _unbind_wheel)

        # Arrow keys for scrolling
        new_window.bind_all("<Up>", lambda e: canvas.yview_scroll(-3, "units"))
        new_window.bind_all("<Down>", lambda e: canvas.yview_scroll(3, "units"))

    elif page_name == "My List":
        new_window.configure(bg="black")
        tk.Label(new_window, text="MY LIST (Favourites)", font=("IMPACT", 48, "bold"), fg="#FF4747",bg="black").pack(pady=30)
        if not favourites:
            tk.Label(new_window, text="You have no favourites yet!", font=("Arial", 16),bg="black").pack(pady=20)
        else:
            for f in favourites:
                line = f"{f['title']} ({f['year']}) — {', '.join(f['genres'])} | ⭐️ {f['rating']}"
                tk.Label(new_window, text=line, font=("Arial", 18),bg="black").pack(anchor="w", padx=60, pady=8)
        tk.Label(new_window, text="Double-click movies in results to view details. Use the button to add to favourites.", font=("Arial", 14, "italic")).pack(pady=(20,0))

    elif page_name == "More":
        new_window.configure(bg="black")
        tk.Label(new_window, text="ABOUT PRIMEFLIX", font=("Impact", 48, "bold"), fg="#8E44AD",bg="black").pack(pady=24)
        tk.Label(new_window, text="PRIMEFLIX is your portal to Indian & World cinema.\nSearch by genre or title, discover hidden gems, and track your favorites.", font=("Impact", 18),bg="black").pack(pady=20)
        tk.Label(new_window, text="Want to suggest a movie? Email: movies@primeflix.com", font=("Impact", 14),bg="black").pack(pady=22)
        tk.Label(new_window, text="Press Esc to exit fullscreen.", font=("Arial", 12, "italic"),bg="black").pack(pady=12)



def browse_genre(parent, genre):
    """Pop up a fullscreen listing filtered by genre."""
    genre_win = tk.Toplevel(parent)
    genre_win.title(f"{genre} Movies")
    genre_win.attributes("-fullscreen", True)
    genre_win.bind("<Escape>", lambda e: genre_win.attributes("-fullscreen", False))
    tk.Label(genre_win, text=f"{genre} Movies", font=("Arial", 36, "bold"), fg=genres.get(genre,"#FF4747")).pack(pady=24)
    filtered = [m for m in MOVIES if genre in m["genres"]]
    if not filtered:
        tk.Label(genre_win, text="No movies found in this genre.", font=("Arial",18)).pack(pady=20)
        return
    for m in filtered:
        desc = f"{m['title']} ({m['year']}) - Rating: {m['rating']}"
        tk.Label(genre_win, text=desc, font=("Arial", 18)).pack(anchor="w", padx=70, pady=6)



# Nav menu items
buttons = ["Home", "Browse", "My List", "More"]
for b in buttons:
    lbl = tk.Label(navbar, text=b, fg="white", bg="black", font=("Arial", 22, "bold"), cursor="hand2")
    lbl.pack(side="right", padx=20, pady=10)
    lbl.bind("<Button-1>", lambda e, name=b: open_page(name))

# Title
title = tk.Label(navbar, text="PRIMEFLIX 🎬", font=("Impact", 48, "bold"), fg="red", bg="black")
title.pack(anchor="nw", padx=30, pady=10)

# --- Genre buttons frame ---
genres = {
    "Comedy": "#FF4747",
    "Romance": "#FF6F91",
    "Thriller": "#8E44AD",
    "Action": "#3498DB",
    "Horror": "#2C3E50",
    "Drama": "#16A085",
    "Sci-Fi": "#F1C40F",
    "Mystery": "#E67E22",
}

genre_frame = tk.Frame(root, bg="black")
genre_frame.place(relx=0.5, rely=0.55, anchor='n')

def insert_genre(genre):
    entry.delete(0, tk.END)
    entry.insert(0, genre)
    entry.config(fg='black')

for g, color in genres.items():
    lbl = tk.Label(
        genre_frame,
        text=g,
        font=("Arial", 25),
        fg=color,
        bg="black",
        padx=12,
        pady=6,
        cursor="hand2"
    )
    lbl.pack(side="left", padx=5)
    lbl.bind("<Button-1>", lambda e, gen=g: insert_genre(gen))
    lbl.bind("<Enter>", lambda e, l=lbl: l.config(fg="white"))
    lbl.bind("<Leave>", lambda e, l=lbl, c=color: l.config(fg=c))

# --- Search entry ---
entry = tk.Entry(
    root,
    width=50,
    font=("Arial", 20),
    fg="gray",
    bg="white",
    bd=3,
    relief="sunken"
)
entry.insert(0, "Search...")
entry.place(relx=0.5, rely=0.45, anchor="center", width=600,height=40)

def on_entry_focus_in(event):
    if entry.get() == "Search...":
        entry.delete(0, tk.END)
        entry.config(fg='black')

def on_entry_focus_out(event):
    if not entry.get():
        entry.insert(0, "Search...")
        entry.config(fg='gray')

entry.bind("<FocusIn>", on_entry_focus_in)
entry.bind("<FocusOut>", on_entry_focus_out)

# Sample movie database
MOVIES = [
    {"title": "Space Warriors", "year": 2018, "rating": 8.0, "genres": ["Action", "Sci-Fi"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 10 22 AM.jpeg"},
    {"title": "Bangalore Days", "year": 2014, "rating": 8.2, "genres": ["Romance", "Comedy", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/Bangalore Days Poster.jpg"},
    {"title": "Kahaani", "year": 2012, "rating": 8.1, "genres": ["Thriller", "Mystery"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (1).jpeg"},
    {"title": "Premam", "year": 2015, "rating": 8.2, "genres": ["Romance", "Comedy"], "image": "/Users/ralphblesson/Desktop/selsnium/1d0248dfb942f6ea6a75d4130c01b727.jpg"},
    {"title": "Sairat", "year": 2016, "rating": 8.6, "genres": ["Romance", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 10 27 AM.jpeg"},
    {"title": "Lucifer", "year": 2019, "rating": 8.0, "genres": ["Action", "Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (3).jpeg"},
    {"title": "Andhadhun", "year": 2018, "rating": 8.3, "genres": ["Thriller", "Comedy"], "image": "//Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (4).jpeg"},
    {"title": "Uyare", "year": 2019, "rating": 8.2, "genres": ["Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 10 22 AM.jpeg"},
    {"title": "Thappad", "year": 2020, "rating": 7.6, "genres": ["Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (5).jpeg"},
    {"title": "Soorarai Pottru", "year": 2020, "rating": 8.7, "genres": ["Drama", "Action"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (6).jpeg"},
    {"title": "Drishyam 2", "year": 2021, "rating": 8.5, "genres": ["Thriller", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (7).jpeg"},
    {"title": "Joji", "year": 2021, "rating": 8.0, "genres": ["Drama", "Crime"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (8).jpeg"},
    {"title": "Minnal Murali", "year": 2021, "rating": 7.9, "genres": ["Action", "Comedy"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApuhweg2).jpeg"},
    {"title": "C U Soon", "year": 2020, "rating": 7.8, "genres": ["Thriller", "Mystery"], "image":"/Users/ralphblesson/Desktop/selsnium/nb .jpeg"},
    {"title": "Kumbalangi Nights", "year": 2019, "rating": 8.6, "genres": ["Drama", "Comedy"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 10 22 AM.jpeg"},
    {"title": "Bahubali: The Beginning", "year": 2015, "rating": 8.1, "genres": ["Action", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/seyfg.jpeg"},
    {"title": "Bahubali 2: The Conclusion", "year": 2017, "rating": 8.2, "genres": ["Action", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/sefs.jpeg"},
    {"title": "Tumbbad", "year": 2018, "rating": 8.3, "genres": ["Horror", "Fantasy"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 10 46 AM.jpeg"},
    {"title": "Gully Boy", "year": 2019, "rating": 8.0, "genres": ["Drama", "Music"], "image": "/Users/ralphblesson/Desktop/selsnium/sefsg.jpeg"},
    {"title": "Stree", "year": 2018, "rating": 7.6, "genres": ["Horror", "Comedy"], "image": "/Users/ralphblesson/Desktop/selsnium/rn.jpeg"},
    {"title": "Virus", "year": 2019, "rating": 8.4, "genres": ["Thriller", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/jej.jpeg"},
    {"title": "Maheshinte Prathikaaram", "year": 2016, "rating": 8.2, "genres": ["Comedy", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 10 49 AM.jpeg"},
    {"title": "Take Off", "year": 2017, "rating": 8.0, "genres": ["Drama", "Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (9).jpeg"},
    {"title": "Kaithi", "year": 2019, "rating": 8.5, "genres": ["Action", "Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 copy 2.jpeg"},
    {"title": "Master", "year": 2021, "rating": 7.6, "genres": ["Action", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/56WhatsApp Image Nov 4 2025 (1).jpeg"},
    {"title": "Pushpa: The Rise", "year": 2021, "rating": 7.3, "genres": ["Action", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WiihatsApp Image Nov 4 2025 (2).jpeg"},
    {"title": "Eega", "year": 2012, "rating": 7.9, "genres": ["Fantasy", "Action"], "image": "/Users/ralphblesson/Desktop/selsnium/675879.jpeg"},
    {"title": "Mahanati", "year": 2018, "rating": 8.5, "genres": ["Biography", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/34567.jpeg"},

    # Additional movies added for balance

    # Comedy (total 15)
    {"title": "Bheeshma", "year": 2020, "rating": 7.1, "genres": ["Comedy", "Romance"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 10 59 AM.jpeg"},
    {"title": "Chhichhore", "year": 2019, "rating": 8.2, "genres": ["Comedy", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/34567.jpeg"},
    {"title": "Delhi Belly", "year": 2011, "rating": 7.5, "genres": ["Comedy"], "image": "/Users/ralphblesson/Desktop/selsnium/34567.jpeg"},
    {"title": "Piku", "year": 2015, "rating": 7.6, "genres": ["Comedy", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/e5768.jpeg"},
    {"title": "Queen", "year": 2013, "rating": 8.2, "genres": ["Comedy", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/786fgu.jpeg"},
    {"title": "Angry Indian Goddesses", "year": 2015, "rating": 7.0, "genres": ["Comedy", "Drama"], "image": "//Users/ralphblesson/Desktop/selsnium/354stdyui.jpeg"},
    {"title": "Bareilly Ki Barfi", "year": 2017, "rating": 7.7, "genres": ["Comedy", "Romance"], "image": "/Users/ralphblesson/Desktop/selsnium/ytufi.jpeg"},
    {"title": "Tamasha", "year": 2015, "rating": 7.6, "genres": ["Romance", "Drama", "Comedy"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (11).jpeg"},
    {"title": "OMG! Oh My God", "year": 2012, "rating": 8.1, "genres": ["Comedy", "Drama"],'image':'/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025.jpeg'},
    {"title": "Jaane Bhi Do Yaaro", "year": 1983, "rating": 8.4, "genres": ["Comedy"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (12).jpeg"},

    # Romance (total 15)
    {"title": "Kuch Kuch Hota Hai", "year": 1998, "rating": 7.6, "genres": ["Romance", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (13).jpeg"},
    {"title": "Barfi!", "year": 2012, "rating": 8.1, "genres": ["Romance", "Comedy", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (14).jpeg"},
    {"title": "Love Aaj Kal", "year": 2009, "rating": 6.6, "genres": ["Romance", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (15).jpeg"},
    {"title": "Veer-Zaara", "year": 2004, "rating": 7.8, "genres": ["Romance", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (16).jpeg"},
    {"title": "Saathiya", "year": 2002, "rating": 7.6, "genres": ["Romance", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (17).jpeg"},
    {"title": "Lootera", "year": 2013, "rating": 7.4, "genres": ["Romance", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (18).jpeg"},
    {"title": "Raja Hindustani", "year": 1996, "rating": 6.8, "genres": ["Romance", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (19).jpeg"},
    {"title": "Jab We Met", "year": 2007, "rating": 7.9, "genres": ["Romance", "Comedy"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (20).jpeg"},
    {"title": "Rehnaa Hai Terre Dil Mein", "year": 2001, "rating": 7.4, "genres": ["Romance", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (21).jpeg"},
    {"title": "Ek Ladki Ko Dekha To Aisa Laga", "year": 2019, "rating": 7.4, "genres": ["Romance", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (22).jpeg"},

    # Thriller (total 15)
    {"title": "Talaash", "year": 2012, "rating": 7.2, "genres": ["Thriller", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (23).jpeg"},
    {"title": "Pink", "year": 2016, "rating": 8.1, "genres": ["Thriller", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (24).jpeg"},
    {"title": "Kahaani 2", "year": 2016, "rating": 6.6, "genres": ["Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (25).jpeg"},
    {"title": "A Wednesday!", "year": 2008, "rating": 8.1, "genres": ["Thriller", "Crime"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (26).jpeg"},
    {"title": "Badlapur", "year": 2015, "rating": 7.6, "genres": ["Thriller", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (27).jpeg"},
    {"title": "Drishyam (Hindi)", "year": 2015, "rating": 7.7, "genres": ["Thriller", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (28).jpeg"},
    {"title": "NH10", "year": 2015, "rating": 7.0, "genres": ["Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (29).jpeg"},
    {"title": "Special 26", "year": 2013, "rating": 7.8, "genres": ["Thriller", "Crime"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (30).jpeg"},
    {"title": "Talvar", "year": 2015, "rating": 8.1, "genres": ["Mystery", "Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (31).jpeg"},

    # Action (total 15)
    {"title": "KGF", "year": 2018, "rating": 8.2, "genres": ["Action", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (32).jpeg"},
    {"title": "War", "year": 2019, "rating": 6.5, "genres": ["Action", "Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (33).jpeg"},
    {"title": "Saaho", "year": 2019, "rating": 5.5, "genres": ["Action", "Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (34).jpeg"},
    {"title": "Raees", "year": 2017, "rating": 7.2, "genres": ["Action", "Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (35).jpeg"},
    {"title": "Ghajini", "year": 2008, "rating": 7.6, "genres": ["Action", "Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (36).jpeg"},
    {"title": "Dhoom 2", "year": 2006, "rating": 7.2, "genres": ["Action", "Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (37).jpeg"},
    {"title": "Holiday", "year": 2014, "rating": 7.9, "genres": ["Action", "Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (38).jpeg"},
    {"title": "Ra.One", "year": 2011, "rating": 4.9, "genres": ["Sci-Fi", "Action"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (39).jpeg"},
    {"title": "Don", "year": 2006, "rating": 7.8, "genres": ["Action", "Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (40).jpeg"},
    {"title": "Gabbar Is Back", "year": 2015, "rating": 6.6, "genres": ["Action", "Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (41).jpeg"},

    # Horror (total 10)
    {"title": "Pari", "year": 2018, "rating": 6.0, "genres": ["Horror"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (42).jpeg"},
    {"title": "Raaz", "year": 2002, "rating": 6.2, "genres": ["Horror", "Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (43).jpeg"},
    {"title": "Pizza", "year": 2012, "rating": 7.0, "genres": ["Horror", "Mystery"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (44).jpeg"},
    {"title": "1920", "year": 2008, "rating": 5.6, "genres": ["Horror", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (45).jpeg"},
    {"title": "Ragini MMS", "year": 2011, "rating": 5.4, "genres": ["Horror"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (46).jpeg"},

    # Drama (total 20)
    {"title": "Anand", "year": 1971, "rating": 9.0, "genres": ["Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (47).jpeg"},
    {"title": "Stanley Ka Dabba", "year": 2011, "rating": 8.0, "genres": ["Drama", "Comedy"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (48).jpeg"},
    {"title": "Masaan", "year": 2015, "rating": 8.1, "genres": ["Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (49).jpeg"},
    {"title": "October", "year": 2018, "rating": 7.7, "genres": ["Drama", "Romance"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (50).jpeg"},
    {"title": "Kapoor & Sons", "year": 2016, "rating": 7.7, "genres": ["Drama", "Comedy"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (51).jpeg"},
    {"title": "Taare Zameen Par", "year": 2007, "rating": 8.4, "genres": ["Drama", "Family"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (52).jpeg"},
    {"title": "Lunchbox", "year": 2013, "rating": 8.0, "genres": ["Drama", "Romance"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (53).jpeg"},
    {"title": "Chhapaak", "year": 2020, "rating": 7.1, "genres": ["Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (54).jpeg"},

    # Sci-Fi (total 6)
    {"title": "PK", "year": 2014, "rating": 8.1, "genres": ["Sci-Fi", "Comedy"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (55).jpeg"},
    {"title": "Cargo", "year": 2019, "rating": 7.3, "genres": ["Sci-Fi", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (56).jpeg"},
    {"title": "Ra.One", "year": 2011, "rating": 4.9, "genres": ["Sci-Fi", "Action"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (58).jpeg"},
    {"title": "Tik Tik Tik", "year": 2018, "rating": 6.1, "genres": ["Sci-Fi", "Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (59).jpeg"},

    # Mystery (total 6)
    {"title": "Talvar", "year": 2015, "rating": 8.1, "genres": ["Mystery", "Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (57).jpeg"},
    {"title": "Badla", "year": 2019, "rating": 7.8, "genres": ["Mystery", "Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (58).jpeg"},
    {"title": "Ittefaq", "year": 2017, "rating": 7.0, "genres": ["Mystery", "Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (59).jpeg"},

    # Fantasy (total 5)
    {"title": "Miruthan", "year": 2016, "rating": 6.1, "genres": ["Fantasy", "Action"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (60).jpeg"},
    {"title": "7aum Arivu", "year": 2011, "rating": 6.3, "genres": ["Fantasy", "Thriller"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (61).jpeg"},
    {"title": "Raavan", "year": 2010, "rating": 6.2, "genres": ["Fantasy", "Action"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (62).jpeg"},

    # Biography (total 3)
    {"title": "Neerja", "year": 2016, "rating": 8.0, "genres": ["Biography", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (63).jpeg"},
    {"title": "Dangal", "year": 2016, "rating": 8.4, "genres": ["Biography", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (64).jpeg"},
    {"title": "MS Dhoni: The Untold Story", "year": 2016, "rating": 9.7, "genres": ["Biography", "Drama"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (65).jpeg"},

    # Music (total 3)
    {"title": "Rockstar", "year": 2011, "rating": 7.9, "genres": ["Drama", "Music"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (66).jpeg"},
    {"title": "Aashiqui 2", "year": 2013, "rating": 7.1, "genres": ["Drama", "Music"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (67).jpeg"},
    {"title": "Secret Superstar", "year": 2017, "rating": 7.8, "genres": ["Drama", "Music"], "image": "/Users/ralphblesson/Desktop/selsnium/WhatsApp Image Nov 4 2025 (68).jpeg"},
]

def find_movies(query):
    q = query.strip().lower()
    if not q or q == "search...":
        return []
    results = []
    for m in MOVIES:
        title_match = q in m["title"].lower()
        genre_match = any(q == g.lower() or q in g.lower() for g in m["genres"])
        if title_match or genre_match:
            results.append(m)
    return results

def show_search_results(results, query):
    import tkinter.font as tkFont

    win = tk.Toplevel(root)
    win.title(f"Search: {query}")
    win.attributes("-fullscreen", True)
    win.bind("<Escape>", lambda e: win.attributes("-fullscreen", False))

    # keep refs for images
    win._images = []

    # Fonts and style
    tree_font = tkFont.Font(family="Arial", size=14)
    row_height = tree_font.metrics("linespace") + 6
    style = ttk.Style()
    style.configure("Treeview", rowheight=row_height)

    if not results:
        tk.Label(win, text=f"No matches for '{query}'", font=("Arial", 24)).pack(expand=True)
        return

    # Layout: left detail panel (fixed width) + right treeview (expand)
    left_w = 320
    container = tk.Frame(win, bg="#0b0b0b")
    container.pack(fill="both", expand=True)

    left_panel = tk.Frame(container, width=left_w, bg="#0d0d0d", padx=12, pady=12)
    left_panel.pack(side="left", fill="y")
    left_panel.pack_propagate(False)

    right_panel = tk.Frame(container, bg="black")
    right_panel.pack(side="left", fill="both", expand=True)

    # Left: Poster placeholder + details
    poster_canvas = tk.Canvas(left_panel, width=200, height=300, bg="#111", highlightthickness=0)
    poster_canvas.pack(pady=(6,12))
    poster_canvas.create_rectangle(4, 4, 196, 296, outline="#333", width=2, fill="#222")
    poster_canvas.create_text(100, 150, text="Poster\nPlaceholder", fill="white", font=("Arial", 12), justify="center")

    title_label = tk.Label(left_panel, text="Title", bg="#0d0d0d", fg="white", font=("Arial", 14, "bold"), wraplength=left_w-24, justify="center")
    title_label.pack(pady=(6,4))

    meta_label = tk.Label(left_panel, text="Year • Rating", bg="#0d0d0d", fg="#cccccc", font=("Arial", 11))
    meta_label.pack(pady=(0,6))

    genres_label = tk.Label(left_panel, text="Genres:", bg="#0d0d0d", fg="#cfcfcf", font=("Arial", 11), wraplength=left_w-24, justify="left")
    genres_label.pack(pady=(0,8))

    desc_label = tk.Label(left_panel, text="Description:\n(Replace with real synopsis)", bg="#0d0d0d", fg="#bfbfbf", font=("Arial", 10), wraplength=left_w-24, justify="left")
    desc_label.pack(pady=(0,12))

    def add_current_to_favourites():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Favourites", "No movie selected.")
            return
        vals = tree.item(sel[0], "values")
        movie = next((m for m in results if m["title"] == vals[0]), None)
        if movie and movie not in favourites:
            favourites.append(movie)
            messagebox.showinfo("Favourites", f"{movie['title']} added to favourites!")
        else:
            messagebox.showinfo("Favourites", f"{vals[0]} is already in favourites.")

    fav_btn = tk.Button(left_panel, text="Add Selected to Favourites", font=("Arial", 12, "bold"),
                        bg="#16A085", fg="red", bd=0, relief="flat", command=add_current_to_favourites)
    fav_btn.pack(pady=(6,8))

    # Right: Treeview of results
    cols = ("Title", "Year", "Rating", "Genres")
    tree = ttk.Treeview(right_panel, columns=cols, show="headings", selectmode="browse", style="Treeview")
    for c in cols:
        tree.heading(c, text=c)
    tree.column("Title", width=420)
    tree.column("Year", width=100, anchor="center")
    tree.column("Rating", width=100, anchor="center")
    tree.column("Genres", width=300)

    # Insert rows
    for m in results:
        tree.insert("", "end", values=(m["title"], m.get("year",""), m.get("rating",""), ", ".join(m.get("genres",[]))))
    tree.pack(fill="both", expand=True, padx=20, pady=20)

    # Selection handler: update left panel with poster + details
    def update_left_panel(event=None):
        sel = tree.selection()
        if not sel:
            return
        vals = tree.item(sel[0], "values")
        title = vals[0]
        movie = next((m for m in results if m["title"] == title), None)
        if not movie:
            return

        # Title / meta / genres
        title_label.config(text=movie.get("title", ""))
        meta_label.config(text=f"{movie.get('year','')}  •  ⭐ {movie.get('rating','')}")
        genres_label.config(text="Genres: " + ", ".join(movie.get("genres", [])))

        # poster: try to load
        poster_canvas.delete("all")
        poster_path = movie.get("image")
        if poster_path and PIL_AVAILABLE and os.path.exists(poster_path):
            try:
                img = Image.open(poster_path)
                img = img.resize((200, 300), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                poster_canvas.create_image(0, 0, image=photo, anchor="nw")
                poster_canvas.image = photo
                win._images.append(photo)
            except Exception:
                poster_canvas.create_rectangle(4, 4, 196, 296, outline="#333", width=2, fill="#222")
                poster_canvas.create_text(100, 150, text="Poster\nUnavailable", fill="white", font=("Arial", 12), justify="center")
        else:
            poster_canvas.create_rectangle(4, 4, 196, 296, outline="#333", width=2, fill="#222")
            poster_canvas.create_text(100, 150, text="Poster\nPlaceholder", fill="white", font=("Arial", 12), justify="center")

    # Bind selection change (single click) and Return key
    tree.bind("<<TreeviewSelect>>", update_left_panel)
    tree.bind("<Return>", lambda e: update_left_panel())

    # Also allow double-click to open the smaller detail popup if you still want that:
    def on_double_click(event):
        sel = tree.selection()
        if not sel:
            return
        vals = tree.item(sel[0], "values")
        title = vals[0]
        movie = next((m for m in results if m["title"] == title), None)
        if movie:
            # existing small popup behavior (keeps compatibility)
            detail = tk.Toplevel(win)
            detail.title(movie["title"])
            detail.geometry("420x360")
            # poster in popup
            poster_canvas_small = tk.Canvas(detail, width=200, height=300, bg="#111", highlightthickness=0)
            poster_canvas_small.pack(pady=(8,6))
            ppath = movie.get("image")
            if ppath and PIL_AVAILABLE and os.path.exists(ppath):
                try:
                    img = Image.open(ppath)
                    img = img.resize((200,300), Image.LANCZOS)
                    ph = ImageTk.PhotoImage(img)
                    poster_canvas_small.create_image(0,0, image=ph, anchor="nw")
                    poster_canvas_small.image = ph
                except Exception:
                    poster_canvas_small.create_text(100,150, text="Poster\nUnavailable")
            else:
                poster_canvas_small.create_text(100,150, text="Poster\nPlaceholder")

            tk.Label(detail, text=movie["title"], font=("Arial", 16, "bold")).pack(pady=(6,4))
            tk.Label(detail, text=f"Year: {movie.get('year','')}", font=("Arial", 12)).pack()
            tk.Label(detail, text=f"Rating: {movie.get('rating','')}", font=("Arial", 12)).pack()
            tk.Label(detail, text=f"Genres: {', '.join(movie.get('genres',[]))}", font=("Arial", 11)).pack(pady=(6,8))

    tree.bind("<Double-1>", on_double_click)

    # Pre-select first row if exists
    first = tree.get_children()
    if first:
        tree.selection_set(first[0])
        tree.focus(first[0])
        update_left_panel()

    # Final layout tweaks
    win.update_idletasks()




def search_action():
    q = entry.get().strip()
    res = find_movies(q)
    if not q or q.lower() == "search...":
        messagebox.showinfo("Empty Search", "Please enter or select a genre or movie title.")
        return
    show_search_results(res, q)

entry.bind("<Return>", lambda e: search_action())

search_btn = tk.Button(
    root,
    text="Search",
    font=("Arial", 14, "bold"),
    fg="red",
    bg="gray",
    activebackground="darkred",
    activeforeground="white",
    bd=0,
    relief="flat",
    padx=20,
    pady=10,
    command=search_action
)
search_btn.place(relx=0.5, rely=0.65, anchor="n")

# --- Escape to exit fullscreen ---
root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

root.mainloop()
