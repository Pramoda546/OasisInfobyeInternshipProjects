import tkinter as tk
from tkinter import messagebox

# Function to calculate BMI
def calculate_bmi():
    try:
        weight = float(weight_entry.get())
        height_cm = float(height_entry.get())

        if weight <= 0 or height_cm <= 0:
            messagebox.showerror("Oops!", "Please enter positive numbers for your weight and height. 😊")
            return

        height = height_cm / 100  

        bmi = weight / (height ** 2)

        if bmi < 18.5:
            category = "You're a bit underweight. Let's aim for a healthier weight!"
        elif 18.5 <= bmi < 24.9:
            category = "Great! You have a normal, healthy weight. Keep it up!"
        elif 25 <= bmi < 29.9:
            category = "You're slightly overweight. A little lifestyle tweak could help!"
        else:
            category = "It looks like you're in the obese category. Let's consider consulting a health professional."

        result_label.config(text=f"Your BMI is: {bmi:.2f}\n{category}")
    except ValueError:
        messagebox.showerror("Oops!", "Hmm, that doesn't look like a number. Please enter numeric values only.")

# GUI Window
root = tk.Tk()
root.title("Friendly BMI Calculator")
root.geometry("450x330")
root.configure(bg="#e6f2ff")

# Title
title_label = tk.Label(root, text="Welcome to your BMI Calculator", font=("Arial", 18, "bold"), bg="#e6f2ff")
title_label.pack(pady=12)

# Weight input
weight_label = tk.Label(root, text="Could you please enter your weight in kilograms?", font=("Arial", 12), bg="#e6f2ff")
weight_label.pack()
weight_entry = tk.Entry(root, font=("Arial", 12))
weight_entry.pack(pady=6)

# Height input (in cm)
height_label = tk.Label(root, text="And your height in centimeters?", font=("Arial", 12), bg="#e6f2ff")
height_label.pack()
height_entry = tk.Entry(root, font=("Arial", 12))
height_entry.pack(pady=6)

# Calculate button
calc_button = tk.Button(root, text="Calculate My BMI, Please!", font=("Arial", 12, "bold"), bg="#1e90ff", fg="white", command=calculate_bmi)
calc_button.pack(pady=18)

# Result label
result_label = tk.Label(root, text="", font=("Arial", 14, "italic"), fg="#004080", bg="#e6f2ff", wraplength=400, justify="center")
result_label.pack(pady=14)

# Run the app
root.mainloop()
