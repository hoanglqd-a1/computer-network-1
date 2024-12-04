import customtkinter as ctk
from PIL import Image

def CenterWindowToDisplay(Screen: ctk.CTk, width: int, height: int):
    """Centers the window to the main display/monitor"""
    screen_width = Screen.winfo_screenwidth()
    screen_height = Screen.winfo_screenheight()
    x = int((screen_width/2) - (width/2))
    y = int((screen_height/2) - (height/2))
    return f"{width}x{height}+{x}+{y}"

def change_appearanceMode(new_appearance_mode: str):
    ctk.set_appearance_mode(new_appearance_mode)   

def change_widgetSize(new_scale_size: str):
    new_scaling_float = int(new_scale_size.replace("%", "")) / 100
    ctk.set_widget_scaling(new_scaling_float)
    
class login(ctk.CTk):
    port_no: int 
    folder_name: str
    
    def __init__(self):
        super().__init__()
        self.geometry(CenterWindowToDisplay(self, 600, 480))
        self.resizable(0, 0)
        
        self.side_img_data = Image.open("icons/login-image.jpg")
        self.port_icon_data = Image.open("icons/port-icon.png")
        self.folder_icon_data = Image.open("icons/folder.png")
        
        self.side_img = ctk.CTkImage(dark_image=self.side_img_data, light_image=self.side_img_data, size=(300,480))
        self.port_icon = ctk.CTkImage(dark_image=self.port_icon_data, light_image=self.port_icon_data, size=(20,20))
        self.folder_icon = ctk.CTkImage(dark_image=self.folder_icon_data, light_image=self.folder_icon_data, size=(17,17))
        
        ctk.CTkLabel(self, text="", image=self.side_img).pack(expand=True, side="left")
        
        self.login_frame = ctk.CTkFrame(self, width=300, height=480, fg_color="#ffffff")
        self.login_frame.pack_propagate(0)
        self.login_frame.pack(expand=True, side="right")
        
        ctk.CTkLabel(self.login_frame, text="Welcome!", text_color="#601E88", anchor="w", justify="left", font=("Arial Bold", 24)).pack(anchor="w", pady=(50, 5), padx=(25, 0))
        ctk.CTkLabel(self.login_frame, text="Sign in your port", text_color="#7E7E7E", anchor="w", justify="left", font=("Arial Bold", 12)).pack(anchor="w", padx=(25, 0))
        
        ctk.CTkLabel(self.login_frame, text="  Port number:", text_color="#601E88", anchor="w", justify="left", font=("Arial Bold", 14), image=self.port_icon, compound="left").pack(anchor="w", pady=(38, 0), padx=(25, 0))
        self.port_input = ctk.CTkEntry(self.login_frame, width=225, fg_color="#EEEEEE", border_color="#601E88", border_width=1, text_color="#000000")
        self.port_input.pack(anchor="w", padx=(25, 0))
        ctk.CTkLabel(self.login_frame, text="  Name:", text_color="#601E88", anchor="w", justify="left", font=("Arial Bold", 14), image=self.folder_icon, compound="left").pack(anchor="w", pady=(38, 0), padx=(25, 0))
        self.folder_input = ctk.CTkEntry(self.login_frame, width=225, fg_color="#EEEEEE", border_color="#601E88", border_width=1, text_color="#000000")
        self.folder_input.pack(anchor="w", padx=(25, 0))
        
        bt = ctk.CTkButton(self.login_frame, text="Open chat", fg_color="#601E88", hover_color="#E44982", font=("Arial Bold", 12), text_color="#ffffff", width=225, command= self.set_value)
        bt.pack(anchor="w", pady=(40, 0), padx=(25, 0))
        bt.bind("<Return>", lambda event: self.set_value())
        
        self.mainloop()
        
    def set_value(self):
        self.port_no = self.port_input.get()
        self.folder_name = self.folder_input.get()
        self.destroy()

    