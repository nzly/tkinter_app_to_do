import smtplib
import threading
import tkinter as tk
from email.message import EmailMessage
from tkinter import ttk


class EmailApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Email Sender")
        self.geometry("480x520")

        # Form Container
        container = ttk.Frame(self, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        # Sender Credentials
        ttk.Label(container, text="Your Email:").grid(row=0, column=0, sticky="w", pady=4)
        self.sender_entry = ttk.Entry(container, width=40)
        self.sender_entry.grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(container, text="App Password:").grid(row=1, column=0, sticky="w", pady=4)
        self.password_entry = ttk.Entry(container, width=40, show="*")
        self.password_entry.grid(row=1, column=1, sticky="ew", pady=4)

        # Recipient & Subject
        ttk.Label(container, text="To Email:").grid(row=2, column=0, sticky="w", pady=4)
        self.receiver_entry = ttk.Entry(container, width=40)
        self.receiver_entry.grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(container, text="Subject:").grid(row=3, column=0, sticky="w", pady=4)
        self.subject_entry = ttk.Entry(container, width=40)
        self.subject_entry.grid(row=3, column=1, sticky="ew", pady=4)

        # Email Body
        ttk.Label(container, text="Message:").grid(row=4, column=0, sticky="nw", pady=4)
        self.body_text = tk.Text(container, height=10, width=40)
        self.body_text.grid(row=4, column=1, sticky="ew", pady=4)

        # Send Button & Status Label
        self.send_btn = ttk.Button(container, text="Send Email", command=self.start_send_thread)
        self.send_btn.grid(row=5, column=1, sticky="e", pady=12)

        self.status_label = ttk.Label(container, text="", foreground="blue")
        self.status_label.grid(row=6, column=0, columnspan=2, sticky="w")

        container.columnconfigure(1, weight=1)

    def start_send_thread(self):
        """Collects field values on the main thread and spawns a background worker thread."""
        sender = self.sender_entry.get().strip()
        password = self.password_entry.get().strip()
        receiver = self.receiver_entry.get().strip()
        subject = self.subject_entry.get().strip()
        body = self.body_text.get("1.0", tk.END).strip()

        if not all([sender, password, receiver, subject, body]):
            self._apply_status("Please fill in all fields.", "red")
            return

        self.send_btn.config(state="disabled")
        self.status_label.config(text="Sending email...", foreground="blue")

        # Pass data into daemon thread so app can exit cleanly if closed during network operation
        thread = threading.Thread(
            target=self.send_email,
            args=(sender, password, receiver, subject, body),
            daemon=True,
        )
        thread.start()

    def send_email(self, sender, password, receiver, subject, body):
        """Runs on a background thread to prevent UI freezing."""
        try:
            # Build email message using modern EmailMessage API
            msg = EmailMessage()
            msg["From"] = sender
            msg["To"] = receiver
            msg["Subject"] = subject
            msg.set_content(body)

            # Connect to SMTP server using context manager for proper cleanup
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender, password)
                server.send_message(msg)

            self.update_status("Email sent successfully!", "green")
        except Exception as err:
            self.update_status(f"Error: {str(err)}", "red")

    def update_status(self, message, color):
        """Thread-safe UI status update via after()."""
        self.after(0, lambda: self._apply_status(message, color))

    def _apply_status(self, message, color):
        self.status_label.config(text=message, foreground=color)
        self.send_btn.config(state="normal")


if __name__ == "__main__":
    app = EmailApp()
    app.mainloop()