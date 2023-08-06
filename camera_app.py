import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import datetime
import os
import subprocess
import sys

class CameraApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Camera Application")
        self.geometry("800x600")
        self.camera = cv2.VideoCapture(0)
        self.camera_frame = tk.Frame(self)
        self.camera_frame.pack(fill=tk.BOTH, expand=True)
        self.video_stream = tk.Label(self.camera_frame)
        self.video_stream.pack(fill=tk.BOTH, expand=True)
        self.control_frame = tk.Frame(self)
        self.control_frame.pack(pady=10)
        self.btn_capture = tk.Button(self.control_frame, text="Capture Image", command=self.capture_image)
        self.btn_capture.pack(side=tk.LEFT, padx=10)
        self.btn_record = tk.Button(self.control_frame, text="Record Video", command=self.toggle_record)
        self.btn_record.pack(side=tk.LEFT, padx=10)
        self.btn_gallery = tk.Button(self.control_frame, text="Gallery", command=self.open_gallery)
        self.btn_gallery.pack(side=tk.LEFT, padx=10)
        self.is_recording = False
        self.video_writer = None
        self.btn_quit = tk.Button(self.control_frame, text="Quit", command=self.quit_app)
        self.btn_quit.pack(side=tk.LEFT, padx=10)
        self.update_video_stream()

    def update_video_stream(self):
        ret, frame = self.camera.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(image=img)
            self.video_stream.img_tk = img_tk
            self.video_stream.config(image=img_tk)
            if self.is_recording:
                self.video_writer.write(frame)
        self.after(10, self.update_video_stream)

    def capture_image(self):
        ret, frame = self.camera.read()
        if ret:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"captured_image_{timestamp}.png"
            cv2.imwrite(file_name, frame)
            print(f"Image captured and saved as {file_name}")

    def toggle_record(self):
        if not self.is_recording:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"recorded_video_{timestamp}.avi"
            self.video_writer = cv2.VideoWriter(file_name, cv2.VideoWriter_fourcc(*"XVID"), 20, (640, 480))
            self.is_recording = True
            self.btn_record.config(text="Stop Recording", bg="red")
            print(f"Video recording started. Saving as {file_name}")
        else:
            self.is_recording = False
            self.video_writer.release()
            self.btn_record.config(text="Record Video", bg="SystemButtonFace")
            print("Video recording stopped.")

    def open_gallery(self):
        self.gallery_app = GalleryApp(self)
        self.withdraw()  
        self.gallery_app.protocol("WM_DELETE_WINDOW", self.on_gallery_close)
        self.gallery_app.mainloop()

    def on_gallery_close(self):
        self.gallery_app.destroy()  
        self.deiconify()  
        self.update_video_stream()

    def quit_app(self):
        if self.is_recording:
            self.video_writer.release()
        self.camera.release()
        self.destroy()

    def file_list(self):
        return [file for file in os.listdir(".") if
                file.startswith("captured_image") or file.startswith("recorded_video")]

class GalleryApp(tk.Toplevel):
    def __init__(self, camera_app):
        super().__init__(camera_app)
        self.title("Gallery")
        self.geometry("800x600")
        self.camera_app = camera_app
        self.file_list = self.camera_app.file_list()
        self.gallery_frame = tk.Frame(self)
        self.gallery_frame.pack(fill=tk.BOTH, expand=True)
        self.gallery_title = tk.Label(self.gallery_frame, text="Gallery", font=("Helvetica", 24, "bold"))
        self.gallery_title.pack(pady=20)
        self.back_button = tk.Button(self.gallery_frame, text="Back to Camera", command=self.back_to_camera)
        self.back_button.pack(pady=10)
        self.preview_canvas = tk.Canvas(self.gallery_frame, bg="white")
        self.preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar = ttk.Scrollbar(self.gallery_frame, orient=tk.VERTICAL, command=self.preview_canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.preview_canvas.bind("<Configure>", lambda event: self.preview_canvas.configure(
            scrollregion=self.preview_canvas.bbox("all")))
        self.preview_frame = tk.Frame(self.preview_canvas, bg="white")
        self.preview_canvas.create_window((0, 0), window=self.preview_frame, anchor=tk.NW)
        self.show_previews()

    def show_previews(self):
        if not self.file_list:
            label = tk.Label(self.preview_frame, text="No items found.", font=("Helvetica", 16))
            label.pack()
            return
        for i, file in enumerate(self.file_list):
            if file.startswith("captured_image"):
                img = Image.open(file)
                img.thumbnail((200, 150))
                img_tk = ImageTk.PhotoImage(image=img)
                label = tk.Label(self.preview_frame, image=img_tk, text=file, compound=tk.TOP, wraplength=180,
                                 font=("Helvetica", 12), bg="white")
                label.image = img_tk
                label.grid(row=i // 3, column=i % 3, padx=5, pady=5)
                label.bind("<Button-1>", lambda event, file=file: self.open_file(file))
            elif file.startswith("recorded_video"):
                cap = cv2.VideoCapture(file)
                ret, frame = cap.read()
                cap.release()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                    img.thumbnail((200, 150))
                    img_tk = ImageTk.PhotoImage(image=img)
                    label = tk.Label(self.preview_frame, image=img_tk, text=file, compound=tk.TOP, wraplength=180,
                                     font=("Helvetica", 12), bg="white")
                    label.image = img_tk
                    label.grid(row=i // 3, column=i % 3, padx=5, pady=5)
                    label.bind("<Button-1>", lambda event, file=file: self.open_file(file))

    def open_file(self, file_name):
        try:
            if sys.platform.startswith("darwin"):  
                subprocess.run(["open", file_name])
            elif os.name == "nt": 
                os.startfile(file_name)
            elif os.name == "posix": 
                subprocess.run(["xdg-open", file_name])
        except Exception as e:
            print(f"Failed to open file: {file_name}. Error: {e}")

    def back_to_camera(self):
        self.destroy()  
        self.camera_app.deiconify() 

if __name__ == "__main__":
    app = CameraApp()
    app.mainloop()
