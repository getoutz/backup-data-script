import os
import subprocess
from datetime import datetime, timedelta
import configparser
import time
import sys
import shutil
import colorama
from colorama import Fore, Style

# เริ่มต้น colorama
colorama.init(autoreset=True)

# ตรวจสอบว่ามีไฟล์ config.conf หรือไม่
config_file = 'config.conf'
if not os.path.exists(config_file):
    print(f"{Fore.RED}Error: Configuration file 'config.conf' not found. Exiting...{Style.RESET_ALL}")
    time.sleep(10)
    sys.exit(1)

# อ่านค่าจากไฟล์ config
config = configparser.ConfigParser()
config.read(config_file, encoding='utf-8')

# ตรวจสอบว่ามีข้อมูลในไฟล์ config หรือไม่
if not config.sections():
    print(f"{Fore.RED}Error: Configuration file 'config.conf' is empty or unreadable. Exiting...{Style.RESET_ALL}")
    time.sleep(10)
    sys.exit(1)

# กำหนดค่าต่างๆ จากไฟล์ config
DB_NAME = config['database']['DB_NAME']
DB_USER = config['database']['DB_USER']
DB_HOST = config['database']['DB_HOST']
DB_PORT = config['database']['DB_PORT']
BACKUP_DIR = config['database']['BACKUP_DIR']
DB_PASSWORD = config['database']['DB_PASSWORD']
PG_DUMP_PATH = config['database']['PG_DUMP_PATH']
BACKUP_INTERVAL = int(config['settings']['backup_interval'])
BACKUP_NAME_FORMAT = config['settings'].get('BACKUP_NAME_FORMAT', 'detailed')
BACKUP_MODE = config['settings'].get('BACKUP_MODE', 'single')

# กำหนดค่าตำแหน่ง NAS จากไฟล์ config
NAS_PATH = config['nas']['NAS_PATH']
ENABLE_NAS_COPY = config['nas'].getboolean('ENABLE_NAS_COPY', False)

# ตรวจสอบและสร้างโฟลเดอร์ backup หากยังไม่มี
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)
    print(f"{Fore.YELLOW}Backup directory created at: {BACKUP_DIR}{Style.RESET_ALL}")

def logtime():
    return datetime.now().strftime('%d-%m-%Y %H:%M:%S')

def backup_database():
    # ตั้งค่าเวลาและวันที่สำหรับชื่อไฟล์ backup
    now = datetime.now()
    
    # ตรวจสอบรูปแบบการตั้งชื่อไฟล์สำรอง
    if BACKUP_NAME_FORMAT == 'daily':
        backup_name = f"backup_{now.strftime('%Y_%m_%d')}.backup"
    else:
        backup_name = f"backup_{now.strftime('%Y_%m_%d_%H%M%S')}.backup"
    
    # ตรวจสอบรูปแบบการเก็บไฟล์
    if BACKUP_MODE == 'daily':
        # เก็บแยกตามวัน เช่น backups/2024_11_13/
        daily_backup_dir = os.path.join(BACKUP_DIR, now.strftime('%Y_%m_%d'))
        if not os.path.exists(daily_backup_dir):
            os.makedirs(daily_backup_dir)
        backup_path = os.path.join(daily_backup_dir, backup_name)
    else:
        # เก็บไฟล์ทั้งหมดในโฟลเดอร์เดียว
        backup_path = os.path.join(BACKUP_DIR, backup_name)

    # ตั้งค่ารหัสผ่านใน environment variable สำหรับ pg_dump
    os.environ["PGPASSWORD"] = DB_PASSWORD

    # คำสั่งสำรองข้อมูลในรูปแบบ custom archive format
    try:
        subprocess.run(
            [
                PG_DUMP_PATH,
                "-U", DB_USER,
                "-h", DB_HOST,
                "-p", DB_PORT,
                "-F", "c",
                "-f", backup_path,
                DB_NAME
            ],
            check=True
        )
        print(f"{Fore.GREEN}{logtime()} >> Backup completed successfully at: {backup_path}{Style.RESET_ALL}")
        
        # ตรวจสอบว่าการคัดลอกไป NAS เปิดใช้งานอยู่หรือไม่
        if ENABLE_NAS_COPY and NAS_PATH:
            if BACKUP_MODE == 'daily':
                # กำหนดโฟลเดอร์ใน NAS ตามวันที่ เช่น Z:\Developer\test\2024_11_13
                nas_backup_dir = os.path.join(NAS_PATH, now.strftime('%Y_%m_%d'))
                try:
                    if not os.path.exists(nas_backup_dir):
                        os.makedirs(nas_backup_dir)  # สร้างโฟลเดอร์ใน NAS ตามวันที่ หากยังไม่มี
                    shutil.copy(backup_path, os.path.join(nas_backup_dir, os.path.basename(backup_path)))
                    print(f"{Fore.GREEN}{logtime()} >> Daily backup file copied to NAS at: {os.path.join(nas_backup_dir, os.path.basename(backup_path))}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}{logtime()} >> Error occurred while copying daily file to NAS: {e}{Style.RESET_ALL}")
            else:
                # คัดลอกไฟล์ backup ไปยัง NAS ในโหมด single
                nas_backup_path = os.path.join(NAS_PATH, os.path.basename(backup_path))
                try:
                    shutil.copy(backup_path, nas_backup_path)
                    print(f"{Fore.GREEN}{logtime()} >> Backup copied to NAS at: {nas_backup_path}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}{logtime()} >> Error occurred while copying to NAS: {e}{Style.RESET_ALL}")



    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}{logtime()} >> Error occurred during backup: {e}{Style.RESET_ALL}")

    # ลบไฟล์สำรองที่เก่ากว่า 3 วัน
    cutoff_time = now - timedelta(days=3)
    for filename in os.listdir(BACKUP_DIR):
        if filename.endswith(".backup"):
            file_path = os.path.join(BACKUP_DIR, filename)
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_time < cutoff_time:
                os.remove(file_path)
                print(f"{Fore.YELLOW}{logtime()} >> Old backup file deleted: {file_path}{Style.RESET_ALL}")

    # ยกเลิกตัวแปรรหัสผ่าน
    del os.environ["PGPASSWORD"]

print(f"{Fore.MAGENTA}=========================== LOADING CONFIG ========================={Style.RESET_ALL}")
print(f"{Fore.MAGENTA}PATH BACKUP : {BACKUP_DIR}{Style.RESET_ALL}")
print(f"{Fore.MAGENTA}PATH NAS : {NAS_PATH if ENABLE_NAS_COPY else 'NAS Copy Disabled'}{Style.RESET_ALL}")
print(f"{Fore.MAGENTA}HOST : {DB_HOST}   PORT : {DB_PORT}{Style.RESET_ALL}")
print(f"{Fore.MAGENTA}USER : {DB_USER}{Style.RESET_ALL}")
print(f"{Fore.MAGENTA}PASS : {'*' * len(DB_PASSWORD)} (hidden){Style.RESET_ALL}")
print(f"{Fore.MAGENTA}DB NAME : {DB_NAME}{Style.RESET_ALL}")
print(f"{Fore.MAGENTA}Backup Interval : {BACKUP_INTERVAL} minutes{Style.RESET_ALL}")
print(f"{Fore.MAGENTA}NAS Copy Enabled : {ENABLE_NAS_COPY}{Style.RESET_ALL}")
print(f"{Fore.MAGENTA}Backup Mode : {BACKUP_MODE} ('daily' for daily folders, 'single' for single folder){Style.RESET_ALL}")
print(f"{Fore.MAGENTA}Backup Name Format : {BACKUP_NAME_FORMAT} ('detailed' for timestamped backups, 'daily' for daily overwrite){Style.RESET_ALL}")
print(f"{Fore.MAGENTA}============================= END CONFIG ==========================={Style.RESET_ALL}")

# Loop สำรองข้อมูลทุกๆ backup_interval นาที
while True:
    backup_database()
    print(f"{Fore.CYAN}{logtime()} >> Waiting {BACKUP_INTERVAL} minutes for the next backup...{Style.RESET_ALL}")
    time.sleep(BACKUP_INTERVAL * 60)
