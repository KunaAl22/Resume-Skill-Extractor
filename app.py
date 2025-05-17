import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from pdf_extractor import PDFExtractor
import os

class PDFTextExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Resume Information Extractor")
        self.root.geometry("1200x800")
        
        # Initialize PDF extractor
        self.pdf_extractor = PDFExtractor()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure styles
        style = ttk.Style()
        style.configure('Upload.TButton', foreground='gray')
        
        # Create and place widgets
        self.create_widgets()

    def create_widgets(self):
        # Create notebook for different sections
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create frames for each section
        self.info_frame = ttk.Frame(self.notebook)
        self.skills_frame = ttk.Frame(self.notebook)
        self.exp_frame = ttk.Frame(self.notebook)
        self.text_frame = ttk.Frame(self.notebook)
        
        # Configure frame weights for proper resizing
        self.skills_frame.grid_columnconfigure(0, weight=1)
        self.skills_frame.grid_rowconfigure(0, weight=1)
        
        # Add frames to notebook
        self.notebook.add(self.info_frame, text="Personal Info")
        self.notebook.add(self.skills_frame, text="Skills")
        self.notebook.add(self.exp_frame, text="Experience")
        self.notebook.add(self.text_frame, text="Raw Text")
        
        # Personal info frame
        ttk.Label(self.info_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.name_label = ttk.Label(self.info_frame, text="")
        self.name_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(self.info_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.email_label = ttk.Label(self.info_frame, text="")
        self.email_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(self.info_frame, text="Phone:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.phone_label = ttk.Label(self.info_frame, text="")
        self.phone_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Skills text widget
        self.skills_text = tk.Text(self.skills_frame, height=15, width=60, wrap=tk.WORD)
        self.skills_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Skills scrollbar
        self.skills_scrollbar = ttk.Scrollbar(
            self.skills_frame,
            orient=tk.VERTICAL,
            command=self.skills_text.yview
        )
        self.skills_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure text widget and scrollbar
        self.skills_text.configure(yscrollcommand=self.skills_scrollbar.set)
        self.skills_scrollbar.configure(command=self.skills_text.yview)

        # Summary frame
        self.summary_frame = ttk.LabelFrame(self.main_frame, text="Resume Summary", padding=(5, 5))
        self.summary_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        
        # Summary text widget
        self.summary_text = tk.Text(self.summary_frame, height=10, width=60, wrap=tk.WORD)
        self.summary_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Summary scrollbar
        self.summary_scrollbar = ttk.Scrollbar(
            self.summary_frame,
            orient=tk.VERTICAL,
            command=self.summary_text.yview
        )
        self.summary_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configure summary text widget and scrollbar
        self.summary_text.configure(yscrollcommand=self.summary_scrollbar.set)
        self.summary_scrollbar.configure(command=self.summary_text.yview)
        
        # Experience frame
        self.exp_text = tk.Text(self.exp_frame, width=60, height=15)
        self.exp_text.grid(row=0, column=0, padx=5, pady=5)
        
        self.exp_scrollbar = ttk.Scrollbar(
            self.exp_frame,
            orient=tk.VERTICAL,
            command=self.exp_text.yview
        )
        self.exp_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.exp_text.configure(yscrollcommand=self.exp_scrollbar.set)
        
        # Raw text frame
        self.text_area = tk.Text(self.text_frame, width=80, height=20)
        self.text_area.grid(row=0, column=0, padx=5, pady=5)
        
        self.text_scrollbar = ttk.Scrollbar(
            self.text_frame,
            orient=tk.VERTICAL,
            command=self.text_area.yview
        )
        self.text_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.text_area.configure(yscrollcommand=self.text_scrollbar.set)
        
        # Upload button
        self.upload_button = ttk.Button(
            self.main_frame,
            text="Upload PDF",
            style='Upload.TButton',
            command=self.upload_pdf
        )
        self.upload_button.grid(row=1, column=0, padx=5, pady=5)
        
        # Status label
        self.status_label = ttk.Label(self.main_frame, text="")
        self.status_label.grid(row=2, column=0, padx=5, pady=5)

    def upload_pdf(self):
        # Open file dialog to select PDF
        file_path = filedialog.askopenfilename(
            title="Select PDF",
            filetypes=[("PDF files", "*.pdf")]
        )
        
        if file_path:
            try:
                # Clear all previous data first
                self.clear_all()
                
                # Update PDF path
                self.pdf_extractor.pdf_path = file_path
                
                # Extract and display all information
                self.extract_text()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to process PDF: {str(e)}")
                self.status_label.config(
                    text="Error processing PDF",
                    foreground="red"
                )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to process PDF: {str(e)}")
                self.status_label.config(
                    text="Error processing PDF",
                    foreground="red"
                )

    def clear_all(self):
        # Clear personal info
        self.name_label.config(text="")
        self.email_label.config(text="")
        self.phone_label.config(text="")
        
        # Clear text areas
        for widget in [self.skills_text, self.exp_text, self.text_area, self.summary_text]:
            widget.configure(state='normal')  # Enable editing first
            widget.delete(1.0, tk.END)
            widget.configure(state='disabled')  # Disable editing
        
        # Clear status
        self.status_label.config(text="", foreground="black")
        
        # Reset PDF extractor
        self.pdf_extractor = PDFExtractor()

    def extract_text(self):
        try:
            # Extract text from PDF
            text = self.pdf_extractor.extract_text(self.pdf_extractor.pdf_path)
            
            # Update status
            self.status_label.config(
                text=f"Processing: {os.path.basename(self.pdf_extractor.pdf_path)}",
                foreground="green"
            )
            
            # Extract and display personal info
            name = self.pdf_extractor.extract_name(text)
            email = self.pdf_extractor.extract_email(text)
            phone = self.pdf_extractor.extract_phone(text)
            
            self.name_label.config(text=name)
            self.email_label.config(text=email)
            self.phone_label.config(text=phone)
            
            # Extract and display skills
            try:
                skills = self.pdf_extractor.extract_skills(text)
                if skills:
                    self.skills_text.configure(state='normal')
                    self.skills_text.delete(1.0, tk.END)
                    for skill_dict in skills:
                        category = skill_dict.get("category", "Unknown")
                        tech_stack = skill_dict.get("tech_stack", [])
                        if tech_stack:
                            self.skills_text.insert(tk.END, f"\n{category}:\n")
                            for skill in tech_stack:
                                self.skills_text.insert(tk.END, f"- {skill}\n")
                    self.skills_text.configure(state='disabled')
                else:
                    self.skills_text.configure(state='normal')
                    self.skills_text.delete(1.0, tk.END)
                    self.skills_text.insert(tk.END, "No skills found\n")
                    self.skills_text.configure(state='disabled')
            except Exception as e:
                print(f"Error extracting skills: {str(e)}")
                self.skills_text.configure(state='normal')
                self.skills_text.delete(1.0, tk.END)
                self.skills_text.insert(tk.END, "Error displaying skills\n")
                self.skills_text.configure(state='disabled')
            
            # Extract and display experience
            try:
                experience = self.pdf_extractor.extract_experience(text)
                if experience:
                    self.exp_text.configure(state='normal')
                    self.exp_text.delete(1.0, tk.END)
                    for exp in experience:
                        exp_text = f"""Position: {exp.get('position', 'Position not specified')}
                            Company: {exp.get('company', 'Company not specified')}
                            Duration: {exp.get('duration', 'Duration not specified')}
                            Location: {exp.get('location', 'Location not specified')}

                            """
                        self.exp_text.insert(tk.END, exp_text)
                    self.exp_text.configure(state='disabled')
                else:
                    self.exp_text.configure(state='normal')
                    self.exp_text.delete(1.0, tk.END)
                    self.exp_text.insert(tk.END, "No experience information found\n")
                    self.exp_text.configure(state='disabled')
            except Exception as e:
                print(f"Error extracting experience: {str(e)}")
                self.exp_text.configure(state='normal')
                self.exp_text.delete(1.0, tk.END)
                self.exp_text.insert(tk.END, "Error displaying experience\n")
                self.exp_text.configure(state='disabled')
            
            # Display raw text
            self.text_area.configure(state='normal')
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, text)
            self.text_area.configure(state='disabled')
            
            # Generate and display summary
            try:
                summary = self.pdf_extractor.generate_resume_summary(name, skills, experience)
                self.summary_text.configure(state='normal')
                self.summary_text.delete(1.0, tk.END)
                self.summary_text.insert(tk.END, summary)
                self.summary_text.configure(state='disabled')
            except Exception as e:
                print(f"Error generating summary: {str(e)}")
                self.summary_text.configure(state='normal')
                self.summary_text.delete(1.0, tk.END)
                self.summary_text.insert(tk.END, "Error generating summary\n")
                self.summary_text.configure(state='disabled')
            
            # Update final status
            
            # Save to file
            output_file = self.pdf_extractor.pdf_path.rsplit('.', 1)[0] + '_extracted.txt'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            self.status_label.config(
                text=f"Text extracted and saved to: {os.path.basename(output_file)}",
                foreground="green"
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract text: {str(e)}")
            self.status_label.config(
                text="Error extracting text",
                foreground="red"
            )

def main():
    root = tk.Tk()
    app = PDFTextExtractorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
