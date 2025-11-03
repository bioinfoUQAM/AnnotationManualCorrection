import cv2
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os

class AnnotationCorrectionTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Outil de Correction d'Annotations")
        self.root.geometry("1300x900")
        
        self.video_path = None
        self.csv_path = None
        self.annotations_df = None
        self.cap = None
        self.current_frame_idx = 0
        self.total_frames = 0
        self.behavior_columns = []
        self.modified = False
        
        # Mapping des touches clavier aux comportements
        self.keyboard_shortcuts = {}
        
        self.setup_ui()
        
        # Bind des touches clavier
        self.root.bind('<Key>', self.handle_keypress)
    
    def setup_ui(self):
        # Menu principal
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Charger Vidéo", command=self.load_video)
        file_menu.add_command(label="Charger Annotations CSV", command=self.load_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Sauvegarder", command=self.save_annotations)
        file_menu.add_command(label="Sauvegarder sous...", command=self.save_annotations_as)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.quit_app)
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuration du redimensionnement
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Section vidéo
        video_frame = ttk.LabelFrame(main_frame, text="Vidéo", padding="10")
        video_frame.grid(row=0, column=0, rowspan=2, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.video_label = ttk.Label(video_frame, text="Aucune vidéo chargée", relief=tk.SUNKEN)
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # Info frame
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        self.frame_info_label = ttk.Label(info_frame, text="Frame: 0 / 0", font=("Arial", 12, "bold"))
        self.frame_info_label.pack()
        
        # Section annotations actuelles
        current_annotation_frame = ttk.LabelFrame(main_frame, text="Annotations actuelles", padding="10")
        current_annotation_frame.grid(row=1, column=1, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.current_annotation_text = tk.Text(current_annotation_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        self.current_annotation_text.pack(fill=tk.BOTH, expand=True)
        
        # Section correction
        correction_frame = ttk.LabelFrame(main_frame, text="Correction des annotations (Utilisez les touches pour cocher/décocher)", padding="10")
        correction_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Conteneur scrollable pour les checkboxes
        canvas = tk.Canvas(correction_frame, height=150)
        scrollbar = ttk.Scrollbar(correction_frame, orient="vertical", command=canvas.yview)
        self.checkbox_frame = ttk.Frame(canvas)
        
        self.checkbox_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.checkboxes = {}
        
        # Application par plage de frames
        range_frame = ttk.LabelFrame(main_frame, text="Application par plage de frames", padding="10")
        range_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        range_control_frame = ttk.Frame(range_frame)
        range_control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(range_control_frame, text="De la frame:").pack(side=tk.LEFT, padx=5)
        self.range_start_entry = ttk.Entry(range_control_frame, width=10)
        self.range_start_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(range_control_frame, text="À la frame:").pack(side=tk.LEFT, padx=5)
        self.range_end_entry = ttk.Entry(range_control_frame, width=10)
        self.range_end_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(range_control_frame, text="✓ Appliquer aux frames sélectionnées", 
                  command=self.apply_to_range, style="Accent.TButton").pack(side=tk.LEFT, padx=10)
        
        ttk.Label(range_control_frame, text="(Applique les comportements cochés à toutes les frames de la plage)").pack(side=tk.LEFT, padx=5)
        
        # Boutons de contrôle
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=5)
        
        ttk.Button(control_frame, text="◄◄ Frame Précédente", command=self.prev_frame).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="✓ Correct (Frame suivante)", command=self.next_frame, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="✓ OK - Confirmer Correction", command=self.confirm_correction).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Frame Suivante ►►", command=self.next_frame).pack(side=tk.LEFT, padx=5)
        
        # Saut de frame
        jump_frame = ttk.Frame(main_frame)
        jump_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=5)
        
        ttk.Label(jump_frame, text="Aller à la frame:").pack(side=tk.LEFT, padx=5)
        self.jump_entry = ttk.Entry(jump_frame, width=10)
        self.jump_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(jump_frame, text="Aller", command=self.jump_to_frame).pack(side=tk.LEFT, padx=5)
        
        # Affichage des raccourcis clavier
        self.shortcuts_label = ttk.Label(jump_frame, text="", foreground="blue")
        self.shortcuts_label.pack(side=tk.LEFT, padx=20)
    
    def assign_keyboard_shortcuts(self):
        """Assigne automatiquement des touches aux comportements"""
        self.keyboard_shortcuts = {}
        used_keys = set()
        
        for behavior in self.behavior_columns:
            # Essayer d'utiliser la première lettre (minuscule)
            first_letter = behavior[0].lower()
            
            if first_letter not in used_keys and first_letter.isalpha():
                self.keyboard_shortcuts[first_letter] = behavior
                used_keys.add(first_letter)
            else:
                # Essayer les autres lettres du mot
                for char in behavior.lower():
                    if char.isalpha() and char not in used_keys:
                        self.keyboard_shortcuts[char] = behavior
                        used_keys.add(char)
                        break
        
        # Afficher les raccourcis
        shortcuts_text = "Raccourcis: " + ", ".join([f"{key.upper()}={behavior[:15]}" for key, behavior in sorted(self.keyboard_shortcuts.items())])
        self.shortcuts_label.config(text=shortcuts_text[:100] + "...")
    
    def handle_keypress(self, event):
        """Gère les touches du clavier pour cocher/décocher les comportements"""
        key = event.char.lower()
        
        if key in self.keyboard_shortcuts:
            behavior = self.keyboard_shortcuts[key]
            # Toggle la checkbox
            current_value = self.checkboxes[behavior].get()
            self.checkboxes[behavior].set(1 - current_value)
    
    def load_video(self):
        filepath = filedialog.askopenfilename(
            title="Sélectionner la vidéo",
            filetypes=[("Fichiers vidéo", "*.mp4 *.avi *.mov *.mkv"), ("Tous les fichiers", "*.*")]
        )
        if filepath:
            self.video_path = filepath
            self.cap = cv2.VideoCapture(filepath)
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            messagebox.showinfo("Succès", f"Vidéo chargée: {os.path.basename(filepath)}\nFrames totales: {self.total_frames}")
            if self.annotations_df is not None:
                self.display_frame(0)
    
    def load_csv(self):
        filepath = filedialog.askopenfilename(
            title="Sélectionner le fichier CSV d'annotations",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")]
        )
        if filepath:
            self.csv_path = filepath
            self.annotations_df = pd.read_csv(filepath)
            
            # Identifier les colonnes de comportement (toutes sauf 'Frame')
            self.behavior_columns = [col for col in self.annotations_df.columns if col != 'Frame']
            
            # Créer les checkboxes
            self.create_checkboxes()
            
            # Assigner les raccourcis clavier
            self.assign_keyboard_shortcuts()
            
            messagebox.showinfo("Succès", f"Annotations chargées: {os.path.basename(filepath)}\nFrames: {len(self.annotations_df)}\nComportements: {len(self.behavior_columns)}")
            
            if self.cap is not None:
                self.display_frame(0)
    
    def create_checkboxes(self):
        # Nettoyer les anciennes checkboxes
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()
        
        self.checkboxes = {}
        
        # Créer les checkboxes en grille (4 colonnes)
        for idx, behavior in enumerate(self.behavior_columns):
            row = idx // 4
            col = idx % 4
            
            var = tk.IntVar()
            # On ajoutera la lettre du raccourci plus tard
            cb = ttk.Checkbutton(self.checkbox_frame, text=behavior, variable=var)
            cb.grid(row=row, column=col, sticky=tk.W, padx=10, pady=5)
            
            self.checkboxes[behavior] = var
    
    def update_checkbox_labels(self):
        """Met à jour les labels des checkboxes avec les raccourcis clavier"""
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()
        
        for idx, behavior in enumerate(self.behavior_columns):
            row = idx // 4
            col = idx % 4
            
            # Trouver le raccourci pour ce comportement
            shortcut = ""
            for key, beh in self.keyboard_shortcuts.items():
                if beh == behavior:
                    shortcut = f" [{key.upper()}]"
                    break
            
            cb = ttk.Checkbutton(self.checkbox_frame, 
                               text=f"{behavior}{shortcut}", 
                               variable=self.checkboxes[behavior])
            cb.grid(row=row, column=col, sticky=tk.W, padx=10, pady=5)
    
    def display_frame(self, frame_idx):
        if self.cap is None or self.annotations_df is None:
            messagebox.showwarning("Attention", "Veuillez charger la vidéo et les annotations d'abord.")
            return
        
        if frame_idx < 0 or frame_idx >= len(self.annotations_df):
            messagebox.showwarning("Attention", f"Frame {frame_idx} hors limites.")
            return
        
        self.current_frame_idx = frame_idx
        
        # Lire la frame vidéo (Frame dans le CSV commence à 1, index vidéo à 0)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = self.cap.read()
        
        if ret:
            # Convertir pour affichage
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Target size
            target_w, target_h = 640, 480

            # Original size
            h, w = frame_rgb.shape[:2]
            ratio = min(target_w / w, target_h / h)
            new_w, new_h = int(w * ratio), int(h * ratio)

            # Resize without distortion
            frame_resized = cv2.resize(frame_rgb, (new_w, new_h))

            # Create a black canvas and center the resized frame
            canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
            x_offset = (target_w - new_w) // 2
            y_offset = (target_h - new_h) // 2
            canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = frame_resized

            img = Image.fromarray(canvas)
            imgtk = ImageTk.PhotoImage(image=img)

            self.video_label.configure(image=imgtk, text="")
            self.video_label.image = imgtk

        
        # Mettre à jour l'info de frame
        frame_number = self.annotations_df.iloc[frame_idx]['Frame']
        self.frame_info_label.config(text=f"Frame: {frame_number} / {len(self.annotations_df)}")
        
        # Afficher les annotations actuelles
        self.update_current_annotations(frame_idx)
        
        # Mettre à jour les checkboxes
        self.update_checkboxes(frame_idx)
        
        # Mettre à jour les labels avec raccourcis si nécessaire
        if hasattr(self, 'keyboard_shortcuts') and self.keyboard_shortcuts:
            self.update_checkbox_labels()
    
    def update_current_annotations(self, frame_idx):
        row = self.annotations_df.iloc[frame_idx]
        
        active_behaviors = []
        for behavior in self.behavior_columns:
            if row[behavior] == 1:
                active_behaviors.append(behavior)
        
        self.current_annotation_text.config(state=tk.NORMAL)
        self.current_annotation_text.delete(1.0, tk.END)
        
        if active_behaviors:
            self.current_annotation_text.insert(tk.END, "Comportements actifs:\n\n")
            for behavior in active_behaviors:
                self.current_annotation_text.insert(tk.END, f"  ✓ {behavior}\n")
        else:
            self.current_annotation_text.insert(tk.END, "Aucun comportement actif")
        
        self.current_annotation_text.config(state=tk.DISABLED)
    
    def update_checkboxes(self, frame_idx):
        row = self.annotations_df.iloc[frame_idx]
        
        for behavior in self.behavior_columns:
            self.checkboxes[behavior].set(int(row[behavior]))
    
    def next_frame(self):
        if self.current_frame_idx < len(self.annotations_df) - 1:
            self.display_frame(self.current_frame_idx + 1)
        else:
            messagebox.showinfo("Info", "Dernière frame atteinte.")
    
    def prev_frame(self):
        if self.current_frame_idx > 0:
            self.display_frame(self.current_frame_idx - 1)
        else:
            messagebox.showinfo("Info", "Première frame atteinte.")
    
    def jump_to_frame(self):
        try:
            frame_num = int(self.jump_entry.get())
            # Trouver l'index correspondant au numéro de frame
            frame_idx = self.annotations_df[self.annotations_df['Frame'] == frame_num].index
            if len(frame_idx) > 0:
                self.display_frame(frame_idx[0])
            else:
                messagebox.showerror("Erreur", f"Frame {frame_num} non trouvée dans les annotations.")
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer un numéro de frame valide.")
    
    def apply_to_range(self):
        """Applique les comportements cochés à une plage de frames"""
        if self.annotations_df is None:
            messagebox.showwarning("Attention", "Aucune annotation chargée.")
            return
        
        try:
            start_frame = int(self.range_start_entry.get())
            end_frame = int(self.range_end_entry.get())
            
            if start_frame > end_frame:
                messagebox.showerror("Erreur", "La frame de début doit être inférieure ou égale à la frame de fin.")
                return
            
            # Trouver les indices correspondants
            start_idx = self.annotations_df[self.annotations_df['Frame'] == start_frame].index
            end_idx = self.annotations_df[self.annotations_df['Frame'] == end_frame].index
            
            if len(start_idx) == 0 or len(end_idx) == 0:
                messagebox.showerror("Erreur", "Numéros de frame invalides.")
                return
            
            start_idx = start_idx[0]
            end_idx = end_idx[0]
            
            # Récupérer les valeurs des checkboxes
            checkbox_values = {}
            for behavior in self.behavior_columns:
                checkbox_values[behavior] = self.checkboxes[behavior].get()
            
            # Appliquer à toutes les frames de la plage
            for idx in range(start_idx, end_idx + 1):
                for behavior in self.behavior_columns:
                    self.annotations_df.at[idx, behavior] = checkbox_values[behavior]
            
            self.modified = True
            
            # Rafraîchir l'affichage
            self.update_current_annotations(self.current_frame_idx)
            
            num_frames = end_idx - start_idx + 1
            messagebox.showinfo("Succès", f"Annotations appliquées à {num_frames} frames (de {start_frame} à {end_frame}).")
            
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer des numéros de frame valides.")
    
    def confirm_correction(self):
        if self.annotations_df is None:
            return
        
        # Mettre à jour les annotations avec les valeurs des checkboxes
        for behavior in self.behavior_columns:
            self.annotations_df.at[self.current_frame_idx, behavior] = self.checkboxes[behavior].get()
        
        self.modified = True
        
        # Rafraîchir l'affichage
        self.update_current_annotations(self.current_frame_idx)
        
        
        messagebox.showinfo("Succès", f"Annotation de la frame {self.annotations_df.iloc[self.current_frame_idx]['Frame']} mise à jour.")
        
        # Passer à la frame suivante
        self.next_frame()
    
    def save_annotations(self):
        if self.annotations_df is None:
            messagebox.showwarning("Attention", "Aucune annotation à sauvegarder.")
            return
        
        if self.csv_path:
            self.annotations_df.to_csv(self.csv_path, index=False)
            self.modified = False
            messagebox.showinfo("Succès", f"Annotations sauvegardées dans {os.path.basename(self.csv_path)}")
        else:
            self.save_annotations_as()
    
    def save_annotations_as(self):
        if self.annotations_df is None:
            messagebox.showwarning("Attention", "Aucune annotation à sauvegarder.")
            return
        
        filepath = filedialog.asksaveasfilename(
            title="Sauvegarder les annotations",
            defaultextension=".csv",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")]
        )
        
        if filepath:
            self.annotations_df.to_csv(filepath, index=False)
            self.csv_path = filepath
            self.modified = False
            messagebox.showinfo("Succès", f"Annotations sauvegardées dans {os.path.basename(filepath)}")
    
    def quit_app(self):
        if self.modified:
            response = messagebox.askyesnocancel("Quitter", "Voulez-vous sauvegarder les modifications avant de quitter?")
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self.save_annotations()
        
        if self.cap is not None:
            self.cap.release()
        self.root.quit()

def main():
    root = tk.Tk()
    app = AnnotationCorrectionTool(root)
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    root.mainloop()

if __name__ == "__main__":
    main()
