import os
import urllib.request
import json

def load_local_settings():
  
    home = os.path.expanduser("~")
    settings_path = os.path.join(home, ".config", "applifey", "settings.json")
    defaults = {"show_branding": True, "default_browser": "brave", "language": "en"}
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                return {**defaults, **json.load(f)}
        except:
            return defaults
    return defaults

def get_installed_apps():

    home = os.path.expanduser("~")
    applications_dir = os.path.join(home, ".local", "share", "applications")
    installed = []
    
    if os.path.exists(applications_dir):
        for file in os.listdir(applications_dir):
            if file.startswith("applifey_") and file.endswith(".desktop"):
                path = os.path.join(applications_dir, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    name = ""
                    for line in lines:
                        if line.startswith("Name="):
                            name = line.split("=")[1].strip().replace(" (Applifey)", "")
                    if name:
                        installed.append((name, file))
                except:
                    pass
    return installed

def remove_pwa(desktop_file_name):

    home = os.path.expanduser("~")
    applications_dir = os.path.join(home, ".local", "share", "applications")
    config_dir = os.path.join(home, ".config", "applifey")
    
    file_path = os.path.join(applications_dir, desktop_file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        
    clean_name = desktop_file_name.replace("applifey_", "").replace(".desktop", "")
    icon_path = os.path.join(config_dir, "icons", f"{clean_name}.png")
    if os.path.exists(icon_path):
        os.remove(icon_path)

def create_pwa(app_name, url, browser="brave"):
    
    home = os.path.expanduser("~")
    config_dir = os.path.join(home, ".config", "applifey")
    icon_dir = os.path.join(config_dir, "icons")
    applications_dir = os.path.join(home, ".local", "share", "applications")
    
    os.makedirs(icon_dir, exist_ok=True)
    clean_name = app_name.lower().replace(" ", "_").replace("/", "")
    icon_path = os.path.join(icon_dir, f"{clean_name}.png")
    
    domain = url.split("//")[-1].split("/")[0]
    icon_url = "https://www.google.com/s2/favicons?sz=128&domain=" + ("whatsapp.com" if "whatsapp" in domain else domain)
    
    try:
        req = urllib.request.Request(icon_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(icon_path, 'wb') as out_file:
            out_file.write(response.read())
    except:
        icon_path = "utilities-terminal"

    if browser.lower() == "brave":
        exec_command = f"brave-browser --app={url}"
    elif browser.lower() in ["chrome", "google-chrome"]:
        exec_command = f"google-chrome --app={url}"
    elif browser.lower() == "chromium":
        exec_command = f"chromium --app={url}"
    else:
        exec_command = f"firefox --new-window {url}"

    settings = load_local_settings()
    is_de = settings.get("language", "en") == "de"
    
    if settings.get("show_branding", True):
        display_name = f"{app_name} (Applifey)"
        comment_text = "Web-App erstellt mit Applifey" if is_de else "Web-App created with Applifey"
    else:
        display_name = app_name
        comment_text = "Web-App"

    desktop_file_path = os.path.join(applications_dir, f"applifey_{clean_name}.desktop")
    desktop_entry = f"[Desktop Entry]\nVersion=1.0\nType=Application\nName={display_name}\nComment={comment_text}\nExec={exec_command}\nIcon={icon_path}\nTerminal=false\nCategories=Network;WebBrowser;\n"

    with open(desktop_file_path, "w", encoding="utf-8") as f:
        f.write(desktop_entry)
        
    os.chmod(desktop_file_path, 0o755)
    
    
    os.system("echo -e '\a'")
