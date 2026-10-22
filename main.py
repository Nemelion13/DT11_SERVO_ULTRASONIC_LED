import customtkinter as ctk
import threading
from Tools_arduino_tkinter import Thermometer, CircularCanvas, SerialManager


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Arduino Multi-Control Dashboard")
        self.geometry("900x650")
        self.data = {"Temperature": 0, "Humidity": 0, "Heat_index": 0, "Distance": 0}
        self.serial_manager = SerialManager(self)
        self.protocol("WM_DELETE_WINDOW", self.close)

        # --- GRID CONFIG ---
        self.grid_columnconfigure((0, 1, 2), weight=1)

        # 1. STATUS & THEME FRAME
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        self.status_led = ctk.CTkLabel(self.top_frame, text="●", text_color="red")
        self.status_led.pack(side="left", padx=10)
        
        self.statut_connection = ctk.CTkLabel(self.top_frame, text="Statut de la Connexion: Déconnecté")
        self.statut_connection.pack(side="left", padx=10)

        self.theme_menu = ctk.CTkOptionMenu(self.top_frame, values=["Light", "Dark"], command=ctk.set_appearance_mode)
        self.theme_menu.pack(side="right", padx=10)

        # 2. SENSOR DATA FRAME
        self.DHT_data_frame = ctk.CTkFrame(self)
        self.DHT_data_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(self.DHT_data_frame, text="Données Capteurs DHT", font=("Arial", 18, "bold")).pack(pady=10)
        
        self.ultrasonic_data_frame = ctk.CTkFrame(self)
        self.ultrasonic_data_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(self.ultrasonic_data_frame, text="Données Capteur Ultrason", font=("Arial", 18, "bold")).pack(pady=10)

         # Sensor Data Labels
        self.lbl_temp = ctk.CTkLabel(self.DHT_data_frame, text="Température: -- °C")
        self.lbl_temp.pack()
        self.lbl_hum = ctk.CTkLabel(self.DHT_data_frame, text="Humidité: -- %")
        self.lbl_hum.pack()
        self.lbl_heat = ctk.CTkLabel(self.DHT_data_frame, text="Indice de Chaleur: --")
        self.lbl_heat.pack()
        self.lbl_dist = ctk.CTkLabel(self.ultrasonic_data_frame, text="Distance: -- cm")
        self.lbl_dist.pack()
        self.led_alert = CircularCanvas(self.ultrasonic_data_frame,bg_color="#EBEBEB", size=100)
        self.led_alert.pack(pady=10)
        self.thermometer = Thermometer(self.DHT_data_frame, min_temp=0, max_temp=50, initial_temp=0)
        self.thermometer.pack(pady=10)
        #canva en cercle

        # 3. CONTROLS FRAME (LED & SERVO MODE)
        self.ctrl_frame = ctk.CTkFrame(self)
        self.ctrl_frame.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.ctrl_frame, text="Contrôles", font=("Arial", 18, "bold")).pack(pady=10)
        
        # LED
        ctk.CTkButton(self.ctrl_frame, text="LED ON", fg_color="green", command=lambda: self.send('L1')).pack(pady=5)
        ctk.CTkButton(self.ctrl_frame, text="LED OFF", fg_color="red", command=lambda: self.send('L0')).pack(pady=5)
        
        # SERVO MODE
        ctk.CTkLabel(self.ctrl_frame, text="Mode Servo:").pack(pady=(10,0))
        self.mode_menu = ctk.CTkOptionMenu(self.ctrl_frame, values=["Manuel (Python)", "Automatique"], command=self.change_servo_mode)
        self.mode_menu.pack(pady=5)

        # 4. SLIDER FRAME
        self.slider_frame = ctk.CTkFrame(self)
        self.slider_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.slider = ctk.CTkSlider(self.slider_frame, from_=0, to=180, command=self.srv_slider)
        self.slider.pack(fill="x", padx=20, pady=20)
        #Afficher la valeur du slider
        self.slider_value_label = ctk.CTkLabel(self.slider_frame, text="Position Servo: 0°")
        self.slider_value_label.pack()
        self.slider.configure(command=lambda val: [self.srv_slider(val), self.slider_value_label.configure(text=f"Position Servo: {int(float(val))}°")])

        
        threading.Thread(
            target=self.serial_manager.connect_serial,
            daemon=True,
        ).start()
        self.update_gui()

    def send(self, msg):
        self.serial_manager.send(msg)

    def change_servo_mode(self, mode):
        val = "1" if mode == "Automatique" else "0"
        self.send(f'M{val}')

    def srv_slider(self, val):
        self.send(f'S{int(val)}')

    def update_gui(self):
        self.lbl_temp.configure(text=f"Température: {self.data['Temperature']} °C")
        self.lbl_hum.configure(text=f"Humidité: {self.data['Humidity']} %")
        self.lbl_heat.configure(text=f"Indice de Chaleur: {self.data['Heat_index']}")
        self.lbl_dist.configure(text=f"Distance: {self.data['Distance']} cm")
        self.thermometer.set_temperature(self.data['Temperature'])
        if self.data['Distance'] < 15:
             self.led_alert.canvas.itemconfig(self.led_alert.circle_id, fill="red")
        else :
            self.led_alert.canvas.itemconfig(self.led_alert.circle_id,fill = 'green')
        
        self.after(500, self.update_gui)

    def close(self):
        self.serial_manager.disconnect_serial()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
    