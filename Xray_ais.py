import tkinter as tk
from tkinter import ttk, messagebox
import random
import math
from datetime import datetime
import numpy as np
from PIL import Image, ImageTk, ImageDraw
import io

class MaritimeSecuritySimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Maritime Security Simulator: AIS + X-ray Integration")
        self.root.geometry("1200x800")
        
        # Notebook for multi-tab interface
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # AIS Tab
        self.ais_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.ais_tab, text="AIS Monitoring")
        self.setup_ais_tab()
        
        # X-ray Tab
        self.xray_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.xray_tab, text="Container X-ray Scanner")
        self.setup_xray_tab()
        
        # Shared Data
        self.ships = []
        self.containers = []
        self.generate_initial_data()
        
        # Start simulation
        self.update_ais()
    
    def setup_ais_tab(self):
        """Configure the AIS monitoring interface"""
        # Map Canvas
        self.ais_canvas = tk.Canvas(self.ais_tab, width=800, height=500, bg='#001a33')
        self.ais_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Control Panel
        control_frame = ttk.Frame(self.ais_tab)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Add Ship", command=self.add_ship).pack(pady=5)
        ttk.Button(control_frame, text="Scan Selected", command=self.scan_selected_ship).pack(pady=5)
        
        # AIS Messages
        self.ais_msg = tk.Text(control_frame, width=40, height=20, wrap=tk.WORD)
        self.ais_msg.pack(pady=5)
        
        # Ship Info
        self.ship_info = ttk.Label(control_frame, text="No ship selected")
        self.ship_info.pack(pady=5)
        
        # Bind click event
        self.ais_canvas.bind("<Button-1>", self.select_ship)
    
    def setup_xray_tab(self):
        """Configure the X-ray scanner interface"""
        # X-ray Image
        self.xray_canvas = tk.Canvas(self.xray_tab, width=600, height=400, bg='black')
        self.xray_canvas.pack(pady=10)
        
        # Control Panel
        xray_controls = ttk.Frame(self.xray_tab)
        xray_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(xray_controls, text="New Scan", command=self.new_xray_scan).pack(side=tk.LEFT, padx=5)
        ttk.Button(xray_controls, text="Analyze", command=self.analyze_container).pack(side=tk.LEFT, padx=5)
        
        # Results
        result_frame = ttk.LabelFrame(self.xray_tab, text="Scan Results")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.result_text = tk.Text(result_frame, height=10, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # Threat indicators
        self.threat_indicator = ttk.Label(result_frame, text="STATUS: CLEAN", foreground="green")
        self.threat_indicator.pack()
    
    def generate_initial_data(self):
        """Create initial ships and containers"""
        # Create ships
        ship_types = {
            "Cargo": {"color": "green", "containers": True},
            "Tanker": {"color": "red", "containers": False},
            "Passenger": {"color": "white", "containers": False},
            "Fishing": {"color": "yellow", "containers": False}
        }
        
        for i in range(5):
            ship_type = random.choice(list(ship_types.keys()))
            self.ships.append({
                "mmsi": 100000000 + i,
                "name": f"{ship_type}-{i+1}",
                "type": ship_type,
                "color": ship_types[ship_type]["color"],
                "lat": 34.0 + random.random() * 0.5,
                "lon": -118.0 + random.random() * 0.5,
                "sog": random.uniform(0, 20),
                "cog": random.uniform(0, 360),
                "size": random.randint(20, 40),
                "has_containers": ship_types[ship_type]["containers"],
                "selected": False
            })
        
        # Create containers (some with threats)
        self.containers = []
        for i in range(20):
            self.containers.append({
                "id": f"CONT-{1000+i}",
                "ship_mmsi": random.choice([s["mmsi"] for s in self.ships if s["has_containers"]]),
                "threat": random.choice([None, "weapon", "drugs", "explosive"]) if random.random() < 0.2 else None
            })
    
    def latlon_to_xy(self, lat, lon):
        """Convert latitude/longitude to canvas coordinates"""
        x = (lon + 118.5) * 800 / 1.0
        y = (34.5 - lat) * 500 / 1.0
        return x, y
    
    def draw_ais_map(self):
        """Draw all ships on the AIS map"""
        self.ais_canvas.delete("all")
        
        # Draw grid lines
        for lon in [-118.5, -118.0, -117.5]:
            x, _ = self.latlon_to_xy(34.0, lon)
            self.ais_canvas.create_line(x, 0, x, 500, fill='#003366', dash=(2,2))
        
        for lat in [34.0, 34.5, 35.0]:
            _, y = self.latlon_to_xy(lat, -118.5)
            self.ais_canvas.create_line(0, y, 800, y, fill='#003366', dash=(2,2))
        
        # Draw port area
        port_x, port_y = self.latlon_to_xy(34.3, -118.2)
        self.ais_canvas.create_rectangle(port_x-100, port_y-50, port_x+100, port_y+50, 
                                       fill='#333333', outline='white')
        self.ais_canvas.create_text(port_x, port_y, text="PORT", fill='white')
        
        # Draw ships
        for ship in self.ships:
            x, y = self.latlon_to_xy(ship["lat"], ship["lon"])
            
            # Ship shape (triangle pointing in COG direction)
            angle = math.radians(ship["cog"])
            size = ship["size"]
            
            points = [
                x + math.sin(angle) * size,
                y - math.cos(angle) * size,
                x + math.sin(angle + 2.5) * size/2,
                y - math.cos(angle + 2.5) * size/2,
                x + math.sin(angle - 2.5) * size/2,
                y - math.cos(angle - 2.5) * size/2
            ]
            
            fill_color = ship["color"]
            outline = 'yellow' if ship["selected"] else 'black'
            width = 3 if ship["selected"] else 1
            
            self.ais_canvas.create_polygon(points, fill=fill_color, outline=outline, width=width)
            
            # Label
            self.ais_canvas.create_text(x, y-size-15, text=ship["name"], fill='white')
            
            # Course/speed indicator
            self.ais_canvas.create_line(
                x, y,
                x + math.sin(angle) * size*1.5,
                y - math.cos(angle) * size*1.5,
                arrow=tk.LAST, fill='white'
            )
    
    def update_ais(self):
        """Update ship positions and AIS data"""
        for ship in self.ships:
            # Update position based on course and speed
            ship["lat"] += 0.01 * math.cos(math.radians(ship["cog"])) * ship["sog"] / 10
            ship["lon"] += 0.01 * math.sin(math.radians(ship["cog"])) * ship["sog"] / 10
            
            # Random course/speed changes
            if random.random() < 0.1:
                ship["cog"] += random.uniform(-5, 5)
            if random.random() < 0.1:
                ship["sog"] += random.uniform(-1, 1)
            
            # Keep ships in bounds
            ship["lat"] = max(34.0, min(35.0, ship["lat"]))
            ship["lon"] = max(-118.5, min(-117.5, ship["lon"]))
        
        self.draw_ais_map()
        self.update_ais_messages()
        self.root.after(1000, self.update_ais)  # Update every second
    
    def update_ais_messages(self):
        """Generate current AIS messages"""
        self.ais_msg.delete(1.0, tk.END)
        
        for ship in self.ships:
            msg = (f"!AIVDM,1,1,,A,"
                  f"{ship['mmsi']:09d},"
                  f"{int(ship['lat']*600000):07d},"
                  f"{int(ship['lon']*600000):08d},"
                  f"{int(ship['sog']*10):04d},"
                  f"{int(ship['cog']):03d},"
                  f"{datetime.now().strftime('%H%M%S')},"
                  f"{ship['type'][0]},0*{random.randint(10,99):02d}")
            
            self.ais_msg.insert(tk.END, f"{ship['name']} (MMSI: {ship['mmsi']}):\n{msg}\n\n")
    
    def add_ship(self):
        """Add a new random ship to the simulation"""
        ship_types = ["Cargo", "Tanker", "Passenger", "Fishing"]
        ship_type = random.choice(ship_types)
        
        new_ship = {
            "mmsi": random.randint(100000000, 999999999),
            "name": f"{ship_type}-{len(self.ships)+1}",
            "type": ship_type,
            "color": {"Cargo": "green", "Tanker": "red", 
                     "Passenger": "white", "Fishing": "yellow"}[ship_type],
            "lat": 34.0 + random.random() * 0.5,
            "lon": -118.0 + random.random() * 0.5,
            "sog": random.uniform(0, 20),
            "cog": random.uniform(0, 360),
            "size": random.randint(20, 40),
            "has_containers": ship_type == "Cargo",
            "selected": False
        }
        
        self.ships.append(new_ship)
        
        # Add containers if cargo ship
        if new_ship["has_containers"]:
            for _ in range(random.randint(5, 15)):
                self.containers.append({
                    "id": f"CONT-{random.randint(2000, 9999)}",
                    "ship_mmsi": new_ship["mmsi"],
                    "threat": random.choice([None, "weapon", "drugs", "explosive"]) if random.random() < 0.2 else None
                })
    
    def select_ship(self, event):
        """Handle ship selection on the map"""
        x, y = event.x, event.y
        
        for ship in self.ships:
            ship["selected"] = False
        
        for ship in self.ships:
            sx, sy = self.latlon_to_xy(ship["lat"], ship["lon"])
            distance = math.hypot(x - sx, y - sy)
            
            if distance < ship["size"]:
                ship["selected"] = True
                self.show_ship_info(ship)
                break
        
        self.draw_ais_map()
    
    def show_ship_info(self, ship):
        """Display information about the selected ship"""
        info_text = (
            f"Ship Name: {ship['name']}\n"
            f"MMSI: {ship['mmsi']}\n"
            f"Type: {ship['type']}\n"
            f"Position: {ship['lat']:.4f}°N, {ship['lon']:.4f}°W\n"
            f"Course: {ship['cog']:.1f}°\n"
            f"Speed: {ship['sog']:.1f} knots\n"
            f"Containers: {'Yes' if ship['has_containers'] else 'No'}"
        )
        
        self.ship_info.config(text=info_text)
    
    def scan_selected_ship(self):
        """Initiate X-ray scan of selected ship's containers"""
        selected_ship = next((s for s in self.ships if s["selected"]), None)
        
        if not selected_ship:
            messagebox.showwarning("No Selection", "Please select a ship first")
            return
        
        if not selected_ship["has_containers"]:
            messagebox.showinfo("No Containers", "This ship type doesn't carry containers")
            return
        
        self.notebook.select(self.xray_tab)
        self.current_scan_ship = selected_ship["mmsi"]
        self.new_xray_scan()
    
    def new_xray_scan(self):
        """Generate a new X-ray image of a random container"""
        if not hasattr(self, 'current_scan_ship'):
            self.current_scan_ship = random.choice([s["mmsi"] for s in self.ships if s["has_containers"]])
        
        # Find containers from this ship
        ship_containers = [c for c in self.containers if c["ship_mmsi"] == self.current_scan_ship]
        
        if not ship_containers:
            messagebox.showwarning("No Containers", "No containers found on this ship")
            return
        
        # Select a random container
        self.current_container = random.choice(ship_containers)
        self.generate_xray_image()
        
        # Update UI
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, 
                              f"Scanning container {self.current_container['id']}\n"
                              f"From ship MMSI: {self.current_scan_ship}\n\n"
                              "Click 'Analyze' to detect threats")
        self.threat_indicator.config(text="STATUS: SCANNED", foreground="yellow")
    
    def generate_xray_image(self):
        """Create a synthetic X-ray image of a container"""
        width, height = 600, 400
        image = Image.new("RGB", (width, height), "black")
        draw = ImageDraw.Draw(image)
        
        # Draw container outline
        draw.rectangle([50, 50, width-50, height-50], outline="gray", width=2)
        
        # Draw random contents
        for _ in range(random.randint(5, 15)):
            x1 = random.randint(60, width-120)
            y1 = random.randint(60, height-120)
            x2 = x1 + random.randint(40, 150)
            y2 = y1 + random.randint(40, 100)
            
            # Different materials show differently in X-ray
            material = random.choice(["metal", "organic", "mixed"])
            if material == "metal":
                color = (random.randint(200, 255), random.randint(50, 150), random.randint(50, 150))
            elif material == "organic":
                color = (random.randint(50, 150), random.randint(200, 255), random.randint(50, 150))
            else:
                color = (random.randint(150, 200), random.randint(150, 200), random.randint(200, 255))
            
            draw.rectangle([x1, y1, x2, y2], fill=color)
            
            # Add threat if this container has one
            if self.current_container["threat"]:
                if random.random() < 0.8:  # 80% chance threat is visible
                    threat_x = random.randint(x1+10, x2-10)
                    threat_y = random.randint(y1+10, y2-10)
                    
                    if self.current_container["threat"] == "weapon":
                        draw.rectangle([threat_x-15, threat_y-5, threat_x+15, threat_y+5], fill="red")
                        draw.rectangle([threat_x-5, threat_y-15, threat_x+5, threat_y+5], fill="red")
                    elif self.current_container["threat"] == "drugs":
                        draw.ellipse([threat_x-10, threat_y-10, threat_x+10, threat_y+10], fill="yellow")
                    elif self.current_container["threat"] == "explosive":
                        draw.line([threat_x-10, threat_y-10, threat_x+10, threat_y+10], fill="red", width=3)
                        draw.line([threat_x+10, threat_y-10, threat_x-10, threat_y+10], fill="red", width=3)
        
        # Display image
        self.xray_image = image
        self.tk_image = ImageTk.PhotoImage(image)
        self.xray_canvas.delete("all")
        self.xray_canvas.create_image(width//2, height//2, image=self.tk_image)
    
    def analyze_container(self):
        """Analyze the current X-ray image for threats"""
        if not hasattr(self, 'current_container'):
            messagebox.showwarning("No Scan", "Please scan a container first")
            return
        
        self.result_text.delete(1.0, tk.END)
        
        if self.current_container["threat"]:
            # Simulate analysis with 85% accuracy
            if random.random() < 0.85:
                threat_desc = {
                    "weapon": "Firearm components detected",
                    "drugs": "Organic anomaly consistent with narcotics",
                    "explosive": "Potential explosive device identified"
                }[self.current_container["threat"]]
                
                self.result_text.insert(tk.END, 
                                      f"THREAT DETECTED!\n\n"
                                      f"Container ID: {self.current_container['id']}\n"
                                      f"Threat Type: {self.current_container['threat'].upper()}\n"
                                      f"Confidence: {random.randint(75, 95)}%\n\n"
                                      f"Details: {threat_desc}", "threat")
                self.result_text.tag_config("threat", foreground="red")
                self.threat_indicator.config(text="STATUS: THREAT DETECTED", foreground="red")
                
                # Highlight threat area
                self.xray_canvas.create_rectangle(
                    random.randint(100, 500),
                    random.randint(100, 300),
                    random.randint(150, 550),
                    random.randint(150, 350),
                    outline="red", width=3
                )
            else:
                self.result_text.insert(tk.END, 
                                      f"Analysis complete\n\n"
                                      f"Container ID: {self.current_container['id']}\n"
                                      f"Status: CLEAR\n\n"
                                      "No threats detected", "clear")
                self.result_text.tag_config("clear", foreground="green")
                self.threat_indicator.config(text="STATUS: CLEAR", foreground="green")
        else:
            # 10% chance of false positive
            if random.random() < 0.1:
                self.result_text.insert(tk.END, 
                                      f"POTENTIAL THREAT\n\n"
                                      f"Container ID: {self.current_container['id']}\n"
                                      f"False positive detected\n"
                                      f"Confidence: {random.randint(40, 60)}%\n\n"
                                      "Recommend manual inspection", "warning")
                self.result_text.tag_config("warning", foreground="orange")
                self.threat_indicator.config(text="STATUS: INSPECTION NEEDED", foreground="orange")
            else:
                self.result_text.insert(tk.END, 
                                      f"Analysis complete\n\n"
                                      f"Container ID: {self.current_container['id']}\n"
                                      f"Status: CLEAR\n\n"
                                      "No threats detected", "clear")
                self.result_text.tag_config("clear", foreground="green")
                self.threat_indicator.config(text="STATUS: CLEAR", foreground="green")

if __name__ == "__main__":
    root = tk.Tk()
    app = MaritimeSecuritySimulator(root)
    root.mainloop()