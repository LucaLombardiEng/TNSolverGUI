import tkinter as tk

def create_metric_scale(canvas, x, y, width, height_low, height_high, num_rectangles, tick_length=10):
    """
    Crea una scala metrica con rettangoli alternati e tacche.

    Args:
        canvas: Il canvas Tkinter su cui disegnare.
        x: La coordinata x iniziale della scala.
        y: La coordinata y della base della scala.
        width: La larghezza totale della scala.
        height_low: L'altezza dei rettangoli bassi.
        height_high: L'altezza dei rettangoli alti.
        num_rectangles: Il numero di rettangoli nella scala.
        tick_length: La lunghezza delle tacche.
    """
    rectangle_width = width / num_rectangles
    current_x = x
    current_height = height_low

    for i in range(num_rectangles):
        # Disegna il rettangolo
        canvas.create_rectangle(current_x, y - current_height, current_x + rectangle_width, y, fill="lightblue", outline="black")

        # Disegna le tacche principali (ogni due rettangoli)
        if i % 2 == 0:
            canvas.create_line(current_x, y, current_x, y + tick_length, fill="black")
            canvas.create_line(current_x + rectangle_width, y, current_x + rectangle_width, y + tick_length, fill="black")

        # Disegna le tacche secondarie (a metà di ogni rettangolo)
        half_x = current_x + rectangle_width / 2
        canvas.create_line(half_x, y, half_x, y + tick_length / 2, fill="black")

        current_x += rectangle_width
        current_height = height_high if current_height == height_low else height_low

def main():
    """
    Funzione principale per creare e visualizzare la scala metrica.
    """
    window = tk.Tk()
    window.title("Scala Metrica")

    canvas_width = 600  # Increased width for better visualization
    canvas_height = 200
    canvas = tk.Canvas(window, width=canvas_width, height=canvas_height, bg="white")
    canvas.pack()

    # Parametri della scala
    x_start = 50
    y_base = canvas_height - 20
    total_width = 500  # Increased width
    low_height = 40
    high_height = 80
    num_rects = 10  # Increased number of rectangles
    tick_len = 10

    create_metric_scale(canvas, x_start, y_base, total_width, low_height, high_height, num_rects, tick_len)

    window.mainloop()

if __name__ == "__main__":
    main()
