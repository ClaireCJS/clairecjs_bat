import colorsys

def generate_ansi_bg_color_cycle():
    rgb_values = [tuple(round(j * 255) for j in colorsys.hsv_to_rgb(i / 256.0, 1.0, 1.0)) for i in range(256)]
    ansi_codes = []
    for i in range(len(rgb_values)):
        r, g, b = rgb_values[i]
        ansi_codes.append(f'\x1b]11;rgb:{r:x}/{g:x}/{b:x}\x1b\\')
    return ansi_codes

if __name__ == "__main__":
    ansi_codes = generate_ansi_bg_color_cycle()
    with open("color_cycle_output.txt", "w") as file:
        for ansi_code in ansi_codes:
            file.write(ansi_code + '\n')
