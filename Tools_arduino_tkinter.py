import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk
import json
import math
import threading
import time
import serial
import serial.tools.list_ports
from datetime import datetime

class Thermometer(ctk.CTkFrame):
    def __init__(self, master, min_temp=-20, max_temp=50, initial_temp=20,
                 width=90, height=150, **kwargs):
        super().__init__(master, width=width, height=height, **kwargs)
        
        self.min_temp = min_temp
        self.max_temp = max_temp
        self.temperature = initial_temp
        
        # Import tkinter pour le Canvas
        import tkinter as tk
        
        # Canvas pour dessiner le thermomètre
        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=self.cget("fg_color")[1] if ctk.get_appearance_mode() == "Dark" 
               else self.cget("fg_color")[0],
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Variables de dimension
        self.canvas_width = width
        self.canvas_height = height
        
        # Label pour afficher la température
        self.temp_label = ctk.CTkLabel(
            self,
            text=f"{self.temperature}°C",
            font=("Arial", 20, "bold"),
            text_color="white"
        )
        self.temp_label.place(relx=0.5, rely=0.95, anchor="center")
        
        # Dessiner le thermomètre initial
        self.draw_thermometer()
    
    def draw_thermometer(self):
        """Dessine le thermomètre complet"""
        self.canvas.delete("all")
        
        w, h = self.canvas_width, self.canvas_height
        
        # Calcul des positions
        bulb_radius = w // 3
        tube_width = w // 4
        tube_height = h - 50
        tube_top = 30
        tube_bottom = tube_top + tube_height
        bulb_center_x = w // 2
        bulb_center_y = tube_bottom + bulb_radius - 5
        
        # 1. Dessiner le bulbe (partie basse)
        bulb_color = self.get_temperature_color(self.temperature)
        self.canvas.create_oval(
            bulb_center_x - bulb_radius,
            bulb_center_y - bulb_radius,
            bulb_center_x + bulb_radius,
            bulb_center_y + bulb_radius,
            fill=bulb_color,
            outline="#333333",
            width=2
        )
        
        # 2. Dessiner le tube
        tube_left = bulb_center_x - tube_width // 2
        tube_right = bulb_center_x + tube_width // 2
        
        # Tube vide (fond)
        self.canvas.create_rectangle(
            tube_left,
            tube_top,
            tube_right,
            tube_bottom,
            fill="#E0E0E0",
            outline="#333333",
            width=2
        )
        
        # 3. Calculer et dessiner le mercure
        temp_range = self.max_temp - self.min_temp
        if temp_range > 0:
            # Hauteur du mercure proportionnelle à la température
            mercury_height = ((self.temperature - self.min_temp) / temp_range) * (tube_bottom - tube_top)
            mercury_top = tube_bottom - mercury_height
            
            # S'assurer que le mercure ne dépasse pas
            mercury_top = max(tube_top, mercury_top)
            
            # Couleur du mercure selon la température
            mercury_color = self.get_temperature_color(self.temperature)
            
            # Dessiner le mercure
            self.canvas.create_rectangle(
                tube_left + 2,
                mercury_top,
                tube_right - 2,
                tube_bottom,
                fill=mercury_color,
                outline="",
                width=0
            )
            
            # Ajouter un effet de brillance sur le mercure
            self.canvas.create_line(
                tube_left + 3,
                mercury_top + 10,
                tube_left + 3,
                tube_bottom - 10,
                fill="white",
                width=1
            )
        
        # 4. Dessiner les graduations
        self.draw_graduations(tube_left, tube_top, tube_right, tube_bottom)
        
        # 5. Ajouter un petit cercle de connexion tube/bulbe
        self.canvas.create_oval(
            bulb_center_x - tube_width // 2,
            tube_bottom - 5,
            bulb_center_x + tube_width // 2,
            tube_bottom + 5,
            fill=bulb_color,
            outline="#333333",
            width=2
        )
    
    def draw_graduations(self, left, top, right, bottom):
        """Dessine les graduations du thermomètre"""
        # Graduations principales tous les 10 degrés
        for temp in range(self.min_temp, self.max_temp + 1, 10):
            if self.min_temp < temp < self.max_temp:
                # Position de la graduation
                ratio = (temp - self.min_temp) / (self.max_temp - self.min_temp)
                y = bottom - ratio * (bottom - top)
                
                # Ligne de graduation
                self.canvas.create_line(
                    right + 5,
                    y,
                    right + 15,
                    y,
                    fill="black",
                    width=2
                )
                
                # Texte de la température
                self.canvas.create_text(
                    right + 25,
                    y,
                    text=f"{temp}°",
                    fill="white" if ctk.get_appearance_mode() == "Dark" else "black",
                    font=("Arial", 10)
                )
        
        # Graduations mineures tous les 2 degrés
        for temp in range(self.min_temp, self.max_temp + 1, 2):
            if self.min_temp < temp < self.max_temp and temp % 10 != 0:
                ratio = (temp - self.min_temp) / (self.max_temp - self.min_temp)
                y = bottom - ratio * (bottom - top)
                
                self.canvas.create_line(
                    right + 5,
                    y,
                    right + 10,
                    y,
                    fill="gray",
                    width=1
                )
    
    def get_temperature_color(self, temp):
        """Retourne une couleur en fonction de la température"""
        # Échelle de couleur du froid au chaud
        if temp <= -10:
            return "#1E90FF"  # Bleu très froid
        elif temp <= 0:
            return "#87CEEB"  # Bleu froid
        elif temp <= 10:
            return "#98FB98"  # Vert clair frais
        elif temp <= 15 :
            return "#DDA0D0"
        elif temp <= 20:
            return "#FFD700"  # Jaune doux
        elif temp <= 30:
            return "#FF8C00"  # Orange
        elif temp <= 40:
            return "#FF4500"  # Rouge-orange
        else:
            return "#DC143C"  # Rouge vif très chaud
    
    def set_temperature(self, temp):
        """Définit la température et met à jour l'affichage"""
        # Limiter la température aux bornes
        self.temperature = max(self.min_temp, min(self.max_temp, temp))
        
        # Mettre à jour le label
        self.temp_label.configure(
            text=f"{self.temperature}°C",
            text_color=self.get_text_color(self.temperature)
        )
        
        # Redessiner le thermomètre
        self.draw_thermometer()
    
    def get_text_color(self, temp):
        """Couleur du texte selon la température"""
        if temp > 35:
            return "#FF0000"  # Rouge pour températures dangereuses
        elif temp < 0:
            return "#1E90FF"  # Bleu pour températures froides
        else:
            return "white"
    
    def get_temperature(self):
        """Retourne la température actuelle"""
        return self.temperature
    


class CircularProgressBar(ctk.CTkFrame):
    def __init__(self, master, width=300, height=300, 
                 progress_color="#FF6B6B", bg_color="#2B2B2B", 
                 line_width=15, **kwargs):
        super().__init__(master, width=width, height=height, **kwargs)
        
        self.width = width
        self.height = height
        self.progress_color = progress_color
        self.bg_color = bg_color
        self.line_width = line_width
        self.progress = 0
        
        # Canvas pour dessiner
        import tkinter as tk
        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=self.cget("fg_color")[1] if ctk.get_appearance_mode() == "Dark" else self.cget("fg_color")[0],
            highlightthickness=0
        )
        self.canvas.pack()
        
        # Labels pour le texte
        self.center_label = ctk.CTkLabel(
            self,
            text="0%",
            font=("Arial", 24, "bold")
        )
        self.center_label.place(relx=0.5, rely=0.4, anchor="center")
        
        self.title_label = ctk.CTkLabel(
            self,
            text="Progression",
            font=("Arial", 14)
        )
        self.title_label.place(relx=0.5, rely=0.6, anchor="center")
        
        # Dessiner le cercle initial
        self.draw_circle()
        
        # Contrôles
        self.create_controls()
    
    def draw_circle(self):
        """Dessine le cercle de progression"""
        self.canvas.delete("all")
        
        center_x = self.width // 2
        center_y = self.height // 2
        radius = min(center_x, center_y) - self.line_width - 5
        
        # Cercle de fond
        self.canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            outline="#444444",
            width=self.line_width
        )
        
        # Cercle de progression
        if self.progress > 0:
            start_angle = 90  # Commence en haut
            extent = -self.progress * 3.6  # 360° pour 100%
            
            self.canvas.create_arc(
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
                start=start_angle,
                extent=extent,
                outline=self.progress_color,
                width=self.line_width,
                style="arc"
            )
    
    def create_controls(self):
        """Crée les contrôles pour modifier la progression"""
        controls_frame = ctk.CTkFrame(self)
        controls_frame.place(relx=0.5, rely=0.85, anchor="center")
        
        # Bouton -
        ctk.CTkButton(
            controls_frame,
            text="-",
            width=40,
            command=lambda: self.set_progress(max(0, self.progress - 10))
        ).pack(side="left", padx=5)
        
        # Slider
        self.slider = ctk.CTkSlider(
            controls_frame,
            from_=0,
            to=100,
            command=self.on_slider_change,
            width=150
        )
        self.slider.pack(side="left", padx=10)
        
        # Bouton +
        ctk.CTkButton(
            controls_frame,
            text="+",
            width=40,
            command=lambda: self.set_progress(min(100, self.progress + 10))
        ).pack(side="left", padx=5)
    
    def set_progress(self, value):
        """Définit la valeur de progression"""
        self.progress = value
        self.slider.set(value)
        self.update_display()
    
    def on_slider_change(self, value):
        """Callback du slider"""
        self.progress = float(value)
        self.update_display()
    
    def update_display(self):
        """Met à jour l'affichage"""
        self.draw_circle()
        self.center_label.configure(text=f"{self.progress:.0f}%")
        
        # Changer la couleur selon la valeur
        if self.progress < 30:
            color = "#FF6B6B"  # Rouge
        elif self.progress < 70:
            color = "#FFD93D"  # Jaune
        else:
            color = "#6BCF7F"  # Vert
        
        self.progress_color = color
        self.draw_circle()



class CircularCanvas(ctk.CTkFrame):
    def __init__(self, master, size=200, bg_color="white", **kwargs):
        super().__init__(master, **kwargs)
        
        # Créer un canvas Tkinter standard (car CTkCanvas n'existe pas)
        import tkinter as tk
        self.canvas = tk.Canvas(
            self,
            width=size,
            height=size,
            bg=bg_color,
            highlightthickness=0
        )
        self.canvas.pack()
        
        # Dessiner un cercle
        self.circle_id = self.canvas.create_oval(
            5, 5, size-5, size-5,
            outline="#D0A13B",
            width=3,
            fill="#1FA526"
        )
        
        # Configurer le frame
        self.configure(width=size, height=size)
    
    def draw_progress(self, percentage):
        """Dessine un cercle de progression"""
        size = self.canvas.winfo_width()
        if size <= 1:  # Si pas encore affiché
            size = 200
        
        # Effacer l'ancien arc
        if hasattr(self, 'arc_id'):
            self.canvas.delete(self.arc_id)
        
        # Dessiner un arc de cercle
        self.arc_id = self.canvas.create_arc(
            5, 5, size-5, size-5,
            start=90,
            extent=percentage * -3.6,  # 360° pour 100%
            outline="#FFD700",
            width=5,
            style="arc"
        )
    
    def add_text(self, text, font_size=20):
        """Ajoute du texte au centre du cercle"""
        size = self.canvas.winfo_width() // 2
        self.text_id = self.canvas.create_text(
            size, size,
            text=text,
            fill="white",
            font=("Arial", font_size, "bold")
        )


class SerialManager:
    def __init__(self, parent_app):
        self.parent = parent_app
        self.ser = None
        self.is_connected = False
        self.should_monitor = False
        self.monitor_thread = None
        self.reading_thread = None
        self.port = None
        self.baudrate = 9600
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
    def connect_serial(self, port=None, baudrate=9600):
        """Tente de se connecter au port série"""
        port = port or self.port or self.find_arduino_port()
        if port is None:
            self.update_ui_status("Aucun Arduino détecté", "red")
            self.start_monitoring()
            return False

        self.port = port
        self.baudrate = baudrate
        print(self.port)

        try:
            previous_connection = self.ser
            self.is_connected = False
            if previous_connection and previous_connection.is_open:
                previous_connection.close()
            if self.reading_thread and self.reading_thread.is_alive():
                self.reading_thread.join(timeout=1)
            
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=0.1,
                write_timeout=1
            )
            
            # Attendre que l'Arduino soit prêt
            time.sleep(2)
            
            # The Arduino firmware has no handshake; opening the port is the connection test.
            self.is_connected = True
            self.reconnect_attempts = 0
            self.update_ui_status(f"Connecté à {port}", "green")
            
            self.start_monitoring()
            self.start_reading()
            
            return True
                
        except serial.SerialException as e:
            error_msg = str(e)
            if "Access is denied" in error_msg:
                self.update_ui_status("Port déjà utilisé", "orange")
            elif "could not open port" in error_msg:
                self.update_ui_status("Port non disponible", "orange")
            else:
                self.update_ui_status(f"Erreur: {error_msg[:30]}...", "orange")
            self.start_monitoring()
            return False
        except OSError as e:
            self.update_ui_status(f"Erreur port série: {e}", "red")
            self.start_monitoring()
            return False
        except Exception as e:
            self.update_ui_status(f"Erreur: {type(e).__name__}", "red")
            self.start_monitoring()
            return False
    
    def find_arduino_port(self):
        """Cherche automatiquement le port de l'Arduino"""
        ports = serial.tools.list_ports.comports()
       
        
        
        for port in ports:
            # Vérifier les caractéristiques typiques d'Arduino
            if ('Arduino' in port.description or 
                'CH340' in port.description or  # Chipsets courants pour clones Arduino
                'USB2.0-Serial' in port.description or
                'ttyACM' in port.device or  # Linux
                'ttyUSB' in port.device):   # Linux
                return port.device
        
        # Si pas trouvé, prendre le premier port disponible
        if ports:
            return ports[0].device
        
        return None
    
    def test_connection(self):
        """Vérifie que le port série actuellement ouvert est encore accessible."""
        try:
            if not self.ser or not self.ser.is_open:
                return False
            
            self.ser.in_waiting
            return True
        except (serial.SerialException, OSError):
            return False
    
    def start_monitoring(self):
        """Démarre le thread de monitoring de la connexion"""
        self.should_monitor = True
        if self.monitor_thread is None or not self.monitor_thread.is_alive():
            self.monitor_thread = threading.Thread(
                target=self.monitor_connection,
                daemon=True
            )
            self.monitor_thread.start()
    
    def monitor_connection(self):
        """Surveille la connexion en arrière-plan"""
        while self.should_monitor:
            time.sleep(2)  # Vérifier toutes les 2 secondes
            
            if not self.is_connected:
                # Tentative de reconnexion automatique
                self.auto_reconnect()
            else:
                # Vérifier si la connexion est toujours active
                if not self.check_connection():
                    self.is_connected = False
                    self.update_ui_status("Déconnecté", "red")
    
    def check_connection(self):
        """Vérifie si la connexion est toujours active"""
        return self.test_connection()

    def send(self, message):
        """Envoie une commande à l'Arduino si le port est ouvert."""
        if not self.ser or not self.ser.is_open:
            return False

        try:
            self.ser.write(message.encode("utf-8"))
            return True
        except (serial.SerialException, OSError) as e:
            self.is_connected = False
            self.update_ui_status(f"Erreur d'envoi série: {e}", "red")
            return False
    
    def auto_reconnect(self):
        """Tente de se reconnecter automatiquement"""
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            self.update_ui_status(
                f"Tentative de reconnexion ({self.reconnect_attempts}/{self.max_reconnect_attempts})", 
                "orange"
            )
            
            # Attendre un peu avant de réessayer
            time.sleep(2)
            
            # Tenter de se reconnecter
            if self.connect_serial():
                self.update_ui_status("Reconnecté automatiquement", "green")
                return True
        
        return False
    
    def start_reading(self):
        """Démarre la lecture des données en continu"""
        if self.reading_thread and self.reading_thread.is_alive():
            return
        self.reading_thread = threading.Thread(
            target=self.read_serial_data,
            args=(self.ser,),
            daemon=True
        )
        self.reading_thread.start()
    
    def read_serial_data(self, connection):
        """Lit les données série en continu"""
        buffer = ""
        while self.is_connected and self.ser is connection:
            try:
                if connection and connection.is_open:
                    # Lire les données disponibles
                    data = connection.read(connection.in_waiting or 1)
                    
                    if data:
                        # Convertir en texte
                        text = data.decode('utf-8', errors='ignore')
                        buffer += text
                        
                        # Traiter les lignes complètes
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()
                            if line:
                                self.process_data(line)
                
                time.sleep(0.01)  # Petite pause pour éviter la surcharge CPU
                
            except (serial.SerialException, OSError):
                if self.ser is connection:
                    self.is_connected = False
                    self.update_ui_status("Erreur de lecture", "red")
                break
            except Exception as e:
                print(f"Erreur lecture: {e}")
                time.sleep(1)
    
    def process_data(self, data):
        """Transmet les données reçues à l'interface sur son thread."""
        self.parent.after(0, self.update_data_ui, data)
    
    def update_data_ui(self, data):
        """Décode une ligne JSON et actualise les mesures de l'application."""
        try:
            payload = json.loads(data)
        except json.JSONDecodeError as e:
            print(f"Erreur JSON reçue de l'Arduino: {e}")
            return

        if not isinstance(payload, dict):
            print("Erreur: les données reçues de l'Arduino ne sont pas un objet JSON.")
            return

        if hasattr(self.parent, "data"):
            self.parent.data.update(payload)
    
    def disconnect_serial(self):
        """Déconnecte proprement le port série"""
        self.should_monitor = False
        self.is_connected = False
        
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except (serial.SerialException, OSError) as e:
                print(f"Erreur fermeture du port série: {e}")
        
        self.update_ui_status("Déconnecté", "red")
    
    def update_ui_status(self, message, color):
        """Met à jour le statut dans l'interface utilisateur"""
        if hasattr(self.parent, 'after'):
            self.parent.after(0, self._update_ui, message, color)
    
    def _update_ui(self, message, color):
        """Méthode interne pour mettre à jour l'UI de manière thread-safe"""
        if hasattr(self.parent, 'status_led'):
            self.parent.status_led.configure(text_color=color)
        
        if hasattr(self.parent, 'statut_connection'):
            self.parent.statut_connection.configure(
                text=f"Statut de la Connexion: {message}"
            )
        
        if hasattr(self.parent, 'log_text'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.parent.log_text.insert(
                "end",
                f"[{timestamp}] {message}\n"
            )
            self.parent.log_text.see("end")