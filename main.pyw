import customtkinter as ctk
import requests
from PIL import Image
import io
import threading
import os
import json
from tkinter import messagebox # 📦 Importiert das Pop-up-System

from applifey_core import create_pwa, load_local_settings, get_installed_apps, remove_pwa
from applifey_cloud import fetch_and_validate_apps

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

# 🌍 DIE ERWEITERTE ÜBERSETZUNGS-DATENBANK
TRANSLATIONS = {
    "en": {
        "settings_title": "Applifey - Settings & Manager",
        "settings_btn": "⚙️ Settings",
        "custom_btn": "➕ Custom App",
        "search_placeholder": "🔍 Search apps...",
        "install_btn": "Install",
        "branding_switch": "Append '(Applifey)' to app name",
        "manage_title": "📦 Manage Installed Web-Apps",
        "no_apps": "No apps installed via Applifey yet.",
        "delete_btn": "Delete",
        "done_btn": "Done",
        "custom_title": "Add Custom Web-App",
        "custom_header": "➕ Link Custom Web-App",
        "app_name_label": "App Name:",
        "app_name_placeholder": "e.g., My Online Banking",
        "url_label": "Web Address (URL):",
        "sys_install_btn": "Install on System",
        "language_label": "Language / Sprache:",
        "notify_title": "Success",
        "notify_msg": "is now ready! You can find it in your system menu."
    },
    "de": {
        "settings_title": "Applifey - Einstellungen & Manager",
        "settings_btn": "⚙️ Einstellungen",
        "custom_btn": "➕ Custom App",
        "search_placeholder": "🔍 Nach Apps suchen...",
        "install_btn": "Installieren",
        "branding_switch": "'(Applifey)' im Namen anhängen",
        "manage_title": "📦 Installierte Web-Apps verwalten",
        "no_apps": "Noch keine Apps über Applifey installiert.",
        "delete_btn": "Löschen",
        "done_btn": "Fertig",
        "custom_title": "Eigene App hinzufügen",
        "custom_header": "➕ Eigene Web-App verknüpfen",
        "app_name_label": "Name der App:",
        "app_name_placeholder": "z.B. Mein Online Banking",
        "url_label": "Web-Adresse (URL):",
        "sys_install_btn": "Auf dem System installieren",
        "language_label": "Sprache / Language:",
        "notify_title": "Erfolg",
        "notify_msg": "ist jetzt bereit! Du findest sie in deinem Startmenü."
    }
}

class CustomAppWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.lang = parent.lang
        self.title(TRANSLATIONS[self.lang]["custom_title"])
        self.geometry("450x300")
        self.resizable(False, False)
        
        self.transient(parent)
        self.withdraw()

        ctk.CTkLabel(self, text=TRANSLATIONS[self.lang]["custom_header"], font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        
        ctk.CTkLabel(self, text=TRANSLATIONS[self.lang]["app_name_label"], font=ctk.CTkFont(size=12)).pack(anchor="w", padx=40)
        self.name_entry = ctk.CTkEntry(self, placeholder_text=TRANSLATIONS[self.lang]["app_name_placeholder"], width=370)
        self.name_entry.pack(pady=(0, 15), padx=40)

        ctk.CTkLabel(self, text=TRANSLATIONS[self.lang]["url_label"], font=ctk.CTkFont(size=12)).pack(anchor="w", padx=40)
        self.url_entry = ctk.CTkEntry(self, placeholder_text="https://example.com", width=370)
        self.url_entry.pack(pady=(0, 20), padx=40)

        self.install_btn = ctk.CTkButton(self, text=TRANSLATIONS[self.lang]["sys_install_btn"], fg_color="#28A745", hover_color="#218838", command=self.add_custom)
        self.install_btn.pack(pady=10)

        self.after(100, self.show_and_grab)

    def show_and_grab(self):
        self.deiconify()
        self.grab_set()

    def add_custom(self):
        name = self.name_entry.get().strip()
        url = self.url_entry.get().strip()
        if name and url:
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            create_pwa(name, url, self.parent.browser_var.get())
            self.destroy()
            # Zeigt Benachrichtigung nach Custom-Installation
            messagebox.showinfo(TRANSLATIONS[self.lang]["notify_title"], f"'{name}' {TRANSLATIONS[self.lang]['notify_msg']}")


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.lang = parent.lang
        self.title(TRANSLATIONS[self.lang]["settings_title"])
        self.geometry("500x500")
        self.resizable(False, False)
        
        self.transient(parent)
        self.withdraw()
        
        self.home = os.path.expanduser("~")
        self.settings_path = os.path.join(self.home, ".config", "applifey", "settings.json")
        self.settings = load_local_settings()

        # Sprachauswahl-Dropdown
        ctk.CTkLabel(self, text=TRANSLATIONS[self.lang]["language_label"], font=ctk.CTkFont(size=12)).pack(anchor="w", padx=30, pady=(15, 0))
        self.lang_var = ctk.StringVar(value="English" if self.lang == "en" else "Deutsch")
        self.lang_dropdown = ctk.CTkOptionMenu(self, values=["English", "Deutsch"], variable=self.lang_var, command=self.change_language)
        self.lang_dropdown.pack(anchor="w", padx=30, pady=(5, 10))

        # Branding-Schalter
        self.branding_var = ctk.BooleanVar(value=self.settings.get("show_branding", True))
        self.branding_switch = ctk.CTkSwitch(
            self, text=TRANSLATIONS[self.lang]["branding_switch"], variable=self.branding_var, command=self.save_settings
        )
        self.branding_switch.pack(pady=10, padx=30, anchor="w")

        # App-Manager Titel
        self.manage_label = ctk.CTkLabel(self, text=TRANSLATIONS[self.lang]["manage_title"], font=ctk.CTkFont(size=16, weight="bold"))
        self.manage_label.pack(anchor="w", padx=30, pady=(15, 5))
        
        self.manager_frame = ctk.CTkScrollableFrame(self, fg_color="#F2F2F2", height=200)
        self.manager_frame.pack(fill="x", padx=30, pady=5)

        self.render_manager_list()

        self.done_btn = ctk.CTkButton(self, text=TRANSLATIONS[self.lang]["done_btn"], command=self.destroy, width=120)
        self.done_btn.pack(side="bottom", pady=15)
        self.after(100, self.show_and_grab)

    def show_and_grab(self):
        self.deiconify()
        self.grab_set()

    def change_language(self, choice):
        new_lang = "en" if choice == "English" else "de"
        self.settings["language"] = new_lang
        self.save_settings()
        self.parent.update_ui_language(new_lang)
        self.destroy()

    def render_manager_list(self):
        for widget in self.manager_frame.winfo_children():
            widget.destroy()

        apps = get_installed_apps()
        if not apps:
            ctk.CTkLabel(self.manager_frame, text=TRANSLATIONS[self.lang]["no_apps"], text_color="gray").pack(pady=40)
            return

        for name, file_name in apps:
            row = ctk.CTkFrame(self.manager_frame, fg_color="transparent")
            row.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(row, text=f"🌐 {name}", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
            
            del_btn = ctk.CTkButton(
                row, text=TRANSLATIONS[self.lang]["delete_btn"], fg_color="#DC3545", hover_color="#C82333", width=70, height=25,
                command=lambda f=file_name: self.delete_app(f)
            )
            del_btn.pack(side="right", padx=5)

    def delete_app(self, file_name):
        remove_pwa(file_name)
        self.render_manager_list()

    def save_settings(self):
        self.settings["show_branding"] = self.branding_var.get()
        os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4)


class ApplifeyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Applifey - Web-App Store")
        self.geometry("900x650")
        self.resizable(False, False)
        self.configure(fg_color="#FFFFFF")

        local_settings = load_local_settings()
        self.lang = local_settings.get("language", "en")

        self.loaded_icons = {}
        self.all_apps = fetch_and_validate_apps()

        # TOP BAR
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(pady=(20, 5), fill="x", padx=40)

        self.header_label = ctk.CTkLabel(self.top_bar, text="🥬 Applifey", font=ctk.CTkFont(family="Arial", size=36, weight="bold"), text_color="#1A1A1A")
        self.header_label.pack(side="left")

        self.settings_btn = ctk.CTkButton(self.top_bar, text=TRANSLATIONS[self.lang]["settings_btn"], font=ctk.CTkFont(size=13, weight="bold"), fg_color="#F2F2F2", hover_color="#E5E5E5", text_color="#1A1A1A", width=120, height=35, command=self.open_settings)
        self.settings_btn.pack(side="right")

        # CONTROL PANEL
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(pady=10, fill="x", padx=40)

        self.browser_var = ctk.StringVar(value=local_settings.get("default_browser", "brave"))
        self.browser_dropdown = ctk.CTkOptionMenu(self.control_frame, values=["brave", "chrome", "chromium", "firefox"], variable=self.browser_var, fg_color="#F2F2F2", button_color="#E5E5E5", text_color="#000000", width=120, command=self.save_default_browser)
        self.browser_dropdown.pack(side="left", padx=(0, 10))

        self.custom_btn = ctk.CTkButton(self.control_frame, text=TRANSLATIONS[self.lang]["custom_btn"], font=ctk.CTkFont(size=13, weight="bold"), fg_color="#007AFF", hover_color="#0056B3", text_color="#FFFFFF", height=35, command=self.open_custom_window)
        self.custom_btn.pack(side="left", padx=10)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.filter_apps)
        self.search_entry = ctk.CTkEntry(self.control_frame, placeholder_text=TRANSLATIONS[self.lang]["search_placeholder"], textvariable=self.search_var, fg_color="#F2F2F2", text_color="#1A1A1A", border_width=0, corner_radius=8, height=35)
        self.search_entry.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # SCROLL AREA
        self.grid_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.grid_frame.pack(expand=True, fill="both", padx=40, pady=(10, 20))
        self.grid_frame.bind_all("<Button-4>", lambda e: self.grid_frame._parent_canvas.yview_scroll(-1, "units"))
        self.grid_frame.bind_all("<Button-5>", lambda e: self.grid_frame._parent_canvas.yview_scroll(1, "units"))

        self.card_widgets = []
        self.render_apps(self.all_apps)

    def update_ui_language(self, new_lang):
        self.lang = new_lang
        self.settings_btn.configure(text=TRANSLATIONS[new_lang]["settings_btn"])
        self.custom_btn.configure(text=TRANSLATIONS[new_lang]["custom_btn"])
        self.search_entry.configure(placeholder_text=TRANSLATIONS[new_lang]["search_placeholder"])
        self.render_apps(self.all_apps)

    def open_settings(self):
        SettingsWindow(self)

    def open_custom_window(self):
        CustomAppWindow(self)

    def trigger_install(self, name, url):
        """Führt die Installation aus und zeigt direkt danach das mehrsprachige Pop-up."""
        create_pwa(name, url, self.browser_var.get())
        messagebox.showinfo(TRANSLATIONS[self.lang]["notify_title"], f"'{name}' {TRANSLATIONS[self.lang]['notify_msg']}")

    def save_default_browser(self, choice):
        home = os.path.expanduser("~")
        settings_path = os.path.join(home, ".config", "applifey", "settings.json")
        current_settings = load_local_settings()
        current_settings["default_browser"] = choice
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(current_settings, f, indent=4)

    def get_icon_async(self, domain, app_name, callback):
        def loader():
            try:
                target_domain = "whatsapp.com" if "whatsapp" in domain else domain
                url = f"https://www.google.com/s2/favicons?sz=64&domain={target_domain}"
                response = requests.get(url, timeout=3, headers={'User-Agent': 'Mozilla'})
                if response.status_code == 200:
                    img = Image.open(io.BytesIO(response.content))
                    ctk_img = ctk.CTkImage(light_image=img, size=(48, 48))
                    self.loaded_icons[app_name] = ctk_img
                    callback(ctk_img)
            except:
                pass
        threading.Thread(target=loader, daemon=True).start()

    def render_apps(self, app_list):
        for widget in self.card_widgets:
            widget.destroy()
        self.card_widgets = []

        columns = 3
        for index, (app_name, url) in enumerate(app_list):
            row = index // columns
            col = index % columns

            card = ctk.CTkFrame(self.grid_frame, fg_color="#F8F9FA", border_color="#E5E5E5", border_width=1, corner_radius=12, height=180)
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
            card.grid_propagate(False)
            self.card_widgets.append(card)

            icon_label = ctk.CTkLabel(card, text="📦", font=ctk.CTkFont(size=32))
            icon_label.pack(pady=(15, 5))

            def update_icon(loaded_img, label_widget=icon_label):
                label_widget.configure(image=loaded_img, text="")

            domain = url.split("//")[-1].split("/")[0]
            if app_name in self.loaded_icons:
                icon_label.configure(image=self.loaded_icons[app_name], text="")
            else:
                self.get_icon_async(domain, app_name, update_icon)

            label = ctk.CTkLabel(card, text=app_name, font=ctk.CTkFont(family="Arial", size=15, weight="bold"), text_color="#1A1A1A")
            label.pack(pady=5)

            # Button ruft jetzt trigger_install auf für Sound + Pop-up
            btn = ctk.CTkButton(
                card, text=TRANSLATIONS[self.lang]["install_btn"], font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#007AFF", hover_color="#0056B3", text_color="#FFFFFF", corner_radius=8, height=30,
                command=lambda name=app_name, target_url=url: self.trigger_install(name, target_url)
            )
            btn.pack(side="bottom", pady=(0, 15), padx=20)

        for i in range(columns):
            self.grid_frame.columnconfigure(i, weight=1)

    def filter_apps(self, *args):
        query = self.search_var.get().lower()
        filtered = [app for app in self.all_apps if query in app[0].lower()]
        self.render_apps(filtered)

if __name__ == "__main__":
    app = ApplifeyApp()
    app.mainloop()