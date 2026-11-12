# scripts/flasher.py
import subprocess
import sys
import os
import shutil
from pathlib import Path

def get_jlink_executable():
    """Находит исполняемый файл J-Link (кроссплатформенно)"""
    exec_name = "JLinkExe" if sys.platform != "win32" else "JLink.exe"
    exec_path = shutil.which(exec_name)
    
    if not exec_path and sys.platform == "win32":
        # Fallback для Windows, если J-Link не в PATH, но установлен по умолчанию
        possible_paths = [
            r"C:\Program Files\SEGGER\JLink\JLink.exe",
            r"C:\Program Files (x86)\SEGGER\JLink\JLink.exe"
        ]
        for p in possible_paths:
            if os.path.exists(p):
                return p
                
    if not exec_path:
        raise RuntimeError(f"❌ J-Link executable ({exec_name}) not found. Please install J-Link Software or add it to system PATH.")
    return exec_path

def flash_jlink(fw_image: str, device: str = "STM32F407VG", speed: int = 4000):
    """Прошивает устройство через J-Link"""
    print(f"🔄 Flashing {fw_image} via J-Link (Device: {device})...")
    
    jlink_exe = get_jlink_executable()
    # J-Link предпочитает прямые слеши даже на Windows
    abs_fw_image = Path(fw_image).resolve().as_posix() 
    
    # Команды: Halt, Load, Reset, Go, Quit (аналог твоих задач из VS Code)
    jlink_commands = f"h\nloadfile {abs_fw_image}\nr\ng\nq\n"
    
    cmd = [
        jlink_exe,
        "-device", device,
        "-if", "SWD",
        "-speed", str(speed),
        "-NoGui", "1"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            input=jlink_commands,
            capture_output=True,
            text=True,
            check=False
        )
    except FileNotFoundError:
        raise RuntimeError(f"❌ Не удалось запустить {jlink_exe}. Проверьте установку.")
    
    if result.returncode != 0:
        print("❌ J-Link Error Output:")
        print(result.stderr)
        if result.stdout:
            print("📄 J-Link Standard Output:")
            print(result.stdout)
        
        if __name__ == "__main__":
            sys.exit(1)
        else:
            raise RuntimeError(f"Failed to flash device via J-Link. Exit code: {result.returncode}")
    
    print("✅ Flashing successful!")

def erase_jlink(device: str = "STM32F407VG", speed: int = 4000):
    """Стирает флеш-память устройства через J-Link"""
    print(f"🔄 Erasing device via J-Link (Device: {device})...")
    
    jlink_exe = get_jlink_executable()
    jlink_commands = f"h\nerase\nr\nq\n"
    
    cmd = [
        jlink_exe,
        "-device", device,
        "-if", "SWD",
        "-speed", str(speed),
        "-NoGui", "1"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            input=jlink_commands,
            capture_output=True,
            text=True,
            check=False
        )
    except FileNotFoundError:
        raise RuntimeError(f"❌ Не удалось запустить {jlink_exe}.")
    
    if result.returncode != 0:
        print("❌ J-Link Erase Error:")
        print(result.stderr)
        if __name__ == "__main__":
            sys.exit(1)
        else:
            raise RuntimeError(f"Failed to erase device. Exit code: {result.returncode}")
            
    print("✅ Erase successful!")

# ===== CLI Интерфейс (запуск напрямую из терминала) =====
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Flash:  python scripts/flasher.py flash <path_to_bin_or_elf> [device] [speed]")
        print("  Erase:  python scripts/flasher.py erase [device] [speed]")
        print("Example: python scripts/flasher.py flash build/stm32f4-debug/wicked_boot.elf STM32F407VG 4000")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    if action == "flash":
        if len(sys.argv) < 3:
            print("❌ Error: Missing file path for 'flash' action.")
            sys.exit(1)
        fw_file = sys.argv[2]
        dev = sys.argv[3] if len(sys.argv) > 3 else "STM32F407VG"
        spd = int(sys.argv[4]) if len(sys.argv) > 4 else 4000
        
        if not os.path.exists(fw_file):
            print(f"❌ File not found: {fw_file}")
            sys.exit(1)
            
        try:
            flash_jlink(fw_file, device=dev, speed=spd)
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            sys.exit(1)
            
    elif action == "erase":
        dev = sys.argv[2] if len(sys.argv) > 2 else "STM32F407VG"
        spd = int(sys.argv[3]) if len(sys.argv) > 3 else 4000
        try:
            erase_jlink(device=dev, speed=spd)
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            sys.exit(1)
    else:
        print(f"❌ Unknown action: {action}. Use 'flash' or 'erase'.")
        sys.exit(1)