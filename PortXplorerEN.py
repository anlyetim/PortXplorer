#PortXplorer
#Copyright (C) 2025 Anıl YETİM
#Licensed with MIT License.

#--------------------------------------------------------------

import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
import time
from queue import Queue

def Local_ip_al():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        yerel_ip = s.getsockname()[0]
        s.close()
        temel_ip = ".".join(yerel_ip.split(".")[:-1])
        return temel_ip, yerel_ip
    except Exception:
        return "192.168.1", "192.168.1.100"

class PortXplorer:
    def __init__(self):
        self.aktif_hostlar = []
        self.aktif_ipler = []
        self.kuyruk = Queue()
        self.lock = threading.Lock()  

    def Port_tarama(self, ip, port):
        soket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soket.settimeout(0.2)
        try:
            sonuc = soket.connect_ex((ip, port))
            if sonuc == 0:
                with self.lock:  
                    self.aktif_hostlar.append(f"{ip}:{port}")
        except socket.gaierror:
            pass
        finally:
            soket.close()

    def Calisan_port(self):
        while not self.kuyruk.empty():
            ip, port = self.kuyruk.get()
            self.Port_tarama(ip, port)
            self.kuyruk.task_done()

    def Hedef_tarama(self, hedef, baslangic_port, bitis_port, istek_sayisi=100):
        self.aktif_hostlar = []
        self.aktif_ipler = []

        if not hedef or hedef.strip() == "":
            return ["Error: Target cannot be empty."], ""

        try:
            socket.inet_aton(hedef)
            hedef_ip = hedef
        except socket.error:
            try:
                hedef_ip = socket.gethostbyname(hedef)
            except socket.gaierror:
                return ["Error: Invalid destination or DNS could not be resolved."], ""

        self.aktif_ipler = [hedef_ip]

        for ip in self.aktif_ipler:
            for port in range(baslangic_port, bitis_port + 1):
                self.kuyruk.put((ip, port))

        for _ in range(min(istek_sayisi, self.kuyruk.qsize())):
            is_parcasi = threading.Thread(target=self.Calisan_port)
            is_parcasi.daemon = True
            is_parcasi.start()
        self.kuyruk.join()

        return self.aktif_hostlar, hedef_ip

    def Ag_tarama(self, temel_ip, baslangic_port, bitis_port, istek_sayisi=100):
        self.aktif_hostlar = []
        self.aktif_ipler = []

        if not temel_ip or temel_ip.strip() == "":
            return ["Error: Base IP cannot be empty."], temel_ip

        for i in range(1, 255):
            ip = f"{temel_ip}.{i}"
            self.kuyruk.put((ip, 80))
        for _ in range(min(50, self.kuyruk.qsize())):
            is_parcasi = threading.Thread(target=self.Calisan_port)
            is_parcasi.daemon = True
            is_parcasi.start()
        self.kuyruk.join()

        for ip in self.aktif_ipler:
            for port in range(baslangic_port, bitis_port + 1):
                self.kuyruk.put((ip, port))

        for _ in range(min(istek_sayisi, self.kuyruk.qsize())):
            is_parcasi = threading.Thread(target=self.Calisan_port)
            is_parcasi.daemon = True
            is_parcasi.start()
        self.kuyruk.join()

        return self.aktif_hostlar, temel_ip

class UygulamaGUI:
    def __init__(self, root):  
        self.root = root
        self.root.title("PortXplorer")
        self.root.geometry("880x480")
        self.tarayici = PortXplorer()
        self.temel_ip, self.yerel_ip = Local_ip_al()

        sol_cerceve = tk.Frame(root)
        sol_cerceve.pack(side=tk.LEFT, anchor=tk.NW, padx=10, pady=10)

        tk.Label(sol_cerceve, text="Target (IP or Website):", anchor=tk.W).pack(anchor=tk.W, pady=5)
        self.hedef_girdi = tk.Entry(sol_cerceve)
        self.hedef_girdi.insert(0, self.temel_ip)
        self.hedef_girdi.pack(anchor=tk.W)

        tk.Label(sol_cerceve, text="First Port:", anchor=tk.W).pack(anchor=tk.W, pady=5)
        self.baslangic_port_girdisi = tk.Entry(sol_cerceve)
        self.baslangic_port_girdisi.insert(0, "1")
        self.baslangic_port_girdisi.pack(anchor=tk.W)

        tk.Label(sol_cerceve, text="Last Port:", anchor=tk.W).pack(anchor=tk.W, pady=5)
        self.bitis_port_girdisi = tk.Entry(sol_cerceve)
        self.bitis_port_girdisi.insert(0, "9999")
        self.bitis_port_girdisi.pack(anchor=tk.W)

        self.kendi_ip_tarama_degiskeni = tk.BooleanVar()
        tk.Checkbutton(sol_cerceve, text="Scan My IP Only", variable=self.kendi_ip_tarama_degiskeni, anchor=tk.W).pack(anchor=tk.W, pady=5)

        self.ag_tarama_degiskeni = tk.BooleanVar()
        tk.Checkbutton(sol_cerceve, text="Scan Local Network", variable=self.ag_tarama_degiskeni, anchor=tk.W).pack(anchor=tk.W, pady=5)

        self.tarama_butonu = tk.Button(sol_cerceve, text="Start Scan", command=self.Taramayi_baslat)
        self.tarama_butonu.pack(anchor=tk.W, pady=5)

        self.sonuc_metni = scrolledtext.ScrolledText(root, width=60, height=20)
        self.sonuc_metni.pack(side=tk.RIGHT, padx=10, pady=10)
        self.sonuc_metni.tag_configure("left", justify="left")

        self.durum = tk.Label(root, text=f"Your IP: {self.yerel_ip}", bd=1, relief=tk.SUNKEN, anchor=tk.W, justify=tk.LEFT)
        self.durum.pack(side=tk.BOTTOM, fill=tk.X)

    def Taramayi_baslat(self):
        self.tarama_butonu.config(state="disabled")
        self.sonuc_metni.delete(1.0, tk.END)
        self.durum.config(text="Scanning...", justify=tk.LEFT)

        hedef = self.hedef_girdi.get()
        try:
            baslangic_port = int(self.baslangic_port_girdisi.get())
            bitis_port = int(self.bitis_port_girdisi.get())
        except ValueError:
            self.sonuc_metni.insert(tk.END, "Error: Port numbers must be a valid number!\n", "left")
            self.tarama_butonu.config(state="normal")
            self.durum.config(text="Hata", justify=tk.LEFT)
            return

        def tarama_isi():
            baslangic_zamani = time.time()
            if self.kendi_ip_tarama_degiskeni.get():
                sonuclar, taranan_ip = self.tarayici.Hedef_tarama(self.yerel_ip, baslangic_port, bitis_port)
            elif self.ag_tarama_degiskeni.get():
                sonuclar, taranan_ip = self.tarayici.Ag_tarama(hedef, baslangic_port, bitis_port)
            else:
                sonuclar, taranan_ip = self.tarayici.Hedef_tarama(hedef, baslangic_port, bitis_port)
            gecen_zaman = time.time() - baslangic_zamani

            self.sonuc_metni.delete(1.0, tk.END)
            if sonuclar and isinstance(sonuclar, list) and "Error" not in sonuclar[0]:
                self.sonuc_metni.insert(tk.END, "Active Ports:\n", "left")
                for host in sonuclar:  
                    self.sonuc_metni.insert(tk.END, f"{host}\n", "left")
            else:
                self.sonuc_metni.insert(tk.END, sonuclar[0] if sonuclar else "No active port was found.\n", "left")
            self.sonuc_metni.insert(tk.END, f"\nScan completed in {gecen_zaman:.2f} sec.", "left")

            self.tarama_butonu.config(state="normal")
            self.durum.config(text=f"Scan Completed. (Scan IP: {taranan_ip})", justify=tk.LEFT)

        threading.Thread(target=tarama_isi, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()  
    app = UygulamaGUI(root)  
    root.mainloop()