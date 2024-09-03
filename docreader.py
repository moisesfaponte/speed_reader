import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser, Menu
import time
from docx import Document
import pdfplumber
from threading import Thread


class ReadingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mejora tu Velocidad de Lectura - Word y PDF")
        self.root.geometry("800x600")

        # Inicializar variables
        self.text_content = ""
        self.speed = 200
        self.is_reading = False
        self.start_index = 0
        self.font_size = 24
        self.is_dark_mode = False
        self.current_word_index = 0
        self.words_per_display = 1
        self.highlight_color = "lightgray"

        # Crear UI
        self.create_widgets()

    def create_widgets(self):
        # Menú
        self.create_menu()

        # Frame principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Panel izquierdo: Opciones de lectura
        left_panel = tk.Frame(main_frame)
        left_panel.pack(side="left", fill="y")

        self.load_button = tk.Button(left_panel, text="Cargar Archivo", command=self.load_file)
        self.load_button.pack(pady=5)

        self.start_button = tk.Button(left_panel, text="Comenzar Lectura", command=self.start_reading)
        self.start_button.pack(pady=5)

        self.pause_button = tk.Button(left_panel, text="Pausar Lectura", command=self.pause_reading)
        self.pause_button.pack(pady=5)

        self.stop_button = tk.Button(left_panel, text="Detener Lectura", command=self.pause_reading)
        self.stop_button.pack(pady=5)

        self.speed_slider = tk.Scale(left_panel, from_=100, to_=2500, orient=tk.HORIZONTAL, label="Velocidad (ppm)",
                                     command=self.set_speed)
        self.speed_slider.set(200)
        self.speed_slider.pack(pady=5)

        self.speed_entry = tk.Entry(left_panel, width=10)
        self.speed_entry.insert(0, "200")
        self.speed_entry.pack(pady=5)
        self.speed_entry.bind("<Return>", self.update_speed_from_entry)

        self.font_slider = tk.Scale(left_panel, from_=10, to_=72, orient=tk.HORIZONTAL, label="Tamaño de la Fuente",
                                    command=self.adjust_font_size)
        self.font_slider.set(24)
        self.font_slider.pack(pady=5)

        self.words_per_display_slider = tk.Scale(left_panel, from_=1, to_=10, orient=tk.HORIZONTAL,
                                                 label="Palabras por Paso", command=self.set_words_per_display)
        self.words_per_display_slider.set(1)
        self.words_per_display_slider.pack(pady=5)

        self.start_slider = tk.Scale(left_panel, from_=0, to_=0, orient=tk.HORIZONTAL, label="Empezar desde (línea)",
                                     command=self.set_start_index)
        self.start_slider.pack(pady=5)

        self.font_var = tk.StringVar(value="Helvetica")
        self.font_menu = tk.OptionMenu(left_panel, self.font_var, "Helvetica", "Arial", "Times New Roman",
                                       command=self.change_font)
        self.font_menu.pack(pady=5)

        self.highlight_color_button = tk.Button(left_panel, text="Elige color de resaltado",
                                                command=self.choose_highlight_color)
        self.highlight_color_button.pack(pady=5)

        self.theme_button = tk.Button(left_panel, text="Modo Lectura", command=self.toggle_theme)
        self.theme_button.pack(pady=5)

        # Panel derecho: Visualización del texto
        right_panel = tk.Frame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True)

        self.text_display = TextWithLineNumbers(right_panel)
        self.text_display.pack(side="top", fill="both", expand=True)

        self.word_display = tk.Text(right_panel, height=2, font=("Helvetica", self.font_size), wrap="word", state='disabled')
        self.word_display.pack(pady=10, fill=tk.X)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(right_panel, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=10)

        self.estimated_time_label = tk.Label(right_panel, text="Tiempo estimado: N/A")
        self.estimated_time_label.pack(pady=5)

        self.remaining_time_label = tk.Label(right_panel, text="Tiempo restante: N/A")
        self.remaining_time_label.pack(pady=5)

    def create_menu(self):
        menu_bar = Menu(self.root)
        file_menu = Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Cargar Archivo", command=self.load_file)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        menu_bar.add_cascade(label="Archivo", menu=file_menu)

        options_menu = Menu(menu_bar, tearoff=0)
        options_menu.add_command(label="Guardar Progreso", command=self.save_progress)
        options_menu.add_command(label="Cargar Progreso", command=self.load_progress)
        menu_bar.add_cascade(label="Opciones", menu=options_menu)

        self.root.config(menu=menu_bar)

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Word files", "*.docx"), ("PDF files", "*.pdf")])
        if file_path:
            if file_path.endswith(".docx"):
                self.text_content = self.read_docx(file_path)
            elif file_path.endswith(".pdf"):
                self.text_content = self.read_pdf(file_path)

            self.text_display.delete(1.0, tk.END)
            self.text_display.insert(tk.END, self.text_content)

            self.set_start_index(0)
            self.update_start_slider()
            self.update_estimated_time()

    def read_docx(self, file_path):
        try:
            doc = Document(file_path)
            full_text = [para.text for para in doc.paragraphs]
            return ' '.join(full_text)
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer el archivo DOCX: {e}")
            return ""

    def read_pdf(self, file_path):
        try:
            with pdfplumber.open(file_path) as pdf:
                full_text = [page.extract_text() for page in pdf.pages]
            return ' '.join(full_text)
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer el archivo PDF: {e}")
            return ""

    def set_speed(self, val):
        self.speed = int(val)
        self.speed_entry.delete(0, tk.END)
        self.speed_entry.insert(0, str(self.speed))
        self.update_estimated_time()

    def update_speed_from_entry(self, event=None):
        try:
            self.speed = int(self.speed_entry.get())
            self.speed_slider.set(self.speed)
            self.update_estimated_time()
        except ValueError:
            messagebox.showerror("Error", "Por favor, introduce un número válido para la velocidad.")

    def set_start_index(self, val):
        self.start_index = int(val)
        words = self.text_content.split()
        self.current_word_index = sum(len(line.split()) for line in self.text_content.split('\n')[:self.start_index])
        self.text_display.mark_set("insert", f"{self.start_index}.0")
        self.text_display.see(f"{self.start_index}.0")

    def start_reading(self):
        if self.text_content and not self.is_reading:
            self.is_reading = True
            read_thread = Thread(target=self.display_words, args=(self.current_word_index,))
            read_thread.start()

    def pause_reading(self):
        self.is_reading = False

    def display_words(self, start_idx):
        words = self.text_content.split()
        word_count = len(words)

        for i in range(start_idx, word_count, self.words_per_display):
            if not self.is_reading:
                self.current_word_index = i
                return
            chunk = " ".join(words[i:i + self.words_per_display])

            self.word_display.config(state='normal')
            self.word_display.delete("1.0", tk.END)
            self.word_display.insert(tk.END, chunk.center(len(chunk) + 20))
            self.word_display.tag_add("highlight", "1.0", "1.end")
            self.word_display.tag_config("highlight", background=self.highlight_color)
            self.word_display.config(state='disabled')

            self.progress_var.set((i + self.words_per_display) / word_count * 100)

            remaining_words = word_count - (i + self.words_per_display)
            if self.speed > 0:
                remaining_minutes = remaining_words / (self.speed / self.words_per_display)
                remaining_seconds = int(remaining_minutes * 60)
                remaining_time_text = time.strftime("%H:%M:%S", time.gmtime(remaining_seconds))
                self.remaining_time_label.config(text=f"Tiempo restante: {remaining_time_text}")

            self.root.update()
            time.sleep(60 / self.speed)

        self.word_display.config(state='normal')
        self.word_display.delete("1.0", tk.END)
        self.word_display.insert(tk.END, "Fin del documento".center(20))
        self.word_display.config(state='disabled')
        self.is_reading = False

    def adjust_font_size(self, val):
        self.font_size = int(val)
        self.word_display.config(font=(self.font_var.get(), self.font_size))

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        bg_color = "black" if self.is_dark_mode else "white"
        fg_color = "white" if self.is_dark_mode else "black"
        self.root.configure(bg=bg_color)
        self.text_display.configure(bg=bg_color, fg=fg_color, insertbackground=fg_color)
        self.word_display.configure(bg=bg_color, fg=fg_color)
        self.text_display.line_numbers.configure(bg=bg_color, fg=fg_color)
        for widget in self.root.winfo_children():
            if isinstance(widget, (tk.Button, tk.Scale, tk.Label, tk.Entry, ttk.Progressbar)):
                widget.configure(bg=bg_color, fg=fg_color)
        self.theme_button.config(text="Modo Light" if self.is_dark_mode else "Modo Lectura")

    def update_start_slider(self):
        num_lines = int(self.text_display.index('end').split('.')[0]) - 1
        self.start_slider.config(to=num_lines)
        self.start_slider.set(self.start_index)

    def set_words_per_display(self, val):
        self.words_per_display = int(val)
        self.update_estimated_time()

    def update_estimated_time(self):
        words = self.text_content.split()
        total_words = len(words)
        if self.speed > 0:
            effective_speed = self.speed / self.words_per_display
            total_minutes = total_words / effective_speed
            total_seconds = int(total_minutes * 60)
            time_text = time.strftime("%H:%M:%S", time.gmtime(total_seconds))
            self.estimated_time_label.config(text=f"Tiempo estimado: {time_text}")
        else:
            self.estimated_time_label.config(text="Tiempo estimado: N/A")

    def change_font(self, selected_font):
        self.word_display.config(font=(selected_font, self.font_size))

    def choose_highlight_color(self):
        self.highlight_color = colorchooser.askcolor(title="Elige un color de resaltado")[1]
        self.word_display.tag_config("highlight", background=self.highlight_color or "lightgray")

    def save_progress(self):
        # Implementar la lógica para guardar el progreso
        pass

    def load_progress(self):
        # Implementar la lógica para cargar el progreso
        pass


class TextWithLineNumbers(tk.Text):
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)
        self.line_numbers = tk.Text(self, width=4, padx=4, takefocus=0, border=0, background='lightgrey', state='disabled')
        self.line_numbers.pack(side="left", fill="y")
        self.pack(side="right", fill="both", expand=True)
        self.bind("<KeyRelease>", self.on_key_release)
        self.bind("<MouseWheel>", self.on_mouse_wheel)
        self.update_line_numbers()

    def on_key_release(self, event=None):
        self.update_line_numbers()

    def on_mouse_wheel(self, event=None):
        self.update_line_numbers()

    def update_line_numbers(self):
        self.line_numbers.config(state='normal')
        self.line_numbers.delete(1.0, "end")

        i = self.index("@0,0")
        while True:
            dline = self.dlineinfo(i)
            if dline is None:
                break
            linenum = str(i).split(".")[0]
            self.line_numbers.insert("end", linenum + "\n")
            i = self.index("%s+1line" % i)
        self.line_numbers.config(state='disabled')


if __name__ == "__main__":
    root = tk.Tk()
    app = ReadingApp(root)
    root.mainloop()
