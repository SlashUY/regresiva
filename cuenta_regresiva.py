#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import io
import re
import time
import signal
import threading
import subprocess
import argparse
import ctypes
import tkinter as tk
import winsound

# ── UTF-8 y ANSI en consola Windows ──────────────────────────────────────────
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.system('chcp 65001 >nul 2>&1')

def enable_ansi():
    try:
        k = ctypes.windll.kernel32
        k.SetConsoleMode(k.GetStdHandle(-11), 7)
    except Exception:
        pass

_CLS = '\033[2J\033[H'   # limpiar pantalla sin subprocess

# ── Colores ANSI ──────────────────────────────────────────────────────────────
G    = '\033[92m'
DG   = '\033[32m'
Y    = '\033[93m'
R    = '\033[91m'
BOLD = '\033[1m'
RESET= '\033[0m'

# ── Regex pre-compilada ───────────────────────────────────────────────────────
_RE_ANSI = re.compile(r'\033\[[0-9;]*m')

def strip_ansi(s):
    return _RE_ANSI.sub('', s)

# ── Dígitos ASCII retro (bloques) ─────────────────────────────────────────────
DIGITS = {
    '0': [' ██████ ','██    ██','██    ██','██    ██',' ██████ '],
    '1': ['   ██   ','  ███   ','   ██   ','   ██   ',' ██████ '],
    '2': [' ██████ ','     ██ ',' ██████ ','██      ','████████'],
    '3': [' ██████ ','     ██ ','  █████ ','     ██ ',' ██████ '],
    '4': ['██    ██','██    ██','████████','     ██ ','     ██ '],
    '5': ['████████','██      ','███████ ','     ██ ','███████ '],
    '6': [' ██████ ','██      ','███████ ','██    ██',' ██████ '],
    '7': ['████████','     ██ ','    ██  ','   ██   ','   ██   '],
    '8': [' ██████ ','██    ██',' ██████ ','██    ██',' ██████ '],
    '9': [' ██████ ','██    ██',' ███████','     ██ ',' ██████ '],
    ':': ['        ','  ████  ','        ','  ████  ','        '],
    ' ': ['        ','        ','        ','        ','        '],
}

ANCHO = 68

def centrar(texto, ancho=ANCHO):
    pad = max(0, (ancho - len(strip_ansi(texto))) // 2)
    return ' ' * pad + texto

def render_big_time(time_str, color):
    lineas = [''] * 5
    for char in time_str:
        digit = DIGITS.get(char, DIGITS[' '])
        for i, fila in enumerate(digit):
            lineas[i] += fila + ' '
    return '\n'.join(centrar(color + BOLD + l + RESET) for l in lineas) + '\n'

def barra_progreso(restante, total, ancho=52, color=G):
    fraccion = restante / total if total > 0 else 0
    lleno = int(ancho * fraccion)
    return f"{color}[{'█'*lleno}{'░'*(ancho-lleno)}] {int(fraccion*100):3d}%{RESET}"

def segundos_a_display(seg):
    h, rem = divmod(seg, 3600)
    m, s   = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

# ── Parsear tiempo ────────────────────────────────────────────────────────────
_RE_HMS  = re.compile(r'^(\d+):(\d+):(\d+)$')
_RE_MS   = re.compile(r'^(\d+):(\d+)$')
_RE_COMB = re.compile(r'^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$')

def parsear_tiempo(texto):
    m = _RE_HMS.match(texto)
    if m:
        return int(m[1])*3600 + int(m[2])*60 + int(m[3])
    m = _RE_MS.match(texto)
    if m:
        return int(m[1])*60 + int(m[2])
    m = _RE_COMB.match(texto)
    if m and any(m.groups()):
        return int(m[1] or 0)*3600 + int(m[2] or 0)*60 + int(m[3] or 0)
    m = re.match(r'^(\d+)$', texto)
    return int(m[1]) if m else None

# ── Pantalla de instrucciones ─────────────────────────────────────────────────
def mostrar_instrucciones():
    print(_CLS, end='', flush=True)
    B = G + BOLD

    def linea(texto=''):
        pad = ANCHO - 2 - len(strip_ansi(texto))
        print(f"{B}║{RESET}{texto}{' '*pad}{B}║{RESET}")

    print(f"{B}╔{'═'*(ANCHO-2)}╗{RESET}")
    linea(f"{B}        ⚡  CUENTA REGRESIVA RETRO  ⚡{RESET}")
    linea(f"{DG}              Para Windows 10 — Consola{RESET}")
    print(f"{B}╠{'═'*(ANCHO-2)}╣{RESET}")
    linea()
    linea(f"{G}  USO:  {RESET}cuenta_regresiva [TIEMPO] [opciones]")
    linea()
    linea(f"{G}  FORMATOS DE TIEMPO:{RESET}")
    for fmt, desc in [('30','30 segundos'),('5m','5 minutos'),('1h30m','1 hora y 30 minutos'),
                      ('1h30m20s','1 hora, 30 min y 20 seg'),('01:30:00','formato HH:MM:SS'),
                      ('01:30','formato MM:SS')]:
        linea(f"{DG}    {fmt:<15}{RESET}→  {desc}")
    linea()
    linea(f"{G}  OPCIONES:{RESET}")
    for opt, desc in [('--mensaje "texto"','Mensaje personalizado al terminar'),
                      ('--accion alerta  ','Ventana emergente (por defecto)'),
                      ('--accion bloquear','Bloquea el equipo'),
                      ('--accion apagar  ','Apaga el equipo (30 seg)'),
                      ('--accion reiniciar','Reinicia el equipo (30 seg)')]:
        linea(f"{DG}    {opt}  {RESET}→  {desc}")
    linea()
    linea(f"{G}  EJEMPLOS:{RESET}")
    linea(f"{DG}    cuenta_regresiva 5m{RESET}")
    linea(f"{DG}    cuenta_regresiva 1h --mensaje \"Reunión\"{RESET}")
    linea(f"{DG}    cuenta_regresiva 01:30:00 --accion bloquear{RESET}")
    linea()
    linea(f"{Y}  Presiona Ctrl+C para cancelar la cuenta en cualquier momento.{RESET}")
    linea()
    print(f"{B}╚{'═'*(ANCHO-2)}╝{RESET}\n")

# ── Widget 7-segmentos ────────────────────────────────────────────────────────
#   Segmentos:  aaa / f b / ggg / e c / ddd
PATRON_SEG = {
    '0': set('abcdef'), '1': set('bc'),     '2': set('abdeg'),
    '3': set('abcdg'),  '4': set('bcfg'),   '5': set('acdfg'),
    '6': set('acdefg'), '7': set('abc'),    '8': set('abcdefg'),
    '9': set('abcdfg'),
}

DW, DH, ST, SG, DSP, CW, PAD = 36, 62, 5, 3, 6, 16, 14
C_ON  = '#00FF41'
C_OFF = '#0B2B10'
C_BG  = '#000000'
C_LBL = '#00CC33'

# Coordenadas de segmentos pre-computadas relativas a (0, 0)
_hw = DH // 2
_SEG_REL = {
    'a': (SG,    0,         DW-SG,  ST),
    'b': (DW-ST, SG,        DW,     _hw-SG),
    'c': (DW-ST, _hw+SG,    DW,     DH-SG),
    'd': (SG,    DH-ST,     DW-SG,  DH),
    'e': (0,     _hw+SG,    ST,     DH-SG),
    'f': (0,     SG,        ST,     _hw-SG),
    'g': (SG,    _hw-ST//2, DW-SG,  _hw+ST//2+1),
}

def dibujar_digito(canvas, ox, oy, char, c_on=C_ON):
    if char == ':':
        r, cx = ST-1, ox + CW//2
        for cy in (oy + DH//3, oy + 2*DH//3):
            canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=c_on, outline='')
        return CW
    activos = PATRON_SEG.get(char, set())
    for seg, (x1, y1, x2, y2) in _SEG_REL.items():
        canvas.create_rectangle(ox+x1, oy+y1, ox+x2, oy+y2,
                                fill=(c_on if seg in activos else C_OFF),
                                outline='')
    return DW

def calcular_ancho_canvas(time_str):
    return sum((CW if c == ':' else DW) + DSP for c in time_str) - DSP + 2*PAD

def crear_widget(tiempo_ref, total_seg, widget_stop, mensaje):
    root = tk.Tk()
    root.overrideredirect(True)
    root.configure(bg=C_BG)

    canvas_w = calcular_ancho_canvas(segundos_a_display(total_seg))
    canvas_h = DH + 2*PAD
    sw       = root.winfo_screenwidth()
    total_h  = canvas_h + (20 if mensaje else 0)
    root.geometry(f'{canvas_w}x{total_h}+{sw - canvas_w - 20}+20')

    canvas = tk.Canvas(root, width=canvas_w, height=canvas_h,
                       bg=C_BG, highlightthickness=1, highlightbackground=C_ON)
    canvas.pack()

    if mensaje:
        tk.Label(root, text=mensaje, font=('Courier New', 8),
                 fg=C_LBL, bg=C_BG).pack(pady=(0, 4))

    ultimo = [-1]

    def update_loop():
        if widget_stop.is_set():
            root.quit()
            return
        t = tiempo_ref[0]
        if t != ultimo[0]:
            ultimo[0] = t
            canvas.delete('all')
            frac  = t / total_seg if total_seg > 0 else 0
            c_seg = C_ON if frac > 0.5 else ('#FFD700' if frac > 0.2 else '#FF3A20')
            x = PAD
            for ch in segundos_a_display(t):
                x += dibujar_digito(canvas, x, PAD, ch, c_on=c_seg) + DSP
        root.after(200, update_loop)

    root.after(0, update_loop)
    root.mainloop()
    try:
        root.destroy()
    except Exception:
        pass

# ── Ventana de alerta ─────────────────────────────────────────────────────────
def ventana_alerta(mensaje):
    def pitidos(stop_evt):
        winmm = ctypes.windll.winmm
        vol   = ctypes.c_uint32()
        winmm.waveOutGetVolume(0, ctypes.byref(vol))
        n60 = int(0xFFFF * 0.6)
        winmm.waveOutSetVolume(0, n60 | (n60 << 16))
        freqs, idx = [880, 660, 990, 550], 0
        try:
            while not stop_evt.is_set():
                winsound.Beep(freqs[idx % 4], 180)
                time.sleep(0.25)
                idx += 1
        finally:
            winmm.waveOutSetVolume(0, vol.value)

    root = tk.Tk()
    root.configure(bg='black')
    root.resizable(False, False)
    w, h = 800, 520
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f'{w}x{h}+{(sw-w)//2}+{(sh-h)//2}')
    root.attributes('-topmost', True)
    root.overrideredirect(True)

    stop_beep = threading.Event()
    threading.Thread(target=pitidos, args=(stop_beep,), daemon=True).start()

    frame = tk.Frame(root, bg='black')
    frame.place(relx=0.5, rely=0.5, anchor='center')

    titulo = tk.Label(frame, text='⚡  ¡TIEMPO TERMINADO!  ⚡',
                      font=('Courier New', 36, 'bold'), fg='#00FF41', bg='black')
    titulo.pack(pady=20)

    if mensaje:
        tk.Label(frame, text=mensaje, font=('Courier New', 22),
                 fg='#00FF41', bg='black').pack(pady=10)

    tk.Label(frame, text='[ PRESIONA CUALQUIER TECLA O CLIC PARA CERRAR ]',
             font=('Courier New', 13), fg='#007A1F', bg='black').pack(pady=40)

    def parpadeo():
        titulo.config(fg='#007A1F' if titulo.cget('fg') == '#00FF41' else '#00FF41')
        root.after(450, parpadeo)

    def cerrar(event=None):
        stop_beep.set()
        root.destroy()
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
        os._exit(0)

    root.bind('<Any-KeyPress>', cerrar)
    root.bind('<Button-1>', cerrar)
    root.focus_set()
    parpadeo()
    root.mainloop()

# ── Countdown (hilo de fondo) ─────────────────────────────────────────────────
def correr_cuenta(total_seg, mensaje, accion, tiempo_ref, widget_stop, cancelado):
    while tiempo_ref[0] >= 0 and not cancelado.is_set():
        restante  = tiempo_ref[0]
        disp      = segundos_a_display(restante)
        color     = G if restante > total_seg*.5 else (Y if restante > total_seg*.2 else R)

        print(_CLS, end='', flush=True)
        print(f"{color}{BOLD}╔{'═'*(ANCHO-2)}╗{RESET}")
        print(f"{color}{BOLD}║{'  ⚡ CUENTA REGRESIVA RETRO ⚡'.center(ANCHO-2)}║{RESET}")
        print(f"{color}{BOLD}╚{'═'*(ANCHO-2)}╝{RESET}\n")
        print(render_big_time(disp, color), end='')
        print(f"\n  {barra_progreso(restante, total_seg, ancho=54, color=color)}\n")
        if mensaje:
            print(centrar(f"{G}  {mensaje}{RESET}") + '\n')
        print(f"{DG}  Transcurrido: {segundos_a_display(total_seg-restante)}"
              f"  |  Acción: {accion}  |  Ctrl+C cancela{RESET}")
        print(f"{color}{BOLD}{'═'*ANCHO}{RESET}")

        if restante == 0:
            break
        time.sleep(1)
        tiempo_ref[0] -= 1

    widget_stop.set()

# ── Acción final ──────────────────────────────────────────────────────────────
def ejecutar_accion(accion, mensaje):
    print(_CLS, end='', flush=True)
    if accion == 'alerta':
        ventana_alerta(mensaje)
    elif accion == 'bloquear':
        winsound.Beep(880, 800)
        ctypes.windll.user32.LockWorkStation()
    else:
        cmd  = '/s' if accion == 'apagar' else '/r'
        aviso = f'Cuenta regresiva terminada. {mensaje}'.strip()
        subprocess.run(['shutdown', cmd, '/t', '30', '/c', aviso])
        col  = R if accion == 'apagar' else Y
        verbo = 'Apagando' if accion == 'apagar' else 'Reiniciando'
        print(f"\n{col}  {verbo} en 30 segundos.  Ejecuta 'shutdown /a' para cancelar.{RESET}\n")
        time.sleep(5)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    enable_ansi()
    ctypes.windll.kernel32.SetConsoleTitleW('⚡ Cuenta Regresiva Retro ⚡')

    if len(sys.argv) == 1:
        mostrar_instrucciones()
        print(f"{G}  Ingresa el tiempo (ej: 5m, 30, 1h30m, 00:30:00): {RESET}",
              end='', flush=True)
        try:
            entrada = input().strip()
        except KeyboardInterrupt:
            print(f"\n{Y}  Saliendo...{RESET}")
            sys.exit(0)
        if not entrada:
            sys.exit(0)
        sys.argv = [sys.argv[0]] + entrada.split()

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('tiempo',    nargs='?', default=None)
    parser.add_argument('--mensaje', '-m', default='')
    parser.add_argument('--accion',  '-a', default='alerta',
                        choices=['alerta', 'bloquear', 'apagar', 'reiniciar'])
    parser.add_argument('--ayuda',   '-h', action='store_true')
    args = parser.parse_args()

    if args.ayuda or not args.tiempo:
        mostrar_instrucciones()
        sys.exit(0)

    total = parsear_tiempo(args.tiempo)
    if not total or total <= 0:
        print(f"\n{R}  Error: formato inválido '{args.tiempo}'{RESET}")
        print(f"{G}  Ejemplos: 30  |  5m  |  1h30m  |  01:30:00{RESET}\n")
        sys.exit(1)

    tiempo_ref  = [total]
    widget_stop = threading.Event()
    cancelado   = threading.Event()

    def on_sigint(sig, frame):
        cancelado.set()
        widget_stop.set()
        print(f"\n{Y}  Cuenta regresiva cancelada.{RESET}\n")
        os._exit(0)

    signal.signal(signal.SIGINT, on_sigint)

    # Minimizar consola CMD al arrancar
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE

    threading.Thread(
        target=correr_cuenta,
        args=(total, args.mensaje, args.accion, tiempo_ref, widget_stop, cancelado),
        daemon=True
    ).start()

    crear_widget(tiempo_ref, total, widget_stop, args.mensaje)  # hilo principal

    if not cancelado.is_set():
        ejecutar_accion(args.accion, args.mensaje)


if __name__ == '__main__':
    main()
